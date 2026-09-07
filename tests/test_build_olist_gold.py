import pandas as pd

from src.build_olist_gold import (
    build_dim_customers,
    build_dim_products,
    build_dim_date,
    build_fact_order_items,
    build_fact_orders,
)


def test_build_dim_customers_removes_duplicate_customer_ids():
    customers = pd.DataFrame(
        {
            "customer_id": ["C1", "C1", "C2"],
            "customer_unique_id": ["U1", "U1", "U2"],
            "customer_zip_code_prefix": [1000, 1000, 2000],
            "customer_city": ["City A", "City A", "City B"],
            "customer_state": ["SP", "SP", "RJ"],
        }
    )

    result = build_dim_customers(customers)

    assert len(result) == 2
    assert result["customer_id"].is_unique


def test_build_dim_products_adds_english_category():
    products = pd.DataFrame(
        {
            "product_id": ["P1", "P2"],
            "product_category_name": [
                "beleza_saude",
                "esporte_lazer",
            ],
        }
    )

    translations = pd.DataFrame(
        {
            "product_category_name": [
                "beleza_saude",
                "esporte_lazer",
            ],
            "product_category_name_english": [
                "health_beauty",
                "sports_leisure",
            ],
        }
    )

    result = build_dim_products(
        products=products,
        translations=translations,
    )

    assert "product_category_name_en" in result.columns

    assert result.loc[
        result["product_id"] == "P1",
        "product_category_name_en",
    ].iloc[0] == "health_beauty"


def test_build_dim_date_creates_calendar_attributes():
    orders = pd.DataFrame(
        {
            "order_purchase_timestamp": pd.to_datetime(
                [
                    "2018-01-01 10:00:00",
                    "2018-01-03 12:00:00",
                ]
            )
        }
    )

    result = build_dim_date(orders)

    assert len(result) == 3

    assert result["date_key"].tolist() == [
        20180101,
        20180102,
        20180103,
    ]

    assert "month_name" in result.columns
    assert "day_name" in result.columns
    assert "is_weekend" in result.columns


def test_build_fact_order_items_calculates_line_total():
    order_items = pd.DataFrame(
        {
            "order_id": ["O1", "O2"],
            "order_item_id": [1, 1],
            "product_id": ["P1", "P2"],
            "seller_id": ["S1", "S2"],
            "shipping_limit_date": pd.to_datetime(
                [
                    "2018-01-03",
                    "2018-01-04",
                ]
            ),
            "price": [100.0, 50.0],
            "freight_value": [10.0, 5.0],
        }
    )

    result = build_fact_order_items(order_items)

    assert result["line_total"].tolist() == [
        110.0,
        55.0,
    ]


def test_build_fact_orders_aggregates_order_metrics():
    orders = pd.DataFrame(
        {
            "order_id": ["O1"],
            "customer_id": ["C1"],
            "order_status": ["delivered"],
            "order_purchase_timestamp": pd.to_datetime(
                ["2018-01-01 10:00:00"]
            ),
            "order_approved_at": pd.to_datetime(
                ["2018-01-01 12:00:00"]
            ),
            "order_delivered_carrier_date": pd.to_datetime(
                ["2018-01-02 10:00:00"]
            ),
            "order_delivered_customer_date": pd.to_datetime(
                ["2018-01-04 10:00:00"]
            ),
            "order_estimated_delivery_date": pd.to_datetime(
                ["2018-01-05 10:00:00"]
            ),
        }
    )

    customers = pd.DataFrame(
        {
            "customer_id": ["C1"],
            "customer_unique_id": ["U1"],
        }
    )

    order_items = pd.DataFrame(
        {
            "order_id": ["O1", "O1"],
            "order_item_id": [1, 2],
            "product_id": ["P1", "P2"],
            "seller_id": ["S1", "S1"],
            "price": [10.0, 20.0],
            "freight_value": [2.0, 3.0],
        }
    )

    payments = pd.DataFrame(
        {
            "order_id": ["O1", "O1"],
            "payment_sequential": [1, 2],
            "payment_type": [
                "credit_card",
                "voucher",
            ],
            "payment_installments": [2, 1],
            "payment_value": [30.0, 5.0],
        }
    )

    reviews = pd.DataFrame(
        {
            "review_id": ["R1"],
            "order_id": ["O1"],
            "review_score": [5],
        }
    )

    result = build_fact_orders(
        orders=orders,
        customers=customers,
        order_items=order_items,
        payments=payments,
        reviews=reviews,
    )

    row = result.iloc[0]

    assert len(result) == 1
    assert row["item_count"] == 2
    assert row["product_count"] == 2
    assert row["seller_count"] == 1

    assert row["item_value"] == 30.0
    assert row["freight_value"] == 5.0
    assert row["gross_order_value"] == 35.0
    assert row["payment_value"] == 35.0
    assert row["payment_difference"] == 0.0

    assert row["payment_transaction_count"] == 2
    assert row["payment_method_count"] == 2
    assert row["review_count"] == 1
    assert row["average_review_score"] == 5

    assert row["order_purchase_date_key"] == 20180101
    assert row["approval_time_hours"] == 2.0
    assert row["delivery_time_days"] == 3.0
    assert row["delivery_variance_days"] == -1.0
    assert bool(row["delivered_on_time"]) is True