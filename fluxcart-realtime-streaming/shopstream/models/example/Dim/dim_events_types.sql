{{ config(materialized='table') }}

select 'BEHAVIOR' as event_type, 'User clicks and page views' as description
union all
select 'ORDER' as event_type, 'Completed financial transactions' as description