import pandas as pd
from dagster import AssetCheckResult, AssetCheckSeverity, asset_check

from weather.assets import raw_weather_forecast


@asset_check(asset=raw_weather_forecast)
def no_missing_temperatures(raw_weather_forecast: pd.DataFrame) -> AssetCheckResult:
    """Ensure no hourly temperature values are null."""
    missing_count = raw_weather_forecast["temperature_celsius"].isna().sum()
    passed = bool(missing_count == 0)
    return AssetCheckResult(
        passed=passed,
        severity=AssetCheckSeverity.ERROR,
        metadata={"missing_temperature_count": int(missing_count)},
    )
