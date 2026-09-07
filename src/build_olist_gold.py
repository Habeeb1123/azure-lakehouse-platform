from pathlib import Path
from datetime import datetime, timezone
import json

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SILVER_DIR = PROJECT_ROOT / "data" / "silver" / "olist"
GOLD_DIR = PROJECT_ROOT / "data" / "gold" / "olist"


def load_dataset(filename: str) -> pd.DataFrame:
    """Load one Silver Parquet dataset."""

    path = SILVER_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Required Silver dataset not found: {path}"
        )

    return pd.read_parquet(path)


def build_dim_customers(
    customers: pd.DataFrame,
) -> pd.DataFrame:
    """Build the customer dimension."""

    columns = [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ]

    result = (
        customers[columns]
        .drop_duplicates(subset=["customer_id"])
        .reset_index(drop=True)
    )

    return result


def build_dim_products(
    products: pd.DataFrame,
    translations: pd.DataFrame,
) -> pd.DataFrame:
    """Build the product dimension with English categories."""

    result = products.merge(
        translations,
        on="product_category_name",
        how="left",
        validate="many_to_one",
    )

    result = result.rename(
        columns={
            "product_category_name_english":
                "product_category_name_en"
        }
    )

    return result.reset_index(drop=True)


def build_dim_sellers(
    sellers: pd.DataFrame,
) -> pd.DataFrame:
    """Build the seller dimension."""

    return (
        sellers
        .drop_duplicates(subset=["seller_id"])
        .reset_index(drop=True)
    )


def build_dim_date(
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Build a reusable calendar dimension."""

    purchase_dates = (
        orders["order_purchase_timestamp"]
        .dropna()
        .dt.normalize()
    )

    start_date = purchase_dates.min()
    end_date = purchase_dates.max()

    dates = pd.date_range(
        start=start_date,
        end=end_date,
        freq="D",
    )

    dim_date = pd.DataFrame(
        {
            "date": dates,
        }
    )

    dim_date["date_key"] = (
        dim_date["date"].dt.year * 10000
        + dim_date["date"].dt.month * 100
        + dim_date["date"].dt.day
    )

    dim_date["year"] = dim_date["date"].dt.year
    dim_date["quarter"] = dim_date["date"].dt.quarter
    dim_date["month"] = dim_date["date"].dt.month

    dim_date["month_name"] = (
        dim_date["date"].dt.month_name()
    )

    dim_date["day"] = dim_date["date"].dt.day

    dim_date["day_of_week"] = (
        dim_date["date"].dt.dayofweek
    )

    dim_date["day_name"] = (
        dim_date["date"].dt.day_name()
    )

    dim_date["is_weekend"] = (
        dim_date["day_of_week"] >= 5
    )

    return dim_date[
        [
            "date_key",
            "date",
            "year",
            "quarter",
            "month",
            "month_name",
            "day",
            "day_of_week",
            "day_name",
            "is_weekend",
        ]
    ]


def build_fact_order_items(
    order_items: pd.DataFrame,
) -> pd.DataFrame:
    """Build the order-item fact table."""

    result = order_items.copy()

    result["line_total"] = (
        result["price"]
        + result["freight_value"]
    )

    return result.reset_index(drop=True)


def build_fact_orders(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    order_items: pd.DataFrame,
    payments: pd.DataFrame,
    reviews: pd.DataFrame,
) -> pd.DataFrame:
    """Build an order-grain analytical fact table."""

    item_metrics = (
        order_items
        .groupby(
            "order_id",
            as_index=False,
        )
        .agg(
            item_count=("order_item_id", "count"),
            product_count=("product_id", "nunique"),
            seller_count=("seller_id", "nunique"),
            item_value=("price", "sum"),
            freight_value=("freight_value", "sum"),
        )
    )

    item_metrics["gross_order_value"] = (
        item_metrics["item_value"]
        + item_metrics["freight_value"]
    )

    payment_metrics = (
        payments
        .groupby(
            "order_id",
            as_index=False,
        )
        .agg(
            payment_transaction_count=(
                "payment_sequential",
                "count",
            ),
            payment_method_count=(
                "payment_type",
                "nunique",
            ),
            payment_value=(
                "payment_value",
                "sum",
            ),
            max_installments=(
                "payment_installments",
                "max",
            ),
        )
    )

    review_metrics = (
        reviews
        .groupby(
            "order_id",
            as_index=False,
        )
        .agg(
            review_count=("review_id", "count"),
            average_review_score=(
                "review_score",
                "mean",
            ),
        )
    )

    customer_keys = customers[
        [
            "customer_id",
            "customer_unique_id",
        ]
    ].drop_duplicates(
        subset=["customer_id"]
    )

    fact = orders.merge(
        customer_keys,
        on="customer_id",
        how="left",
        validate="many_to_one",
    )

    fact = fact.merge(
        item_metrics,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    fact = fact.merge(
        payment_metrics,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    fact = fact.merge(
        review_metrics,
        on="order_id",
        how="left",
        validate="one_to_one",
    )

    count_columns = [
        "item_count",
        "product_count",
        "seller_count",
        "payment_transaction_count",
        "payment_method_count",
        "review_count",
    ]

    for column in count_columns:
        fact[column] = (
            fact[column]
            .fillna(0)
            .astype("int64")
        )

    monetary_columns = [
        "item_value",
        "freight_value",
        "gross_order_value",
        "payment_value",
    ]

    for column in monetary_columns:
        fact[column] = (
            fact[column]
            .fillna(0.0)
        )

    purchase_timestamp = (
        fact["order_purchase_timestamp"]
    )

    fact["order_purchase_date_key"] = (
        purchase_timestamp.dt.year * 10000
        + purchase_timestamp.dt.month * 100
        + purchase_timestamp.dt.day
    ).astype("Int64")

    fact["approval_time_hours"] = (
        (
            fact["order_approved_at"]
            - fact["order_purchase_timestamp"]
        ).dt.total_seconds()
        / 3600
    )

    fact["delivery_time_days"] = (
        (
            fact["order_delivered_customer_date"]
            - fact["order_purchase_timestamp"]
        ).dt.total_seconds()
        / 86400
    )

    fact["delivery_variance_days"] = (
        (
            fact["order_delivered_customer_date"]
            - fact["order_estimated_delivery_date"]
        ).dt.total_seconds()
        / 86400
    )

    fact["payment_difference"] = (
        fact["payment_value"]
        - fact["gross_order_value"]
    )

    delivered_on_time = pd.Series(
        pd.NA,
        index=fact.index,
        dtype="boolean",
    )

    valid_delivery = (
        fact["order_delivered_customer_date"].notna()
        & fact["order_estimated_delivery_date"].notna()
    )

    delivered_on_time.loc[valid_delivery] = (
        fact.loc[
            valid_delivery,
            "order_delivered_customer_date",
        ]
        <= fact.loc[
            valid_delivery,
            "order_estimated_delivery_date",
        ]
    )

    fact["delivered_on_time"] = delivered_on_time

    return fact.reset_index(drop=True)


def write_gold_table(
    name: str,
    df: pd.DataFrame,
) -> dict:
    """Write one Gold table to Parquet."""

    destination = GOLD_DIR / f"{name}.parquet"

    df.to_parquet(
        destination,
        index=False,
        engine="pyarrow",
    )

    print(
        f"SUCCESS: {name}.parquet "
        f"({len(df):,} rows, "
        f"{len(df.columns)} columns)"
    )

    return {
        "table": name,
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
    }


def main() -> None:
    """Build the Olist Gold analytical layer."""

    print("=" * 70)
    print("OLIST GOLD ANALYTICS PIPELINE")
    print("=" * 70)

    GOLD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    customers = load_dataset(
        "olist_customers_dataset.parquet"
    )

    orders = load_dataset(
        "olist_orders_dataset.parquet"
    )

    order_items = load_dataset(
        "olist_order_items_dataset.parquet"
    )

    payments = load_dataset(
        "olist_order_payments_dataset.parquet"
    )

    reviews = load_dataset(
        "olist_order_reviews_dataset.parquet"
    )

    products = load_dataset(
        "olist_products_dataset.parquet"
    )

    sellers = load_dataset(
        "olist_sellers_dataset.parquet"
    )

    translations = load_dataset(
        "product_category_name_translation.parquet"
    )

    dim_customers = build_dim_customers(
        customers
    )

    dim_products = build_dim_products(
        products,
        translations,
    )

    dim_sellers = build_dim_sellers(
        sellers
    )

    dim_date = build_dim_date(
        orders
    )

    fact_order_items = build_fact_order_items(
        order_items
    )

    fact_orders = build_fact_orders(
        orders=orders,
        customers=customers,
        order_items=order_items,
        payments=payments,
        reviews=reviews,
    )

    tables = {
        "fact_orders": fact_orders,
        "fact_order_items": fact_order_items,
        "dim_customers": dim_customers,
        "dim_products": dim_products,
        "dim_sellers": dim_sellers,
        "dim_date": dim_date,
    }

    manifest_tables = []

    for name, dataframe in tables.items():
        manifest_tables.append(
            write_gold_table(
                name=name,
                df=dataframe,
            )
        )

    manifest = {
        "pipeline": "olist_gold_analytics",
        "run_timestamp_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "table_count": len(tables),
        "tables": manifest_tables,
    }

    manifest_path = (
        GOLD_DIR / "_gold_manifest.json"
    )

    with manifest_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            manifest,
            file,
            indent=2,
        )

    print("=" * 70)
    print(f"Gold tables built: {len(tables)}")
    print(f"Manifest: {manifest_path}")
    print(
        "GOLD ANALYTICS PIPELINE "
        "COMPLETED SUCCESSFULLY"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()