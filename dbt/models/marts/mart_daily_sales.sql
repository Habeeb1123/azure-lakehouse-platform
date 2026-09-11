with orders as (

    select *
    from {{ ref('stg_fact_orders') }}

),

dates as (

    select *
    from {{ ref('stg_dim_date') }}

)

select
    d.date_key,
    cast(d.date as date) as order_date,
    d.year,
    d.quarter,
    d.month,
    d.month_name,
    d.day_of_week,
    d.day_name,
    d.is_weekend,

    count(*) as order_count,
    count(distinct o.customer_unique_id) as unique_customers,

    sum(coalesce(o.item_count, 0)) as items_sold,
    sum(coalesce(o.item_value, 0)) as item_revenue,
    sum(coalesce(o.freight_value, 0)) as freight_revenue,
    sum(coalesce(o.gross_order_value, 0)) as gross_revenue,
    sum(coalesce(o.payment_value, 0)) as payment_value,

    avg(o.gross_order_value) as average_order_value,
    avg(o.average_review_score) as average_review_score,
    avg(o.delivery_time_days) as average_delivery_time_days,

    sum(
        case
            when o.order_status = 'delivered' then 1
            else 0
        end
    ) as delivered_order_count,

    sum(
        case
            when o.delivered_on_time = true then 1
            else 0
        end
    ) as on_time_delivery_count

from orders o

inner join dates d
    on o.order_purchase_date_key = d.date_key

group by
    d.date_key,
    d.date,
    d.year,
    d.quarter,
    d.month,
    d.month_name,
    d.day_of_week,
    d.day_name,
    d.is_weekend
