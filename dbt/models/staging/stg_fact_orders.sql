{{ config(materialized='view') }}

select *
from read_parquet('../data/gold/olist/fact_orders.parquet')
