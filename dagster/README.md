# Dagster Pipeline

A production-grade data pipeline built with [Dagster](https://dagster.io), covering two domains: **weather forecasts** and **sales reporting**.

---

## Project Structure

```text
dagster/
├── weather/
│   ├── assets.py      # raw_weather_forecast, weather_summary
│   ├── checks.py      # no_missing_temperatures
│   └── models.py      # WeatherRecord, WeatherSummary
├── sales/
│   ├── assets.py      # raw_sales_data, raw_customers_data, sales_report
│   ├── checks.py      # no_missing_revenue
│   └── models.py      # SalesRecord, CustomerRecord, SalesReport
├── resources/
│   └── open_meteo.py  # OpenMeteoResource (shared HTTP client)
├── jobs/
│   ├── weather.py     # weather_job + weather_schedule
│   └── sales.py       # sales_job + sales_schedule
├── data/
│   └── raw/           # input CSV files
├── tests/
├── definitions.py     # Dagster entry point
└── pyproject.toml
```

### Why this structure?

Folders are organized by **domain** (weather, sales), not by type (assets, jobs). Everything related to weather lives in `weather/`, making it easy to find, change, or remove a domain without touching others.

| File | Purpose |
| --- | --- |
| `assets.py` | Business logic: fetch data, transform data |
| `checks.py` | Data quality checks, separate from business logic |
| `models.py` | Pydantic models describing the shape of data in that domain |
| `jobs/` | Job and schedule live together — a schedule is always tied to a specific job |
| `resources/` | Shared clients or connections used across domains |
| `definitions.py` | Single entry point that Dagster reads to discover everything |

---

## Concepts

### Asset

An asset represents a dataset that your pipeline produces and stores. Instead of thinking about "running a script", you think about "materializing a dataset".

```text
raw_weather_forecast  →  weather_summary

raw_sales_data   ──┐
                   ├──→  sales_report
raw_customers_data ┘
```

### Asset Check

A check runs after an asset is materialized to validate its data quality. If a check fails, Dagster marks it as an error without stopping other assets.

### Resource

A resource is a shared dependency (like an API client or database connection) injected into assets. This makes assets testable — you can swap the real resource for a mock in tests.

```python
# Asset declares it needs the resource by name
def raw_weather_forecast(open_meteo: OpenMeteoResource): ...

# definitions.py wires it up
resources={"open_meteo": OpenMeteoResource()}
```

### Job

A job is a named selection of assets that can be run together. It lets you run a subset of assets rather than everything.

### Schedule

A schedule triggers a job automatically on a cron expression.

| Schedule | Job | Cron |
| --- | --- | --- |
| `weather_schedule` | `weather_job` | `0 6 * * *` (daily 06:00) |
| `sales_schedule` | `sales_job` | `0 7 * * *` (daily 07:00) |

---

## Data Sources

### Weather (Open-Meteo)

Fetches 7-day hourly temperature forecasts for 5 cities via the [Open-Meteo API](https://open-meteo.com) — no API key required.

| City | Latitude | Longitude |
| --- | --- | --- |
| Berlin | 52.52 | 13.41 |
| Bangkok | 13.75 | 100.52 |
| New York | 40.71 | -74.01 |
| Tokyo | 35.68 | 139.69 |
| London | 51.51 | -0.13 |

### Sales (CSV files)

Reads quarterly sales files from `data/raw/sales_*.csv` and a customer master file from `data/raw/customers.csv`.

---

## How to Run

### Prerequisites

Install [uv](https://docs.astral.sh/uv/getting-started/installation/):

```bash
brew install uv
```

### Setup

```bash
uv sync
```

### Start the Dagster UI

```bash
uv run dagster dev
```

Open <http://localhost:3000> in your browser.

From the UI you can:

- **Materialize** assets individually or all at once
- **View the asset graph** to see dependencies
- **Run jobs** manually from the Launchpad
- **Enable schedules** to run jobs automatically

### Run Tests

```bash
uv run pytest
```

---

## Key Design Decisions

| Decision | Reason |
| --- | --- |
| Domain-based folder structure | Easy to find all files related to one topic. Adding a new domain means adding a new folder, not touching existing files. |
| `checks.py` separate from `assets.py` | Data quality checks are not business logic. Keeping them separate makes each file focused on one purpose. |
| Job and schedule in the same file | A schedule is meaningless without its job. Keeping them together avoids jumping between files. |
| `bool()` cast in checks | Pandas `.isna().sum()` returns `numpy.bool_`, which Dagster rejects. Wrapping with `bool()` converts it to a Python native bool. |
| Pydantic models per domain | Each domain owns its data contracts. Models in `weather/models.py` describe weather data only — no mixing with sales. |
