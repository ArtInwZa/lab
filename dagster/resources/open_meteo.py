from dagster import ConfigurableResource


class OpenMeteoResource(ConfigurableResource):
    base_url: str = "https://api.open-meteo.com/v1"
    timeout: int = 30
