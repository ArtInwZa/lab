from pathlib import Path

import duckdb
import pandas as pd
from dagster import AssetExecutionContext, asset
from dagster_dbt import DbtCliResource, dbt_assets

DBT_PROJECT_DIR = Path(__file__).parent.parent / "transform"
DUCKDB_PATH = Path(__file__).parent.parent / "data" / "sales.duckdb"


@asset(deps=["raw_sales_data", "raw_customers_data"])
def duckdb_raw_tables(context: AssetExecutionContext) -> None:
    """Load raw sales and customers CSVs into DuckDB so dbt can read them."""
    data_dir = Path(__file__).parent.parent / "data" / "raw"

    sales_files = sorted(data_dir.glob("sales_*.csv"))
    raw_sales = pd.concat([pd.read_csv(f) for f in sales_files], ignore_index=True)
    raw_customers = pd.read_csv(data_dir / "customers.csv")

    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(DUCKDB_PATH)) as connection:
        connection.register("raw_sales_df", raw_sales)
        connection.execute("CREATE OR REPLACE TABLE raw_sales AS SELECT * FROM raw_sales_df")

        connection.register("raw_customers_df", raw_customers)
        connection.execute("CREATE OR REPLACE TABLE raw_customers AS SELECT * FROM raw_customers_df")

    context.log.info(
        f"Loaded {len(raw_sales)} sales rows and {len(raw_customers)} customer rows into DuckDB"
    )


@dbt_assets(manifest=DBT_PROJECT_DIR / "target" / "manifest.json")
def sales_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    """Run all dbt models in the transform project."""
    yield from dbt.cli(["build"], context=context).stream()
