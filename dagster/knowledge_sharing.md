# Knowledge Sharing: Dagster + dbt

---

## What is Dagster?

Dagster is a **data orchestrator** — a tool that manages when, how, and in what order your data pipelines run.

Think of it this way:

> Without Dagster: you write scripts and run them manually or via cron, hoping dependencies are in the right order.
> With Dagster: you declare what each piece of data depends on, and Dagster figures out the order, runs them, tracks history, and alerts you when something breaks.

### Core idea: Assets, not tasks

Most orchestrators (like Airflow) think in terms of **tasks** — "run this function at this time."

Dagster thinks in terms of **assets** — "produce this dataset, which depends on these other datasets."

This shift matters because:
- You can see *what data exists* and *when it was last updated*
- You can re-run only the assets that are out of date
- Dependencies are explicit and visible in the UI as a graph

---

## Core Concepts

### Asset

A function decorated with `@asset` that produces a dataset.

```python
@asset
def raw_weather_forecast(open_meteo: OpenMeteoResource) -> pd.DataFrame:
    # fetch data from API
    # return a DataFrame — Dagster stores it automatically
    ...
```

- The **return value** is the dataset (Dagster calls this "materializing" the asset)
- The **function argument names** declare dependencies — if an argument matches another asset name, Dagster knows to run that asset first and pass its output in

```python
@asset
def weather_summary(raw_weather_forecast: pd.DataFrame) -> pd.DataFrame:
    # raw_weather_forecast is automatically injected
    # because an asset with that name exists
    ...
```

### Asset Check

A function decorated with `@asset_check` that validates a dataset after it is materialized.

```python
@asset_check(asset=raw_weather_forecast)
def no_missing_temperatures(raw_weather_forecast: pd.DataFrame) -> AssetCheckResult:
    missing_count = raw_weather_forecast["temperature_celsius"].isna().sum()
    passed = bool(missing_count == 0)
    return AssetCheckResult(passed=passed, ...)
```

- Runs automatically after the asset it checks
- Result (pass/fail + metadata) is visible in the UI
- Does **not** stop other assets if it fails — just flags the issue

**Important:** Always wrap numpy boolean with `bool()` — Dagster requires a native Python `bool`, not `numpy.bool_`.

### Resource

A shared dependency (API client, database connection, config) injected into assets.

```python
class OpenMeteoResource(ConfigurableResource):
    base_url: str = "https://api.open-meteo.com/v1"
    timeout: int = 30
```

- Declared as a type-annotated argument in the asset function
- Wired up in `definitions.py` using a string key
- Makes assets testable — swap the real resource for a mock in tests without changing asset code

```python
# asset declares it needs "open_meteo"
def raw_weather_forecast(open_meteo: OpenMeteoResource): ...

# definitions.py wires the key to the implementation
resources={"open_meteo": OpenMeteoResource()}
```

### Job

A named selection of assets to run together.

```python
weather_job = define_asset_job(
    name="weather_job",
    selection=["raw_weather_forecast", "weather_summary"],
)
```

- Lets you run a subset of assets rather than everything
- Can be triggered manually from the Launchpad or by a schedule

### Schedule

Triggers a job automatically on a cron expression.

```python
weather_schedule = ScheduleDefinition(
    job=weather_job,
    cron_schedule="0 6 * * *",  # every day at 06:00
)
```

Job and schedule live in the same file because a schedule is meaningless without its job.

### Definitions

The single entry point Dagster reads at startup. Registers everything — assets, checks, resources, jobs, schedules.

```python
defs = Definitions(
    assets=[...],
    asset_checks=[...],
    resources={...},
    jobs=[...],
    schedules=[...],
)
```

---

## Project Structure

```text
dagster/
├── weather/
│   ├── assets.py          # raw_weather_forecast, weather_summary
│   ├── checks.py          # no_missing_temperatures
│   └── models.py          # Pydantic models for weather data
├── sales/
│   ├── assets.py          # raw_sales_data, raw_customers_data, sales_report
│   ├── checks.py          # no_missing_revenue
│   ├── dbt_assets.py      # duckdb_raw_tables, sales_dbt_assets
│   └── models.py          # Pydantic models for sales data
├── resources/
│   ├── open_meteo.py      # OpenMeteoResource
│   └── dbt.py             # DbtCliResource config
├── jobs/
│   ├── weather.py         # weather_job + weather_schedule
│   ├── sales.py           # sales_job + sales_schedule
│   └── sales_dbt.py       # sales_dbt_job
├── transform/             # dbt project
│   ├── models/
│   │   ├── staging/
│   │   │   ├── stg_sales.sql
│   │   │   └── stg_customers.sql
│   │   └── marts/
│   │       └── sales_by_month.sql
│   ├── dbt_project.yml
│   └── profiles.yml
├── data/raw/              # CSV input files
├── tests/
├── definitions.py         # Dagster entry point
└── pyproject.toml
```

**Why domain-based folders?**
Everything related to one topic (weather, sales) lives together. Adding a new domain = add a new folder, not touch existing files.

---

## Pipeline 1: Weather Forecast

**Source:** Open-Meteo API (free, no key required)

**Asset graph:**

```text
raw_weather_forecast ──→ weather_summary
        │
        └──→ no_missing_temperatures (check)
```

**What each asset does:**

| Asset | File | What it does |
| --- | --- | --- |
| `raw_weather_forecast` | [weather/assets.py](weather/assets.py) | Calls Open-Meteo API for 5 cities, returns 168 hourly rows per city (7 days × 24h) |
| `weather_summary` | [weather/assets.py](weather/assets.py) | Groups by location + date, computes daily min/max/mean temperature |
| `no_missing_temperatures` | [weather/checks.py](weather/checks.py) | Validates no null temperature values exist |

**Job:** `weather_job` runs daily at 06:00

---

## Pipeline 2: Sales Report (Pandas)

**Source:** CSV files in `data/raw/`

**Asset graph:**

```text
raw_sales_data   ──┐
                   ├──→ sales_report ──→ no_missing_revenue (check)
raw_customers_data ┘
```

**What each asset does:**

| Asset | File | What it does |
| --- | --- | --- |
| `raw_sales_data` | [sales/assets.py](sales/assets.py) | Reads all `sales_*.csv` files, concatenates into one DataFrame |
| `raw_customers_data` | [sales/assets.py](sales/assets.py) | Reads `customers.csv` |
| `sales_report` | [sales/assets.py](sales/assets.py) | Joins sales + customers, computes total revenue per customer per month |
| `no_missing_revenue` | [sales/checks.py](sales/checks.py) | Validates no null revenue values exist |

**Job:** `sales_job` runs daily at 07:00

---

## Pipeline 3: Sales + dbt (Dagster + dbt integration)

This pipeline demonstrates how Dagster and dbt work together.

**Asset graph:**

```text
raw_sales_data   ──┐
                   ├──→ duckdb_raw_tables ──→ stg_sales ──┐
raw_customers_data ┘                        stg_customers ─┴──→ sales_by_month
```

Python assets (Dagster) feed into SQL models (dbt), all visible as one graph in the UI.

### How Dagster + dbt works

dbt has a file called `manifest.json` — a blueprint of every model, its dependencies, and its tests.
`dagster-dbt` reads this file and automatically turns every dbt model into a Dagster asset.

```python
@dbt_assets(manifest=DBT_PROJECT_DIR / "target" / "manifest.json")
def sales_dbt_assets(context, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()
```

One decorated function creates assets for all three dbt models: `stg_sales`, `stg_customers`, `sales_by_month`.

`dbt build` = run models + run tests in one command.
`yield from ... .stream()` = stream dbt logs into Dagster UI in real-time.

### dbt models explained

**staging/stg_sales.sql** — clean raw sales data, compute derived columns

```sql
select
    order_id,
    customer_id,
    quantity * unit_price as total_price,
    date_trunc('month', cast(order_date as date)) as order_month
from raw_sales
```

**staging/stg_customers.sql** — clean raw customer data, rename columns

```sql
select
    customer_id,
    name as customer_name,
    country,
    cast(joined_date as date) as joined_date
from raw_customers
```

**marts/sales_by_month.sql** — join + aggregate into final report

```sql
select
    sales.order_month,
    sales.customer_id,
    customers.customer_name,
    sum(sales.total_price) as total_revenue,
    count(sales.order_id) as order_count
from {{ ref('stg_sales') }} as sales
left join {{ ref('stg_customers') }} as customers on sales.customer_id = customers.customer_id
group by 1, 2, 3, 4
```

`{{ ref('stg_sales') }}` is dbt's way of declaring a dependency on another model. dbt resolves the execution order automatically — same idea as Dagster's asset dependencies.

### Why duckdb_raw_tables exists (local demo only)

dbt runs SQL — it needs data to be in a **database table**, not in a Python DataFrame in memory.

`duckdb_raw_tables` is a bridge asset that loads the DataFrames into DuckDB so dbt can `SELECT * FROM raw_sales`.

```python
@asset(deps=["raw_sales_data", "raw_customers_data"])
def duckdb_raw_tables(context) -> None:
    # load CSVs into DuckDB tables
    ...
```

`deps=[...]` tells Dagster to wait for those assets without receiving their output as arguments.

**In production this bridge does not exist** — dbt reads directly from a data warehouse (Snowflake, BigQuery, Redshift) where data is already loaded.

---

## Division of Responsibility: Dagster vs dbt

| Concern | Tool |
| --- | --- |
| Fetch data from APIs | Dagster |
| Load data from files | Dagster |
| Orchestrate execution order | Dagster |
| Schedule and monitor pipelines | Dagster |
| Clean and type-cast raw data | dbt |
| Join and aggregate into reports | dbt |
| SQL-based data quality tests | dbt |

---

## Known Gotchas

### numpy.bool_ vs bool

Pandas operations like `.isna().sum() == 0` return `numpy.bool_`, not Python `bool`.
Dagster's `AssetCheckResult` requires native `bool` and will raise a `ParameterCheckError` if it receives `numpy.bool_`.

**Fix:** always wrap with `bool()`:

```python
passed = bool(missing_count == 0)   # correct
passed = missing_count == 0          # breaks Dagster
```

### dbt manifest.json must exist before dagster dev

Dagster reads `manifest.json` at startup to discover dbt assets. If the file does not exist, Dagster will fail to load.

Generate it once before running:

```bash
cd transform
uv run dbt compile
```

---

## How to Run

```bash
# install dependencies
uv sync

# generate dbt manifest (first time only, or after changing dbt models)
cd transform && uv run dbt compile && cd ..

# start Dagster UI
uv run dagster dev
```

Open <http://localhost:3000>

---

## Deployment Options

| Option | Docker needed | Data stays in | Best for |
| --- | --- | --- | --- |
| Local (`dagster dev`) | No | Your machine | Development |
| Dagster Cloud Serverless | No (auto-built) | Dagster Cloud | Learning, small projects |
| Dagster Cloud Hybrid | Yes | Your infrastructure | Production with privacy requirements |
| Self-hosted | Yes | Your infrastructure | Full control, enterprise |

**Dagster Cloud Serverless** — connect your GitHub repo, Dagster builds and runs everything automatically. No Dockerfile needed. Not suitable for sensitive data.

**Dagster Cloud Hybrid** — UI and scheduling live on Dagster Cloud, but your code runs on your own server. Only metadata (run status, logs) leaves your network. Data never does.
