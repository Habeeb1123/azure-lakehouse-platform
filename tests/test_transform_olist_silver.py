from pathlib import Path

import pandas as pd

from src.transform_olist_silver import (
    clean_string_columns,
    convert_timestamps,
    rename_columns,
    transform_dataset,
)


def test_clean_string_columns_trims_whitespace():
    df = pd.DataFrame(
        {
            "customer_city": [
                " London ",
                "Manchester  ",
                "  Leeds",
            ]
        }
    )

    result = clean_string_columns(df)

    assert result["customer_city"].tolist() == [
        "London",
        "Manchester",
        "Leeds",
    ]


def test_rename_columns_corrects_product_schema():
    df = pd.DataFrame(
        {
            "product_name_lenght": [10],
            "product_description_lenght": [100],
        }
    )

    result = rename_columns(
        df=df,
        dataset_name="olist_products_dataset",
    )

    assert "product_name_length" in result.columns
    assert "product_description_length" in result.columns
    assert "product_name_lenght" not in result.columns
    assert "product_description_lenght" not in result.columns


def test_convert_timestamps_creates_datetime_columns():
    df = pd.DataFrame(
        {
            "order_purchase_timestamp": [
                "2018-01-01 10:30:00",
                "2018-01-02 15:45:00",
            ]
        }
    )

    result = convert_timestamps(
        df=df,
        dataset_name="olist_orders_dataset",
    )

    assert pd.api.types.is_datetime64_any_dtype(
        result["order_purchase_timestamp"]
    )


def test_convert_timestamps_coerces_invalid_values():
    df = pd.DataFrame(
        {
            "order_purchase_timestamp": [
                "2018-01-01 10:30:00",
                "not-a-valid-date",
            ]
        }
    )

    result = convert_timestamps(
        df=df,
        dataset_name="olist_orders_dataset",
    )

    assert pd.isna(
        result.loc[1, "order_purchase_timestamp"]
    )


def test_transform_dataset_removes_duplicates(tmp_path: Path):
    source_path = (
        tmp_path / "olist_geolocation_dataset.parquet"
    )
    destination_path = (
        tmp_path / "silver_geolocation.parquet"
    )

    df = pd.DataFrame(
        {
            "geolocation_zip_code_prefix": [
                1000,
                1000,
                2000,
            ],
            "geolocation_lat": [
                -23.5,
                -23.5,
                -22.9,
            ],
            "geolocation_lng": [
                -46.6,
                -46.6,
                -43.2,
            ],
            "geolocation_city": [
                " Sao Paulo ",
                " Sao Paulo ",
                "Rio de Janeiro",
            ],
            "geolocation_state": [
                "SP",
                "SP",
                "RJ",
            ],
        }
    )

    df.to_parquet(source_path, index=False)

    result = transform_dataset(
        source_path=source_path,
        destination_path=destination_path,
    )

    transformed_df = pd.read_parquet(
        destination_path
    )

    assert destination_path.exists()
    assert result["rows_before"] == 3
    assert result["rows_after"] == 2
    assert result["duplicates_removed"] == 1
    assert len(transformed_df) == 2


def test_transform_dataset_writes_parquet(tmp_path: Path):
    source_path = (
        tmp_path / "olist_customers_dataset.parquet"
    )
    destination_path = (
        tmp_path / "silver_customers.parquet"
    )

    df = pd.DataFrame(
        {
            "customer_id": ["A", "B"],
            "customer_city": [
                " London ",
                " Leeds ",
            ],
        }
    )

    df.to_parquet(source_path, index=False)

    result = transform_dataset(
        source_path=source_path,
        destination_path=destination_path,
    )

    output_df = pd.read_parquet(destination_path)

    assert destination_path.exists()
    assert result["rows_before"] == 2
    assert result["rows_after"] == 2
    assert output_df["customer_city"].tolist() == [
        "London",
        "Leeds",
    ]