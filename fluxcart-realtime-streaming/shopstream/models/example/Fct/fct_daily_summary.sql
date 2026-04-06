{{ config(materialized='table') }}

with analytics as (
    select date_trunc('day', event_at) as event_date, 
           sum(behavior_count) as behaviors, 
           sum(total_revenue) as gross_revenue 
    from {{ ref('stg_analytics') }} group by 1
),
fraud as (
    select date_trunc('day', alerted_at) as event_date, 
           sum(fraud_amount) as potential_fraud_loss,
           count(alert_id) as alert_count
    from {{ ref('stg_fraud') }} group by 1
),
inventory as (
    select date_trunc('day', checked_at) as event_date, 
           sum(stock_units) as current_stock 
    from {{ ref('stg_inventory') }} group by 1
)

select
    a.event_date,
    a.behaviors,
    a.gross_revenue,
    coalesce(f.potential_fraud_loss, 0) as potential_fraud_loss,
    coalesce(f.alert_count, 0) as alert_count,
    coalesce(i.current_stock, 0) as current_stock
from analytics a
left join fraud f on a.event_date = f.event_date
left join inventory i on a.event_date = i.event_date