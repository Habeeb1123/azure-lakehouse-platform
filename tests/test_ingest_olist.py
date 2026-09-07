from pathlib import Path

import pandas as pd
import pytest

from src.ingest_olist import ingest_dataset, validate_dataframe


def test_validate_dataframe_accepts_valid_data():
    df = pd.DataFrame(
        {
            "order_id": ["1", "2"],
            "customer_id": ["A", "B"],
        }
    )

    validate_dataframe(
        df=df,
        filename="test.csv",
        required_columns=["order_id", "customer_id"],
    )


def test_validate_dataframe_rejects_empty_dataframe():
    df = pd.DataFrame(columns=["order_id", "customer_id"])

    with pytest.raises(ValueError, match="contains no rows"):
        validate_dataframe(
            df=df,
            filename="test.csv",
            required_columns=["order_id", "customer_id"],
        )


def test_validate_dataframe_rejects_missing_columns():
    df = pd.DataFrame(
        {
            "order_id": ["1"],
        }
    )

    with pytest.raises(ValueError, match="missing required columns"):
        validate_dataframe(
            df=df,
            filename="test.csv",
            required_columns=["order_id", "customer_id"],
        )


def test_ingest_dataset_creates_parquet(tmp_path: Path):
    source_path = tmp_path / "orders.csv"
    destination_path = tmp_path / "orders.parquet"

    df = pd.DataFrame(
        {
            "order_id": ["1", "2"],
            "customer_id": ["A", "B"],
        }
    )

    df.to_csv(source_path, index=False)

    result = ingest_dataset(
        source_path=source_path,
        destination_path=destination_path,
        required_columns=["order_id", "customer_id"],
    )

    assert destination_path.exists()
    assert result["row_count"] == 2
    assert result["column_count"] == 2


def test_ingest_dataset_preserves_row_count(tmp_path: Path):
    source_path = tmp_path / "customers.csv"
    destination_path = tmp_path / "customers.parquet"

    df = pd.DataFrame(
        {
            "customer_id": ["A", "B", "C"],
            "customer_city": ["London", "Leeds", "Manchester"],
        }
    )

    df.to_csv(source_path, index=False)

    ingest_dataset(
        source_path=source_path,
        destination_path=destination_path,
        required_columns=["customer_id", "customer_city"],
    )

    parquet_df = pd.read_parquet(destination_path)

    assert len(parquet_df) == len(df)