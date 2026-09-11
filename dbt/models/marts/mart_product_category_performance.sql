with order_items as (

    select *
    from {{ ref('stg_fact_order_items') }}

),

products as (

    select *
    from {{ ref('stg_dim_products') }}

)

select
    coalesce(
        p.product_category_name_en,
        p.product_category_name,
        'unknown'
    ) as product_category,

    count(distinct oi.product_id) as product_count,
    count(*) as items_sold,
    count(distinct oi.order_id) as order_count,

    sum(coalesce(oi.price, 0)) as item_revenue,
    sum(coalesce(oi.freight_value, 0)) as freight_revenue,
    sum(coalesce(oi.line_total, 0)) as total_line_value,

    avg(oi.price) as average_item_price,
    avg(oi.freight_value) as average_freight_value,
    avg(oi.line_total) as average_line_value

from order_items oi

inner join products p
    on oi.product_id = p.product_id

group by
    coalesce(
        p.product_category_name_en,
        p.product_category_name,
        'unknown'
    )
