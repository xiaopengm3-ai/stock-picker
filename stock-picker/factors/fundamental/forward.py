"""预期因子 F16–F20 (Phase 1: 占位实现)."""
import numpy as np
import pandas as pd

from ..registry import FactorMeta, register_factor

F16_EARNINGS_FORECAST = FactorMeta(
    id="F16", name="业绩预告方向", category="fundamental", sub_category="forward",
    direction="positive", neutralize_industry=False, standardize_method="zscore",
)
F17_ANALYST_UPGRADE = FactorMeta(
    id="F17", name="分析师预期上调", category="fundamental", sub_category="forward",
    direction="positive", neutralize_industry=True, standardize_method="zscore",
)
F18_ADVANCE_RECEIPTS = FactorMeta(
    id="F18", name="预收账款/合同负债环比", category="fundamental", sub_category="forward",
    direction="positive", neutralize_industry=True, standardize_method="zscore",
)
F19_CFO_TREND = FactorMeta(
    id="F19", name="现金流趋势", category="fundamental", sub_category="forward",
    direction="positive", neutralize_industry=True, standardize_method="zscore",
)
F20_INSIDER_BUYING = FactorMeta(
    id="F20", name="管理层增持", category="fundamental", sub_category="forward",
    direction="positive", neutralize_industry=False, standardize_method="zscore",
)


def compute_earnings_forecast(financial_df: pd.DataFrame) -> pd.Series:
    """F16: 业绩预告 — 占位实现，默认 50 分."""
    if financial_df.empty:
        return pd.Series()
    codes = financial_df.index.get_level_values("code").unique()
    return pd.Series(50.0, index=codes, name="F16_score")


def compute_analyst_upgrade(financial_df: pd.DataFrame) -> pd.Series:
    if financial_df.empty:
        return pd.Series()
    codes = financial_df.index.get_level_values("code").unique()
    return pd.Series(50.0, index=codes, name="F17_score")


def compute_advance_receipts(financial_df: pd.DataFrame) -> pd.Series:
    if financial_df.empty:
        return pd.Series()
    codes = financial_df.index.get_level_values("code").unique()
    return pd.Series(50.0, index=codes, name="F18_score")


def compute_cfo_trend(financial_df: pd.DataFrame) -> pd.Series:
    if financial_df.empty:
        return pd.Series()
    codes = financial_df.index.get_level_values("code").unique()
    return pd.Series(50.0, index=codes, name="F19_score")


def compute_insider_buying(financial_df: pd.DataFrame) -> pd.Series:
    if financial_df.empty:
        return pd.Series()
    codes = financial_df.index.get_level_values("code").unique()
    return pd.Series(50.0, index=codes, name="F20_score")


for f in [F16_EARNINGS_FORECAST, F17_ANALYST_UPGRADE, F18_ADVANCE_RECEIPTS, F19_CFO_TREND, F20_INSIDER_BUYING]:
    register_factor(f)

FORWARD_FACTORS = [F16_EARNINGS_FORECAST, F17_ANALYST_UPGRADE, F18_ADVANCE_RECEIPTS, F19_CFO_TREND, F20_INSIDER_BUYING]
FORWARD_WEIGHTS = {"F16": 0.30, "F17": 0.25, "F18": 0.20, "F19": 0.15, "F20": 0.10}
