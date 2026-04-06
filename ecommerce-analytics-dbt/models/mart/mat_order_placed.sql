--we are going to use the seed table that we have created
{{config(materialized='table')}}

with fct_order_items as (
    select * from {{ref('fct_order_items')}}
),
seed_order_placed as (
    select * from {{ref('order_placed')}}
)

select
f.*
,case when d.DELIVERY_DATE is null then 'UNKNOWN' else 'KNOWN' end as DELIVERY_STATUS
from fct_order_items f
left join seed_order_placed d