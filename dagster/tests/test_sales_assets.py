import pandas as pd
from dagster import materialize

from sales.assets import raw_customers_data, raw_sales_data, sales_report


def test_raw_sales_data_returns_dataframe():
    result = materialize(assets=[raw_sales_data])

    assert result.success

    output = result.output_for_node("raw_sales_data")
    assert isinstance(output, pd.DataFrame)
    assert set(output.columns) == {
        "order_id",
        "customer_id",
        "product_name",
        "quantity",
        "unit_price",
        "order_date",
    }


def test_raw_sales_data_loads_both_quarters():
    result = materialize(assets=[raw_sales_data])

    output = result.output_for_node("raw_sales_data")
    assert len(output) == 40  # 20 rows Q1 + 20 rows Q2


def test_raw_sales_data_order_date_is_datetime():
    result = materialize(assets=[raw_sales_data])

    output = result.output_for_node("raw_sales_data")
    assert pd.api.types.is_datetime64_any_dtype(output["order_date"])


def test_raw_customers_data_returns_dataframe():
    result = materialize(assets=[raw_customers_data])

    assert result.success

    output = result.output_for_node("raw_customers_data")
    assert isinstance(output, pd.DataFrame)
    assert set(output.columns) == {
        "customer_id",
        "name",
        "email",
        "country",
        "joined_date",
    }


def test_raw_customers_data_has_expected_row_count():
    result = materialize(assets=[raw_customers_data])

    output = result.output_for_node("raw_customers_data")
    assert len(output) == 15


def test_sales_report_returns_dataframe():
    result = materialize(assets=[raw_sales_data, raw_customers_data, sales_report])

    assert result.success

    output = result.output_for_node("sales_report")
    assert isinstance(output, pd.DataFrame)
    assert set(output.columns) == {
        "customer_id",
        "customer_name",
        "month",
        "total_revenue",
    }


def test_sales_report_has_no_null_revenue():
    result = materialize(assets=[raw_sales_data, raw_customers_data, sales_report])

    output = result.output_for_node("sales_report")
    assert output["total_revenue"].isna().sum() == 0


def test_sales_report_total_revenue_is_positive():
    result = materialize(assets=[raw_sales_data, raw_customers_data, sales_report])

    output = result.output_for_node("sales_report")
    assert (output["total_revenue"] > 0).all()


def test_sales_report_month_format_is_year_month():
    result = materialize(assets=[raw_sales_data, raw_customers_data, sales_report])

    output = result.output_for_node("sales_report")
    sample_month = output["month"].iloc[0]
    assert len(sample_month) == 7
    assert sample_month[4] == "-"


def test_sales_report_covers_expected_months():
    result = materialize(assets=[raw_sales_data, raw_customers_data, sales_report])

    output = result.output_for_node("sales_report")
    months = set(output["month"].unique())
    expected_months = {"2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"}
    assert months == expected_months
