from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from dagster import materialize

from resources.open_meteo import OpenMeteoResource
from weather.assets import raw_weather_forecast, weather_summary

BERLIN_MOCK_RESPONSE = {
    "hourly": {
        "time": ["2024-01-01T00:00", "2024-01-01T01:00", "2024-01-01T02:00"],
        "temperature_2m": [2.1, 1.8, 1.5],
    }
}

BANGKOK_MOCK_RESPONSE = {
    "hourly": {
        "time": ["2024-01-01T00:00", "2024-01-01T01:00", "2024-01-01T02:00"],
        "temperature_2m": [28.0, 27.5, 27.0],
    }
}

NEW_YORK_MOCK_RESPONSE = {
    "hourly": {
        "time": ["2024-01-01T00:00", "2024-01-01T01:00", "2024-01-01T02:00"],
        "temperature_2m": [-1.0, -1.5, -2.0],
    }
}

TOKYO_MOCK_RESPONSE = {
    "hourly": {
        "time": ["2024-01-01T00:00", "2024-01-01T01:00", "2024-01-01T02:00"],
        "temperature_2m": [5.0, 4.5, 4.0],
    }
}

LONDON_MOCK_RESPONSE = {
    "hourly": {
        "time": ["2024-01-01T00:00", "2024-01-01T01:00", "2024-01-01T02:00"],
        "temperature_2m": [8.0, 7.5, 7.0],
    }
}

LOCATION_RESPONSES = [
    BERLIN_MOCK_RESPONSE,
    BANGKOK_MOCK_RESPONSE,
    NEW_YORK_MOCK_RESPONSE,
    TOKYO_MOCK_RESPONSE,
    LONDON_MOCK_RESPONSE,
]


def build_mock_response(data: dict) -> MagicMock:
    mock_response = MagicMock()
    mock_response.json.return_value = data
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mocked_open_meteo_requests():
    mock_responses = [build_mock_response(data) for data in LOCATION_RESPONSES]
    with patch("weather.assets.requests.get", side_effect=mock_responses) as mock_get:
        yield mock_get


def test_raw_weather_forecast_returns_dataframe(mocked_open_meteo_requests):
    result = materialize(
        assets=[raw_weather_forecast],
        resources={"open_meteo": OpenMeteoResource()},
    )

    assert result.success

    output = result.output_for_node("raw_weather_forecast")
    assert isinstance(output, pd.DataFrame)
    assert set(output.columns) == {"location", "time", "temperature_celsius"}
    assert len(output) == 15  # 5 locations x 3 hours each


def test_raw_weather_forecast_has_correct_locations(mocked_open_meteo_requests):
    result = materialize(
        assets=[raw_weather_forecast],
        resources={"open_meteo": OpenMeteoResource()},
    )

    output = result.output_for_node("raw_weather_forecast")
    expected_locations = {"Berlin", "Bangkok", "New York", "Tokyo", "London"}
    assert set(output["location"].unique()) == expected_locations


def test_raw_weather_forecast_time_column_is_datetime(mocked_open_meteo_requests):
    result = materialize(
        assets=[raw_weather_forecast],
        resources={"open_meteo": OpenMeteoResource()},
    )

    output = result.output_for_node("raw_weather_forecast")
    assert pd.api.types.is_datetime64_any_dtype(output["time"])


def test_weather_summary_aggregates_by_location_and_date(mocked_open_meteo_requests):
    result = materialize(
        assets=[raw_weather_forecast, weather_summary],
        resources={"open_meteo": OpenMeteoResource()},
    )

    assert result.success

    output = result.output_for_node("weather_summary")
    assert isinstance(output, pd.DataFrame)
    assert set(output.columns) == {"location", "date", "min_celsius", "max_celsius", "mean_celsius"}


def test_weather_summary_min_is_less_than_or_equal_to_max(mocked_open_meteo_requests):
    result = materialize(
        assets=[raw_weather_forecast, weather_summary],
        resources={"open_meteo": OpenMeteoResource()},
    )

    output = result.output_for_node("weather_summary")
    assert (output["min_celsius"] <= output["max_celsius"]).all()
