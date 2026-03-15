from dagster import ScheduleDefinition, define_asset_job

sales_job = define_asset_job(
    name="sales_job",
    selection=["raw_sales_data", "raw_customers_data", "sales_report"],
)

sales_schedule = ScheduleDefinition(
    job=sales_job,
    cron_schedule="0 7 * * *",  # every day at 07:00
)
