{{ config(materialized='view') }}

select
    "UNITS"::int as stock_units,
    "ORDERS"::int as inventory_orders,
    "TIMESTAMP"::timestamp as checked_at
from {{ source('kafka_source', 'INVENTORY_SUMMARY') }}