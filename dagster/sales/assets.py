from pathlib import Path

import pandas as pd
from dagster import AssetExecutionContext, asset

DATA_DIRECTORY = Path(__file__).parent.parent / "data" / "raw"


@asset
def raw_sales_data(context: AssetExecutionContext) -> pd.DataFrame:
    """Read all quarterly sales CSV files from data/raw/ and combine into one DataFrame."""
    sales_files = sorted(DATA_DIRECTORY.glob("sales_*.csv"))

    if not sales_files:
        raise FileNotFoundError(f"No sales CSV files found in {DATA_DIRECTORY}")

    dataframes = [pd.read_csv(file) for file in sales_files]
    combined = pd.concat(dataframes, ignore_index=True)
    combined["order_date"] = pd.to_datetime(combined["order_date"])

    context.log.info(
        f"Loaded {len(combined)} sales rows from {len(sales_files)} file(s)"
    )
    return combined


@asset
def raw_customers_data(context: AssetExecutionContext) -> pd.DataFrame:
    """Read the customers master CSV from data/raw/customers.csv."""
    customers_file = DATA_DIRECTORY / "customers.csv"

    if not customers_file.exists():
        raise FileNotFoundError(f"Customers file not found at {customers_file}")

    dataframe = pd.read_csv(customers_file)
    dataframe["joined_date"] = pd.to_datetime(dataframe["joined_date"])

    context.log.info(f"Loaded {len(dataframe)} customer records")
    return dataframe


@asset
def sales_report(
    context: AssetExecutionContext,
    raw_sales_data: pd.DataFrame,
    raw_customers_data: pd.DataFrame,
) -> pd.DataFrame:
    """Join sales with customers and compute total revenue per customer per month."""
    merged = raw_sales_data.merge(
        raw_customers_data[["customer_id", "name"]],
        on="customer_id",
        how="left",
    )

    merged["total_price"] = merged["quantity"] * merged["unit_price"]
    merged["month"] = merged["order_date"].dt.to_period("M").astype(str)

    report = (
        merged.groupby(["customer_id", "name", "month"])["total_price"]
        .sum()
        .reset_index()
        .rename(columns={"name": "customer_name", "total_price": "total_revenue"})
    )

    report = report.sort_values(["month", "customer_id"]).reset_index(drop=True)

    context.log.info(
        f"Sales report has {len(report)} rows covering {report['month'].nunique()} month(s)"
    )
    return report
