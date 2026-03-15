import pandas as pd
from dagster import AssetCheckResult, AssetCheckSeverity, asset_check

from sales.assets import sales_report


@asset_check(asset=sales_report)
def no_missing_revenue(sales_report: pd.DataFrame) -> AssetCheckResult:
    """Ensure no total_revenue values are null in the sales report."""
    missing_count = sales_report["total_revenue"].isna().sum()
    passed = bool(missing_count == 0)
    return AssetCheckResult(
        passed=passed,
        severity=AssetCheckSeverity.ERROR,
        metadata={"missing_revenue_count": int(missing_count)},
    )
