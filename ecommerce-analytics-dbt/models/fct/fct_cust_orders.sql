with orders as (
    select CUSTOMER_ID, ORDER_APPROVED_AT, ORDER_ID, ORDER_PURCHASE_TIMESTAMP, ORDER_STATUS
    from {{ ref('src_orders') }}
),

cust as (
    select CUSTOMER_ID
    ,CUSTOMER_ZIP_CODE_PREFIX from {{ ref('src_customers') }}
)

select distinct customer_id,CUSTOMER_ZIP_CODE_PREFIX,ORDER_ID,ORDER_STATUS
from (select o.* ,c.CUSTOMER_ZIP_CODE_PREFIX
    from orders o
       join cust c on o.CUSTOMER_ID = c.CUSTOMER_ID
      )