{{ config(materialized='table') }}

with daily_data as (
    select * from {{ ref('fct_daily_summary') }}
)

select
    event_date,
    gross_revenue,
    potential_fraud_loss,
    (gross_revenue - potential_fraud_loss) as net_revenue,
    alert_count,
    current_stock,
    -- KPI: Is our stock keeping up with traffic?
    round(current_stock / nullif(behaviors, 0), 2) as stock_to_behavior_ratio
from daily_data