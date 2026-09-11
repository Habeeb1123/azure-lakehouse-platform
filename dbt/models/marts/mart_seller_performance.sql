with order_items as (

    select *
    from {{ ref('stg_fact_order_items') }}

),

sellers as (

    select *
    from {{ ref('stg_dim_sellers') }}

)

select
    s.seller_id,
    s.seller_city,
    s.seller_state,

    count(*) as items_sold,
    count(distinct oi.order_id) as order_count,
    count(distinct oi.product_id) as distinct_products_sold,

    sum(coalesce(oi.price, 0)) as item_revenue,
    sum(coalesce(oi.freight_value, 0)) as freight_value,
    sum(coalesce(oi.line_total, 0)) as total_line_value,

    avg(oi.price) as average_item_price,
    avg(oi.freight_value) as average_freight_value,
    avg(oi.line_total) as average_line_value

from order_items oi

inner join sellers s
    on oi.seller_id = s.seller_id

group by
    s.seller_id,
    s.seller_city,
    s.seller_state
