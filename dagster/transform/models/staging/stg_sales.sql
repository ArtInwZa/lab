with source as (
    select * from raw_sales
)

select
    order_id,
    customer_id,
    product_name,
    quantity,
    unit_price,
    cast(order_date as date)                    as order_date,
    quantity * unit_price                       as total_price,
    date_trunc('month', cast(order_date as date)) as order_month
from source
