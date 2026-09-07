from pathlib import Path
from datetime import datetime, timezone
import json

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "olist"
BRONZE_DIR = PROJECT_ROOT / "data" / "bronze" / "olist"

EXPECTED_DATASETS = {
    "olist_customers_dataset.csv": [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ],
    "olist_geolocation_dataset.csv": [
        "geolocation_zip_code_prefix",
        "geolocation_lat",
        "geolocation_lng",
        "geolocation_city",
        "geolocation_state",
    ],
    "olist_orders_dataset.csv": [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
    ],
    "olist_order_items_dataset.csv": [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "price",
        "freight_value",
    ],
    "olist_order_payments_dataset.csv": [
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
    ],
    "olist_order_reviews_dataset.csv": [
        "review_id",
        "order_id",
        "review_score",
    ],
    "olist_products_dataset.csv": [
        "product_id",
        "product_category_name",
    ],
    "olist_sellers_dataset.csv": [
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state",
    ],
    "product_category_name_translation.csv": [
        "product_category_name",
        "product_category_name_english",
    ],
}


def validate_dataframe(
    df: pd.DataFrame,
    filename: str,
    required_columns: list[str],
) -> None:
    """Validate the basic structure of an incoming dataset."""

    if df.empty:
        raise ValueError(f"{filename} contains no rows.")

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{filename} is missing required columns: {missing_columns}"
        )


def ingest_dataset(
    source_path: Path,
    destination_path: Path,
    required_columns: list[str],
) -> dict:
    """Read, validate and convert one CSV dataset to Parquet."""

    print(f"Reading {source_path.name}...")

    df = pd.read_csv(source_path)

    validate_dataframe(
        df=df,
        filename=source_path.name,
        required_columns=required_columns,
    )

    destination_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_parquet(
        destination_path,
        index=False,
        engine="pyarrow",
    )

    print(
        f"SUCCESS: {source_path.name} "
        f"-> {destination_path.name} "
        f"({len(df):,} rows)"
    )

    return {
        "source_file": source_path.name,
        "bronze_file": destination_path.name,
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
    }


def main() -> None:
    """Execute the Olist Bronze ingestion pipeline."""

    print("=" * 70)
    print("OLIST BRONZE INGESTION PIPELINE")
    print("=" * 70)

    BRONZE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = []

    for filename, required_columns in EXPECTED_DATASETS.items():
        source_path = RAW_DIR / filename

        if not source_path.exists():
            raise FileNotFoundError(
                f"Required source file not found: {source_path}"
            )

        destination_path = (
            BRONZE_DIR / f"{source_path.stem}.parquet"
        )

        result = ingest_dataset(
            source_path=source_path,
            destination_path=destination_path,
            required_columns=required_columns,
        )

        results.append(result)

    manifest = {
        "pipeline": "olist_bronze_ingestion",
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_count": len(results),
        "datasets": results,
    }

    manifest_path = BRONZE_DIR / "_ingestion_manifest.json"

    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)

    print("=" * 70)
    print(f"Datasets processed: {len(results)}")
    print(f"Manifest: {manifest_path}")
    print("BRONZE INGESTION COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()