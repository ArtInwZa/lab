from dagster import Definitions

from jobs.sales import sales_job, sales_schedule
from jobs.sales_dbt import sales_dbt_job
from jobs.weather import weather_job, weather_schedule
from resources.dbt import dbt_resource
from resources.open_meteo import OpenMeteoResource
from sales.assets import raw_customers_data, raw_sales_data, sales_report
from sales.checks import no_missing_revenue
from sales.dbt_assets import duckdb_raw_tables, sales_dbt_assets
from weather.assets import raw_weather_forecast, weather_summary
from weather.checks import no_missing_temperatures

defs = Definitions(
    assets=[
        # weather
        raw_weather_forecast,
        weather_summary,
        # sales (pandas pipeline)
        raw_sales_data,
        raw_customers_data,
        sales_report,
        # sales (dbt pipeline)
        duckdb_raw_tables,
        sales_dbt_assets,
    ],
    asset_checks=[
        no_missing_temperatures,
        no_missing_revenue,
    ],
    resources={
        "open_meteo": OpenMeteoResource(),
        "dbt": dbt_resource,
    },
    jobs=[
        weather_job,
        sales_job,
        sales_dbt_job,
    ],
    schedules=[
        weather_schedule,
        sales_schedule,
    ],
)
