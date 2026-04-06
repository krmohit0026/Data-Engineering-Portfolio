{{ config(materialized='view') }}

select
    "ALERT_ID"::string as alert_id,
    "USER_ID"::string as user_id,
    "RULE"::string as fraud_rule,
    "AMOUNT"::float as fraud_amount,
    "TIMESTAMP"::timestamp as alerted_at
from {{ source('kafka_source', 'FRAUD_ALERTS') }}