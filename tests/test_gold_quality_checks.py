import pandas as pd

from src.quality.gold_quality_checks import validate_gold_tables


def create_valid_gold_tables():
    """Create small valid Gold tables for testing."""

    fact_orders = pd.DataFrame({
        "order_id": ["O1"],
        "customer_id": ["C1"],
        "order_status": ["delivered"],
        "order_purchase_timestamp": pd.to_datetime(
            ["2018-01-01 10:00:00"]
        ),
        "order_purchase_date_key": [20180101],
        "item_count": [1],
        "gross_order_value": [110.0],
        "payment_value": [110.0],
    })

    fact_order_items = pd.DataFrame({
        "order_id": ["O1"],
        "order_item_id": [1],
        "product_id": ["P1"],
        "seller_id": ["S1"],
        "price": [100.0],
        "freight_value": [10.0],
        "line_total": [110.0],
    })

    dim_customers = pd.DataFrame({
        "customer_id": ["C1"],
        "customer_unique_id": ["U1"],
    })

    dim_products = pd.DataFrame({
        "product_id": ["P1"],
    })

    dim_sellers = pd.DataFrame({
        "seller_id": ["S1"],
    })

    dim_date = pd.DataFrame({
        "date_key": [20180101],
        "date": pd.to_datetime(["2018-01-01"]),
    })

    return {
        "fact_orders": fact_orders,
        "fact_order_items": fact_order_items,
        "dim_customers": dim_customers,
        "dim_products": dim_products,
        "dim_sellers": dim_sellers,
        "dim_date": dim_date,
    }


def test_valid_gold_tables_pass_all_quality_checks():
    tables = create_valid_gold_tables()

    report = validate_gold_tables(tables)
    summary = report["summary"]

    assert summary["failed"] == 0
    assert summary["passed"] == summary["total_checks"]


def test_quality_checks_detect_duplicate_primary_keys():
    tables = create_valid_gold_tables()

    tables["dim_customers"] = pd.concat(
        [tables["dim_customers"], tables["dim_customers"]],
        ignore_index=True,
    )

    report = validate_gold_tables(tables)

    failed_checks = [
        check for check in report["checks"]
        if check["status"] == "FAIL"
    ]

    assert any(
        check["check"] == "primary_key_integrity"
        and check["table"] == "dim_customers"
        for check in failed_checks
    )


def test_quality_checks_detect_null_mandatory_values():
    tables = create_valid_gold_tables()
    tables["fact_orders"].loc[0, "customer_id"] = None

    report = validate_gold_tables(tables)

    failed_checks = [
        check for check in report["checks"]
        if check["status"] == "FAIL"
    ]

    assert any(
        check["check"] == "not_null"
        and check["table"] == "fact_orders"
        and check["details"]["column"] == "customer_id"
        for check in failed_checks
    )


def test_quality_checks_detect_broken_foreign_key_relationships():
    tables = create_valid_gold_tables()
    tables["fact_order_items"].loc[0, "product_id"] = "UNKNOWN"

    report = validate_gold_tables(tables)

    failed_checks = [
        check for check in report["checks"]
        if check["status"] == "FAIL"
    ]

    assert any(
        check["check"] == "referential_integrity"
        and check["table"] == "fact_order_items"
        for check in failed_checks
    )


def test_quality_checks_detect_incorrect_line_totals():
    tables = create_valid_gold_tables()
    tables["fact_order_items"].loc[0, "line_total"] = 999.0

    report = validate_gold_tables(tables)

    failed_checks = [
        check for check in report["checks"]
        if check["status"] == "FAIL"
    ]

    assert any(
        check["check"] == "line_total_calculation"
        and check["table"] == "fact_order_items"
        for check in failed_checks
    )