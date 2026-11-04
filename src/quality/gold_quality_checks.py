from datetime import datetime, timezone
from pathlib import Path
import json

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOLD_DIR = PROJECT_ROOT / "data" / "gold" / "olist"

REQUIRED_COLUMNS = {
    "fact_orders": [
        "order_id",
        "customer_id",
        "order_purchase_timestamp",
        "order_purchase_date_key",
        "item_count",
        "gross_order_value",
        "payment_value",
    ],
    "fact_order_items": [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "price",
        "freight_value",
        "line_total",
    ],
    "dim_customers": [
        "customer_id",
        "customer_unique_id",
    ],
    "dim_products": [
        "product_id",
    ],
    "dim_sellers": [
        "seller_id",
    ],
    "dim_date": [
        "date_key",
        "date",
    ],
}

PRIMARY_KEYS = {
    "fact_orders": ["order_id"],
    "fact_order_items": ["order_id", "order_item_id"],
    "dim_customers": ["customer_id"],
    "dim_products": ["product_id"],
    "dim_sellers": ["seller_id"],
    "dim_date": ["date_key"],
}

NOT_NULL_COLUMNS = {
    "fact_orders": [
        "order_id",
        "customer_id",
        "order_purchase_timestamp",
        "order_purchase_date_key",
    ],
    "fact_order_items": [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "price",
        "freight_value",
        "line_total",
    ],
    "dim_customers": [
        "customer_id",
        "customer_unique_id",
    ],
    "dim_products": [
        "product_id",
    ],
    "dim_sellers": [
        "seller_id",
    ],
    "dim_date": [
        "date_key",
        "date",
    ],
}


def add_check(
    results: list,
    name: str,
    table: str,
    passed: bool,
    details: dict,
) -> None:
    """Add an individual quality-check result."""

    results.append(
        {
            "check": name,
            "table": table,
            "status": "PASS" if passed else "FAIL",
            "details": details,
        }
    )


def check_required_columns(
    tables: dict,
    results: list,
) -> None:
    """Check that required columns exist."""

    for table_name, required in REQUIRED_COLUMNS.items():
        dataframe = tables[table_name]

        missing = [
            column
            for column in required
            if column not in dataframe.columns
        ]

        add_check(
            results,
            "required_columns",
            table_name,
            not missing,
            {
                "missing_columns": missing,
                "required_column_count": len(required),
            },
        )


def check_primary_keys(
    tables: dict,
    results: list,
) -> None:
    """Check primary-key completeness and uniqueness."""

    for table_name, columns in PRIMARY_KEYS.items():
        dataframe = tables[table_name]

        if not all(
            column in dataframe.columns
            for column in columns
        ):
            continue

        null_rows = int(
            dataframe[columns].isna().any(axis=1).sum()
        )

        duplicate_rows = int(
            dataframe.duplicated(
                subset=columns,
                keep=False,
            ).sum()
        )

        passed = (
            null_rows == 0
            and duplicate_rows == 0
        )

        add_check(
            results,
            "primary_key_integrity",
            table_name,
            passed,
            {
                "key_columns": columns,
                "null_key_rows": null_rows,
                "duplicate_key_rows": duplicate_rows,
                "row_count": len(dataframe),
            },
        )


def check_not_null_columns(
    tables: dict,
    results: list,
) -> None:
    """Check mandatory fields for missing values."""

    for table_name, columns in NOT_NULL_COLUMNS.items():
        dataframe = tables[table_name]

        for column in columns:
            if column not in dataframe.columns:
                continue

            null_count = int(
                dataframe[column].isna().sum()
            )

            add_check(
                results,
                "not_null",
                table_name,
                null_count == 0,
                {
                    "column": column,
                    "null_count": null_count,
                    "row_count": len(dataframe),
                },
            )


def check_relationship(
    tables: dict,
    results: list,
    child_table: str,
    child_column: str,
    parent_table: str,
    parent_column: str,
) -> None:
    """Check referential integrity between two tables."""

    child = tables[child_table]
    parent = tables[parent_table]

    if (
        child_column not in child.columns
        or parent_column not in parent.columns
    ):
        return

    child_values = child[child_column].dropna()
    parent_values = set(
        parent[parent_column].dropna()
    )

    unmatched = int(
        (~child_values.isin(parent_values)).sum()
    )

    add_check(
        results,
        "referential_integrity",
        child_table,
        unmatched == 0,
        {
            "relationship": (
                f"{child_table}.{child_column} -> "
                f"{parent_table}.{parent_column}"
            ),
            "unmatched_rows": unmatched,
            "checked_rows": len(child_values),
        },
    )


def check_business_rules(
    tables: dict,
    results: list,
) -> None:
    """Check important analytical business rules."""

    items = tables["fact_order_items"]
    orders = tables["fact_orders"]

    # Monetary values must not be negative.

    for column in [
        "price",
        "freight_value",
        "line_total",
    ]:
        if column not in items.columns:
            continue

        invalid = int(
            (items[column] < 0).sum()
        )

        add_check(
            results,
            "non_negative_values",
            "fact_order_items",
            invalid == 0,
            {
                "column": column,
                "invalid_rows": invalid,
            },
        )

    # Line total must equal price plus freight.

    if {
        "price",
        "freight_value",
        "line_total",
    }.issubset(items.columns):

        expected = (
            items["price"]
            + items["freight_value"]
        )

        mismatches = int(
            (
                ~(
                    items["line_total"]
                    .sub(expected)
                    .abs()
                    .le(0.000001)
                )
            ).sum()
        )

        add_check(
            results,
            "line_total_calculation",
            "fact_order_items",
            mismatches == 0,
            {
                "mismatched_rows": mismatches,
            },
        )

    # Order metrics must not be negative.

    for column in [
        "item_count",
        "product_count",
        "seller_count",
        "payment_transaction_count",
        "payment_method_count",
        "review_count",
    ]:
        if column not in orders.columns:
            continue

        invalid = int(
            (orders[column] < 0).sum()
        )

        add_check(
            results,
            "non_negative_counts",
            "fact_orders",
            invalid == 0,
            {
                "column": column,
                "invalid_rows": invalid,
            },
        )

    # Order-level monetary values must not be negative.

    for column in [
        "item_value",
        "freight_value",
        "gross_order_value",
        "payment_value",
    ]:
        if column not in orders.columns:
            continue

        invalid = int(
            (orders[column] < 0).sum()
        )

        add_check(
            results,
            "non_negative_values",
            "fact_orders",
            invalid == 0,
            {
                "column": column,
                "invalid_rows": invalid,
            },
        )

    # Purchase date key must match purchase timestamp.

    if {
        "order_purchase_timestamp",
        "order_purchase_date_key",
    }.issubset(orders.columns):

        timestamp = orders["order_purchase_timestamp"]

        expected_key = (
            timestamp.dt.year * 10000
            + timestamp.dt.month * 100
            + timestamp.dt.day
        )

        mismatches = int(
            (
                orders["order_purchase_date_key"]
                != expected_key
            ).sum()
        )

        add_check(
            results,
            "purchase_date_key_consistency",
            "fact_orders",
            mismatches == 0,
            {
                "mismatched_rows": mismatches,
            },
        )


def validate_gold_tables(
    tables: dict,
) -> dict:
    """Run all Gold-layer data-quality checks."""

    expected_tables = set(REQUIRED_COLUMNS)
    supplied_tables = set(tables)

    missing_tables = sorted(
        expected_tables - supplied_tables
    )

    if missing_tables:
        raise ValueError(
            f"Missing Gold tables: {missing_tables}"
        )

    results = []

    check_required_columns(
        tables,
        results,
    )

    check_primary_keys(
        tables,
        results,
    )

    check_not_null_columns(
        tables,
        results,
    )

    relationships = [
        (
            "fact_orders",
            "customer_id",
            "dim_customers",
            "customer_id",
        ),
        (
            "fact_orders",
            "order_purchase_date_key",
            "dim_date",
            "date_key",
        ),
        (
            "fact_order_items",
            "order_id",
            "fact_orders",
            "order_id",
        ),
        (
            "fact_order_items",
            "product_id",
            "dim_products",
            "product_id",
        ),
        (
            "fact_order_items",
            "seller_id",
            "dim_sellers",
            "seller_id",
        ),
    ]

    for relationship in relationships:
        check_relationship(
            tables,
            results,
            *relationship,
        )

    check_business_rules(
        tables,
        results,
    )

    passed = sum(
        result["status"] == "PASS"
        for result in results
    )

    failed = sum(
        result["status"] == "FAIL"
        for result in results
    )

    return {
        "pipeline": "olist_gold_quality_checks",
        "run_timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "summary": {
            "total_checks": len(results),
            "passed": passed,
            "failed": failed,
            "overall_status": (
                "PASS" if failed == 0 else "FAIL"
            ),
        },
        "checks": results,
    }


def run_quality_checks(
    gold_dir: Path = GOLD_DIR,
) -> dict:
    """Load Gold Parquet tables and generate a quality report."""

    tables = {}

    for table_name in REQUIRED_COLUMNS:
        path = gold_dir / f"{table_name}.parquet"

        if not path.exists():
            raise FileNotFoundError(
                f"Gold table not found: {path}"
            )

        tables[table_name] = pd.read_parquet(path)

    report = validate_gold_tables(tables)

    report_path = (
        gold_dir / "_gold_quality_report.json"
    )

    with report_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
        )

    print("=" * 60)
    print("GOLD DATA QUALITY REPORT")
    print("=" * 60)

    print(
        f"Total checks: {report['summary']['total_checks']}"
    )

    print(
        f"Passed: {report['summary']['passed']}"
    )

    print(
        f"Failed: {report['summary']['failed']}"
    )

    print(
        f"Overall status: "
        f"{report['summary']['overall_status']}"
    )

    print(f"Report: {report_path}")

    for result in report["checks"]:
        print(
            f"{result['status']}: "
            f"{result['table']} - "
            f"{result['check']} - "
            f"{result['details']}"
        )

    return report


if __name__ == "__main__":
    report = run_quality_checks()

    if report["summary"]["failed"] > 0:
        raise SystemExit(1)