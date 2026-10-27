{{ config(materialized='view') }}

select *
from read_parquet('../data/gold/olist/fact_order_items.parquet')
