import requests
import pandas as pd
from dagster import AssetExecutionContext, asset

from resources.open_meteo import OpenMeteoResource

LOCATIONS = [
    {"name": "Berlin",   "latitude": 52.52,  "longitude": 13.41},
    {"name": "Bangkok",  "latitude": 13.75,  "longitude": 100.52},
    {"name": "New York", "latitude": 40.71,  "longitude": -74.01},
    {"name": "Tokyo",    "latitude": 35.68,  "longitude": 139.69},
    {"name": "London",   "latitude": 51.51,  "longitude": -0.13},
]


@asset
def raw_weather_forecast(
    context: AssetExecutionContext,
    open_meteo: OpenMeteoResource,
) -> pd.DataFrame:
    """Fetch hourly temperature forecast for each location from Open-Meteo."""
    rows = []

    for location in LOCATIONS:
        response = requests.get(
            url=f"{open_meteo.base_url}/forecast",
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "hourly": "temperature_2m",
            },
            timeout=open_meteo.timeout,
        )
        response.raise_for_status()

        data = response.json()
        for time, temperature in zip(
            data["hourly"]["time"],
            data["hourly"]["temperature_2m"],
        ):
            rows.append(
                {
                    "location": location["name"],
                    "time": time,
                    "temperature_celsius": temperature,
                }
            )

    dataframe = pd.DataFrame(rows)
    dataframe["time"] = pd.to_datetime(dataframe["time"])

    context.log.info(
        f"Fetched {len(dataframe)} hourly records across {len(LOCATIONS)} locations"
    )
    return dataframe


@asset
def weather_summary(
    context: AssetExecutionContext,
    raw_weather_forecast: pd.DataFrame,
) -> pd.DataFrame:
    """Compute daily min, max, and mean temperature per location."""
    dataframe = raw_weather_forecast.copy()
    dataframe["date"] = dataframe["time"].dt.date

    summary = (
        dataframe.groupby(["location", "date"])["temperature_celsius"]
        .agg(min_celsius="min", max_celsius="max", mean_celsius="mean")
        .reset_index()
    )

    context.log.info(f"Summary has {len(summary)} location-day rows")
    return summary
