with source as (
    select * from raw_customers
)

select
    customer_id,
    name        as customer_name,
    email,
    country,
    cast(joined_date as date) as joined_date
from source
