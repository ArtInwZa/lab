from dagster import ScheduleDefinition, define_asset_job

weather_job = define_asset_job(
    name="weather_job",
    selection=["raw_weather_forecast", "weather_summary"],
)

weather_schedule = ScheduleDefinition(
    job=weather_job,
    cron_schedule="0 6 * * *",  # every day at 06:00
)
