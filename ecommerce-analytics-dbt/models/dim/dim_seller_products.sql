--ephemeral materialization
-- they are not views or tables but just cte in downstream models

{{config(materialized='ephemeral')}}

with products as(
    select PRODUCT_ID,
    PRODUCT_CATEGORY_NAME,
     from {{ref('src_products')}}
),

with seller as (
    select SELLER_ID,SELLER_ZIP_CODE_PREFIX from {{ ref('src_sellers') }}
),

with order as (
    select ORDER_ID
    ,PRODUCT_ID
    ,SELLER_ID
     from {{ ref('src_order_items') }}
)

final as (
    select o.ORDER_ID, p.PRODUCT_ID, s.SELLER_ID
    from order o
    left join products p on o.PRODUCT_ID = p.PRODUCT_ID
    left join seller s on o.SELLER_ID = s.SELLER_ID
)

select * from final 