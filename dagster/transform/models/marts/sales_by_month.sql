with sales as (
    select * from {{ ref('stg_sales') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

joined as (
    select
        sales.order_month,
        sales.customer_id,
        customers.customer_name,
        customers.country,
        sum(sales.total_price) as total_revenue,
        count(sales.order_id)  as order_count
    from sales
    left join customers on sales.customer_id = customers.customer_id
    group by 1, 2, 3, 4
)

select * from joined
order by order_month, total_revenue desc
