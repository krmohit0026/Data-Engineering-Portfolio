{% snapshot snap_cust %}

{{config(
    target_schema='snapshots',
    unique_key=['CUSTOMER_ID', 'CUSTOMER_UNIQUE_ID'],
    strategy='check',             
    check_cols=['CUSTOMER_CITY'],
    invalidate_hard_deletes=True
)}}

SELECT
{{dbt_utils.generate_surrogate_key(['CUSTOMER_ID', 'CUSTOMER_UNIQUE_ID'])}} AS row_key,
CUSTOMER_ID,
CUSTOMER_UNIQUE_ID,
CUSTOMER_CITY
FROM {{ ref('src_customers') }}
LIMIT 100

{% endsnapshot %}

-- surrogate key means we are creating a unique key for each row by combining
-- user_id, movie_id and tag columns

-- this is useful because it allows to track changes to the data over time
-- by adding surrogate key, w can ensure that each row in the snapshot is uniquely identifiable

-- run this dbt snapshot : dbt snapshot