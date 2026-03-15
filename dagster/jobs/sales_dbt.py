from dagster import define_asset_job

sales_dbt_job = define_asset_job(
    name="sales_dbt_job",
    selection=["raw_sales_data", "raw_customers_data", "duckdb_raw_tables", "stg_sales", "stg_customers", "sales_by_month"],
)
