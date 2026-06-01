"""估值因子 F01–F05."""
import numpy as np
import pandas as pd

from ..registry import FactorMeta, register_factor

F01_PE_PERCENTILE = FactorMeta(
    id="F01", name="PE行业分位", category="fundamental", sub_category="valuation",
    direction="negative", neutralize_industry=True, standardize_method="percentile",
)
F02_PB_PERCENTILE = FactorMeta(
    id="F02", name="PB行业分位", category="fundamental", sub_category="valuation",
    direction="negative", neutralize_industry=True, standardize_method="percentile",
)
F03_PS_PERCENTILE = FactorMeta(
    id="F03", name="PS行业分位", category="fundamental", sub_category="valuation",
    direction="negative", neutralize_industry=True, standardize_method="percentile",
)
F04_PE_ABSOLUTE = FactorMeta(
    id="F04", name="PE绝对值", category="fundamental", sub_category="valuation",
    direction="negative", neutralize_industry=True, neutralize_market_cap=True,
    standardize_method="zscore",
)
F05_DIVIDEND_YIELD = FactorMeta(
    id="F05", name="股息率", category="fundamental", sub_category="valuation",
    direction="positive", neutralize_industry=True, standardize_method="zscore",
)


def compute_pe_percentile(valuation_df: pd.DataFrame, industry_map: pd.Series) -> pd.Series:
    if "pe" not in valuation_df.columns or valuation_df.empty:
        return pd.Series(np.nan, index=valuation_df.index)
    codes = valuation_df.index
    industries = industry_map.reindex(codes).fillna("未知")
    scores = pd.Series(np.nan, index=codes, dtype=float)
    for ind in industries.unique():
        ind_codes = industries[industries == ind].index
        ind_pe = valuation_df.loc[ind_codes.intersection(valuation_df.index), "pe"]
        valid = ind_pe[ind_pe > 0]
        if len(valid) < 3:
            continue
        ranks = valid.rank(pct=True, ascending=False) * 100.0
        scores[ranks.index] = ranks
    return scores


def compute_pb_percentile(valuation_df: pd.DataFrame, industry_map: pd.Series) -> pd.Series:
    if "pb" not in valuation_df.columns or valuation_df.empty:
        return pd.Series(np.nan, index=valuation_df.index)
    codes = valuation_df.index
    industries = industry_map.reindex(codes).fillna("未知")
    scores = pd.Series(np.nan, index=codes, dtype=float)
    for ind in industries.unique():
        ind_codes = industries[industries == ind].index
        ind_pb = valuation_df.loc[ind_codes.intersection(valuation_df.index), "pb"]
        valid = ind_pb[ind_pb > 0]
        if len(valid) < 3:
            continue
        ranks = valid.rank(pct=True, ascending=False) * 100.0
        scores[ranks.index] = ranks
    return scores


def compute_ps_percentile(valuation_df: pd.DataFrame, industry_map: pd.Series) -> pd.Series:
    if "ps" not in valuation_df.columns or valuation_df.empty:
        return pd.Series(np.nan, index=valuation_df.index)
    codes = valuation_df.index
    industries = industry_map.reindex(codes).fillna("未知")
    scores = pd.Series(np.nan, index=codes, dtype=float)
    for ind in industries.unique():
        ind_codes = industries[industries == ind].index
        ind_ps = valuation_df.loc[ind_codes.intersection(valuation_df.index), "ps"]
        valid = ind_ps[ind_ps > 0]
        if len(valid) < 3:
            continue
        ranks = valid.rank(pct=True, ascending=False) * 100.0
        scores[ranks.index] = ranks
    return scores


def compute_pe_absolute(valuation_df: pd.DataFrame) -> pd.Series:
    if "pe" not in valuation_df.columns or valuation_df.empty:
        return pd.Series(np.nan, index=valuation_df.index)
    pe = valuation_df["pe"]
    scores = pd.Series(np.nan, index=pe.index, dtype=float)
    scores[(pe >= 5) & (pe <= 15)] = 100.0
    mask = (pe > 15) & (pe <= 50)
    scores[mask] = 100.0 * (50.0 - pe[mask]) / 35.0
    scores[pe > 50] = 0.0
    scores[pe <= 0] = 0.0
    return scores


def compute_dividend_yield(valuation_df: pd.DataFrame) -> pd.Series:
    if "dividend_yield" not in valuation_df.columns or valuation_df.empty:
        return pd.Series(np.nan, index=valuation_df.index)
    dy = valuation_df["dividend_yield"]
    return (dy / 3.0 * 100.0).clip(upper=100.0).where(dy.notna(), np.nan)


for f in [F01_PE_PERCENTILE, F02_PB_PERCENTILE, F03_PS_PERCENTILE, F04_PE_ABSOLUTE, F05_DIVIDEND_YIELD]:
    register_factor(f)

VALUATION_FACTORS = [F01_PE_PERCENTILE, F02_PB_PERCENTILE, F03_PS_PERCENTILE, F04_PE_ABSOLUTE, F05_DIVIDEND_YIELD]
VALUATION_WEIGHTS = {"F01": 0.30, "F02": 0.25, "F03": 0.20, "F04": 0.15, "F05": 0.10}
