from pathlib import Path
from datetime import datetime, timezone
import json

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

BRONZE_DIR = PROJECT_ROOT / "data" / "bronze" / "olist"
SILVER_DIR = PROJECT_ROOT / "data" / "silver" / "olist"


TIMESTAMP_COLUMNS = {
    "olist_orders_dataset": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "olist_order_items_dataset": [
        "shipping_limit_date",
    ],
    "olist_order_reviews_dataset": [
        "review_creation_date",
        "review_answer_timestamp",
    ],
}


COLUMN_RENAMES = {
    "olist_products_dataset": {
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length",
    }
}


def clean_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Trim whitespace from string columns."""

    df = df.copy()

    for column in df.select_dtypes(include=["object", "string"]).columns:
        df[column] = df[column].astype("string").str.strip()

    return df


def convert_timestamps(
    df: pd.DataFrame,
    dataset_name: str,
) -> pd.DataFrame:
    """Convert configured timestamp columns to datetime."""

    df = df.copy()

    for column in TIMESTAMP_COLUMNS.get(dataset_name, []):
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
            )

    return df


def rename_columns(
    df: pd.DataFrame,
    dataset_name: str,
) -> pd.DataFrame:
    """Apply known schema corrections."""

    rename_map = COLUMN_RENAMES.get(dataset_name, {})

    return df.rename(columns=rename_map)


def transform_dataset(
    source_path: Path,
    destination_path: Path,
) -> dict:
    """Transform one Bronze dataset into Silver format."""

    dataset_name = source_path.stem

    print(f"Transforming {source_path.name}...")

    df = pd.read_parquet(source_path)

    rows_before = len(df)

    df = rename_columns(
        df=df,
        dataset_name=dataset_name,
    )

    df = clean_string_columns(df)

    df = convert_timestamps(
        df=df,
        dataset_name=dataset_name,
    )

    duplicate_rows = int(df.duplicated().sum())

    if duplicate_rows:
        df = df.drop_duplicates().reset_index(drop=True)

    rows_after = len(df)

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
        f"-> {destination_path.name} | "
        f"{rows_before:,} -> {rows_after:,} rows | "
        f"{duplicate_rows:,} duplicates removed"
    )

    return {
        "dataset": dataset_name,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "duplicates_removed": duplicate_rows,
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "null_counts": {
            column: int(count)
            for column, count in df.isna().sum().items()
            if count > 0
        },
    }


def main() -> None:
    """Execute Bronze-to-Silver transformations."""

    print("=" * 70)
    print("OLIST SILVER TRANSFORMATION PIPELINE")
    print("=" * 70)

    SILVER_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    bronze_files = sorted(
        BRONZE_DIR.glob("*.parquet")
    )

    if not bronze_files:
        raise FileNotFoundError(
            f"No Bronze Parquet files found in {BRONZE_DIR}"
        )

    results = []

    for source_path in bronze_files:
        destination_path = (
            SILVER_DIR / source_path.name
        )

        result = transform_dataset(
            source_path=source_path,
            destination_path=destination_path,
        )

        results.append(result)

    manifest = {
        "pipeline": "olist_silver_transformation",
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_count": len(results),
        "datasets": results,
    }

    manifest_path = (
        SILVER_DIR / "_transformation_manifest.json"
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
    print(f"Datasets processed: {len(results)}")
    print(f"Manifest: {manifest_path}")
    print("SILVER TRANSFORMATION COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()