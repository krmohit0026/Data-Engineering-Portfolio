{{config
    (materialized='incremental',
    on_schema_change='fail'
    )}}

--incremental:build this as table, but only add new rows

with SRC_ORDER_ITEMS as(
    select * from {{ref('src_order_items')}}
)

select ORDER_ID as ORDER_ID
,ORDER_ITEM_ID as ORDER_ITEM_ID
,PRODUCT_ID as PRODUCT_ID
,SELLER_ID as SELLER_ID
,PRICE as PRICE
from src_order_items



-- incremental logic
{% if is_incremental() %}

    where (ORDER_ID, ORDER_ITEM_ID) not in (select ORDER_ID, ORDER_ITEM_ID from {{ this }})

{% endif %}

-- TO EXECUTE A SINGLE FILE TO REFLECT CHANGES MADE : dbt run --model src_order_items