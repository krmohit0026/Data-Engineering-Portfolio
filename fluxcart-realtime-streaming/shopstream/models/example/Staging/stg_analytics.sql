{{ config(materialized='view') }}

select
    "TIMESTAMP"::timestamp as event_at,
    "BEHAVIOR_EVENTS"::int as behavior_count,
    "ORDER_EVENTS"::int as order_count,
    "TOTAL_REVENUE"::float as total_revenue
from {{ source('kafka_source', 'ANALYTICS_SUMMARY') }}