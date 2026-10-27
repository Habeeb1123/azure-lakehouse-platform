{{ config(materialized='view') }}

select *
from read_parquet('../data/gold/olist/dim_sellers.parquet')
