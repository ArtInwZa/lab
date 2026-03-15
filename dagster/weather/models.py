from datetime import datetime

from pydantic import BaseModel


class WeatherRecord(BaseModel):
    location: str
    time: datetime
    temperature_celsius: float | None


class WeatherSummary(BaseModel):
    location: str
    date: str
    min_celsius: float
    max_celsius: float
    mean_celsius: float
