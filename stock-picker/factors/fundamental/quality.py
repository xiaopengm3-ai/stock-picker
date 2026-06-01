"""质量因子 F11–F15 (Phase 1: 基于 valuation 和简单规则实现核心逻辑)."""
import numpy as np
import pandas as pd

from ..registry import FactorMeta, register_factor

F11_DEBT_RATIO = FactorMeta(
    id="F11", name="资产负债率", category="fundamental", sub_category="quality",
    direction="negative", neutralize_industry=True, standardize_method="zscore",
    hard_thresholds={"max": 70.0},
)
F12_CFO_TO_PROFIT = FactorMeta(
    id="F12", name="经营现金流/净利润", category="fundamental", sub_category="quality",
    direction="positive", neutralize_industry=True, standardize_method="zscore",
    hard_thresholds={"min": 0.3},
)
F13_GOODWILL_RATIO = FactorMeta(
    id="F13", name="商誉/净资产", category="fundamental", sub_category="quality",
    direction="negative", neutralize_industry=True, standardize_method="percentile",
    hard_thresholds={"max": 50.0},
)
F14_PLEDGE_RATIO = FactorMeta(
    id="F14", name="股权质押比例", category="fundamental", sub_category="quality",
    direction="negative", neutralize_industry=False, standardize_method="zscore",
    hard_thresholds={"max": 60.0},
)
F15_INSIDER_SELLING = FactorMeta(
    id="F15", name="大股东减持", category="fundamental", sub_category="quality",
    direction="negative", neutralize_industry=False, standardize_method="zscore",
)


def compute_debt_ratio(financial_df: pd.DataFrame) -> pd.Series:
    if "debt_ratio" not in financial_df.columns or financial_df.empty:
        all_codes = financial_df.index.get_level_values("code").unique() if not financial_df.empty else pd.Index([])
        return pd.Series(np.nan, index=all_codes)
    codes = financial_df.index.get_level_values("code").unique()
    values = {}
    for code in codes:
        try:
            dr = financial_df.loc[code]["debt_ratio"].dropna()
            values[code] = dr.iloc[-1] if len(dr) > 0 else np.nan
        except Exception:
            values[code] = np.nan
    dr = pd.Series(values)
    scores = (1.0 - dr / 70.0) * 100.0  # ≤40%→满分, ≥70%→0分
    return scores.clip(lower=0.0, upper=100.0).where(dr.notna(), np.nan)


def compute_cfo_to_profit(financial_df: pd.DataFrame) -> pd.Series:
    if "operating_cf" not in financial_df.columns or "net_profit" not in financial_df.columns or financial_df.empty:
        all_codes = financial_df.index.get_level_values("code").unique() if not financial_df.empty else pd.Index([])
        return pd.Series(np.nan, index=all_codes)
    codes = financial_df.index.get_level_values("code").unique()
    values = {}
    for code in codes:
        try:
            data = financial_df.loc[code]
            cf = data["operating_cf"].dropna()
            profit = data["net_profit"].dropna()
            if len(cf) > 0 and len(profit) > 0:
                v = cf.iloc[-1] / abs(profit.iloc[-1]) if profit.iloc[-1] != 0 else np.nan
                values[code] = v
            else:
                values[code] = np.nan
        except Exception:
            values[code] = np.nan
    ratio = pd.Series(values)
    scores = ratio.clip(lower=0.0, upper=1.0) * 100.0  # ≥1.0→满分
    return scores.where(ratio.notna(), np.nan)


def compute_goodwill_ratio(financial_df: pd.DataFrame) -> pd.Series:
    if "goodwill" not in financial_df.columns or "net_equity" not in financial_df.columns or financial_df.empty:
        all_codes = financial_df.index.get_level_values("code").unique() if not financial_df.empty else pd.Index([])
        return pd.Series(np.nan, index=all_codes)
    codes = financial_df.index.get_level_values("code").unique()
    values = {}
    for code in codes:
        try:
            data = financial_df.loc[code]
            gw = data["goodwill"].dropna()
            eq = data["net_equity"].dropna()
            if len(gw) > 0 and len(eq) > 0 and eq.iloc[-1] > 0:
                values[code] = gw.iloc[-1] / eq.iloc[-1]
            else:
                values[code] = np.nan
        except Exception:
            values[code] = np.nan
    gr = pd.Series(values)
    scores = (1.0 - gr / 0.50) * 100.0  # ≤10%→满分, ≥50%→0分
    return scores.clip(lower=0.0, upper=100.0).where(gr.notna(), np.nan)


def compute_pledge_ratio(financial_df: pd.DataFrame) -> pd.Series:
    """F14: 股权质押比例 — 占位实现，返回默认 50 分."""
    if financial_df.empty:
        return pd.Series()
    codes = financial_df.index.get_level_values("code").unique()
    return pd.Series(50.0, index=codes, name="F14_score")


def compute_insider_selling(financial_df: pd.DataFrame) -> pd.Series:
    """F15: 大股东减持 — 占位实现，返回默认 80 分（无减持默认高分）."""
    if financial_df.empty:
        return pd.Series()
    codes = financial_df.index.get_level_values("code").unique()
    return pd.Series(80.0, index=codes, name="F15_score")


for f in [F11_DEBT_RATIO, F12_CFO_TO_PROFIT, F13_GOODWILL_RATIO, F14_PLEDGE_RATIO, F15_INSIDER_SELLING]:
    register_factor(f)

QUALITY_FACTORS = [F11_DEBT_RATIO, F12_CFO_TO_PROFIT, F13_GOODWILL_RATIO, F14_PLEDGE_RATIO, F15_INSIDER_SELLING]
QUALITY_WEIGHTS = {"F11": 0.25, "F12": 0.30, "F13": 0.25, "F14": 0.10, "F15": 0.10}
