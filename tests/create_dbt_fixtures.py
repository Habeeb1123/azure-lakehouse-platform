"""Create small synthetic Gold Parquet datasets for dbt CI validation."""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLD_DIR = PROJECT_ROOT / "data" / "gold" / "olist"

def create_fixtures() -> None:
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    # Customer dimension
    customers = pd.DataFrame(
        {
            "customer_id": pd.Series(["C1", "C2"], dtype="string"),
            "customer_unique_id": pd.Series(["U1", "U2"], dtype="string"),
            "customer_zip_code_prefix": pd.Series([1000, 2000], dtype="int64"),
            "customer_city": pd.Series(["City A", "City B"], dtype="string"),
            "customer_state": pd.Series(["SP", "RJ"], dtype="string"),
        }
    )

    # Calendar dimension
    dates = pd.date_range("2018-01-01", "2018-01-03", freq="D")
    dim_date = pd.DataFrame({"date": dates})

    dim_date["date_key"] = (
        dim_date["date"].dt.year * 10000
        + dim_date["date"].dt.month * 100
        + dim_date["date"].dt.day
    ).astype("int32")

    dim_date["year"] = dim_date["date"].dt.year.astype("int32")
    dim_date["quarter"] = dim_date["date"].dt.quarter.astype("int32")
    dim_date["month"] = dim_date["date"].dt.month.astype("int32")
    dim_date["month_name"] = dim_date["date"].dt.month_name()
    dim_date["day"] = dim_date["date"].dt.day.astype("int32")
    dim_date["day_of_week"] = dim_date["date"].dt.dayofweek.astype("int32")
    dim_date["day_name"] = dim_date["date"].dt.day_name()
    dim_date["is_weekend"] = dim_date["day_of_week"] >= 5

    dim_date = dim_date[
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

    # Product dimension
    products = pd.DataFrame(
        {
            "product_id": pd.Series(["P1", "P2"], dtype="string"),
            "product_category_name": pd.Series(
                ["beleza_saude", "esporte_lazer"], dtype="string"
            ),
            "product_name_length": [10.0, 12.0],
            "product_description_length": [100.0, 120.0],
            "product_photos_qty": [2.0, 3.0],
            "product_weight_g": [500.0, 750.0],
            "product_length_cm": [20.0, 25.0],
            "product_height_cm": [10.0, 12.0],
            "product_width_cm": [15.0, 18.0],
            "product_category_name_en": pd.Series(
                ["health_beauty", "sports_leisure"], dtype="string"
            ),
        }
    )

    # Seller dimension
    sellers = pd.DataFrame(
        {
            "seller_id": pd.Series(["S1", "S2"], dtype="string"),
            "seller_zip_code_prefix": pd.Series([3000, 4000], dtype="int64"),
            "seller_city": pd.Series(["City A", "City B"], dtype="string"),
            "seller_state": pd.Series(["SP", "RJ"], dtype="string"),
        }
    )

    # Order fact
    purchase_times = pd.to_datetime(
        ["2018-01-01 10:00:00", "2018-01-02 11:00:00"]
    )
    approved_times = pd.to_datetime(
        ["2018-01-01 12:00:00", "2018-01-02 12:00:00"]
    )
    delivered_times = pd.to_datetime(
        ["2018-01-04 10:00:00", "2018-01-05 11:00:00"]
    )
    estimated_times = pd.to_datetime(
        ["2018-01-05 10:00:00", "2018-01-06 11:00:00"]
    )

    orders = pd.DataFrame(
        {
            "order_id": pd.Series(["O1", "O2"], dtype="string"),
            "customer_id": pd.Series(["C1", "C2"], dtype="string"),
            "order_status": pd.Series(["delivered", "delivered"], dtype="string"),
            "order_purchase_timestamp": purchase_times,
            "order_approved_at": approved_times,
            "order_delivered_carrier_date": pd.to_datetime(
                ["2018-01-02 10:00:00", "2018-01-03 11:00:00"]
            ),
            "order_delivered_customer_date": delivered_times,
            "order_estimated_delivery_date": estimated_times,
            "customer_unique_id": pd.Series(["U1", "U2"], dtype="string"),
            "item_count": pd.Series([2, 1], dtype="int64"),
            "product_count": pd.Series([2, 1], dtype="int64"),
            "seller_count": pd.Series([2, 1], dtype="int64"),
            "item_value": [30.0, 50.0],
            "freight_value": [5.0, 7.0],
            "gross_order_value": [35.0, 57.0],
            "payment_transaction_count": pd.Series([1, 1], dtype="int64"),
            "payment_method_count": pd.Series([1, 1], dtype="int64"),
            "payment_value": [35.0, 57.0],
            "max_installments": [1.0, 2.0],
            "review_count": pd.Series([1, 1], dtype="int64"),
            "average_review_score": [5.0, 4.0],
            "order_purchase_date_key": pd.Series(
                [20180101, 20180102], dtype="Int64"
            ),
            "approval_time_hours": [2.0, 1.0],
            "delivery_time_days": [3.0, 3.0],
            "delivery_variance_days": [-1.0, -1.0],
            "payment_difference": [0.0, 0.0],
            "delivered_on_time": pd.Series([True, True], dtype="boolean"),
        }
    )

    # Order-item fact
    order_items = pd.DataFrame(
        {
            "order_id": pd.Series(["O1", "O1", "O2"], dtype="string"),
            "order_item_id": pd.Series([1, 2, 1], dtype="int64"),
            "product_id": pd.Series(["P1", "P2", "P1"], dtype="string"),
            "seller_id": pd.Series(["S1", "S2", "S1"], dtype="string"),
            "shipping_limit_date": pd.to_datetime(
                ["2018-01-03", "2018-01-03", "2018-01-04"]
            ),
            "price": [10.0, 20.0, 50.0],
            "freight_value": [2.0, 3.0, 7.0],
            "line_total": [12.0, 23.0, 57.0],
        }
    )

    tables = {
        "dim_customers": customers,
        "dim_date": dim_date,
        "dim_products": products,
        "dim_sellers": sellers,
        "fact_orders": orders,
        "fact_order_items": order_items,
    }

    existing = [name for name in tables if (GOLD_DIR / f"{name}.parquet").exists()]
    if existing:
        raise SystemExit("Refusing to overwrite existing Gold files: " + ", ".join(existing))

    for name, dataframe in tables.items():
        destination = GOLD_DIR / f"{name}.parquet"
        dataframe.to_parquet(destination, index=False, engine="pyarrow")
        print(
            f"Created {destination.relative_to(PROJECT_ROOT)}: "
            f"{len(dataframe)} rows"
        )

    print("Synthetic dbt CI fixtures created successfully.")


if __name__ == "__main__":
    create_fixtures()
