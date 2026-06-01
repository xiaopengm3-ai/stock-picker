"""成长因子 F06–F10."""
import numpy as np
import pandas as pd

from ..registry import FactorMeta, register_factor

F06_ROE = FactorMeta(
    id="F06", name="ROE(TTM)", category="fundamental", sub_category="growth",
    direction="positive", neutralize_industry=True, standardize_method="zscore",
)
F07_ROE_TREND = FactorMeta(
    id="F07", name="ROE趋势", category="fundamental", sub_category="growth",
    direction="positive", neutralize_industry=False, standardize_method="zscore",
)
F08_REVENUE_GROWTH = FactorMeta(
    id="F08", name="营收同比增速", category="fundamental", sub_category="growth",
    direction="positive", neutralize_industry=True, neutralize_market_cap=True,
    standardize_method="zscore",
)
F09_PROFIT_GROWTH = FactorMeta(
    id="F09", name="净利润同比增速", category="fundamental", sub_category="growth",
    direction="positive", neutralize_industry=True, neutralize_market_cap=True,
    standardize_method="zscore",
)
F10_GROSS_MARGIN_TREND = FactorMeta(
    id="F10", name="毛利率趋势", category="fundamental", sub_category="growth",
    direction="positive", neutralize_industry=True, standardize_method="zscore",
)


def compute_roe(indicators_df: pd.DataFrame) -> pd.Series:
    if "roe" not in indicators_df.columns or indicators_df.empty:
        all_codes = indicators_df.index.get_level_values("code").unique() if not indicators_df.empty else pd.Index([])
        return pd.Series(np.nan, index=all_codes)
    codes = indicators_df.index.get_level_values("code").unique()
    latest_data = {}
    for code in codes:
        try:
            g = indicators_df.loc[code]
            if isinstance(g, pd.Series):
                latest_data[code] = g.get("roe", np.nan)
            else:
                sorted_g = g.sort_index(level="report_date")
                latest_data[code] = sorted_g["roe"].iloc[-1] if "roe" in sorted_g.columns else np.nan
        except Exception:
            latest_data[code] = np.nan
    return pd.Series(latest_data, name="F06_score")


def compute_roe_trend(indicators_df: pd.DataFrame) -> pd.Series:
    if "roe" not in indicators_df.columns or indicators_df.empty:
        all_codes = indicators_df.index.get_level_values("code").unique() if not indicators_df.empty else pd.Index([])
        return pd.Series(np.nan, index=all_codes)
    codes = indicators_df.index.get_level_values("code").unique()
    scores = {}
    for code in codes:
        try:
            code_data = indicators_df.loc[code]
            if isinstance(code_data, pd.Series):
                scores[code] = np.nan; continue
            recent_roe = code_data["roe"].dropna().tail(4)
            if len(recent_roe) < 4:
                scores[code] = np.nan; continue
            ups = (recent_roe.diff().dropna() > 0).sum()
            scores[code] = {3: 100.0, 2: 67.0, 1: 33.0, 0: 0.0}.get(ups, np.nan)
        except Exception:
            scores[code] = np.nan
    return pd.Series(scores, name="F07_score")


def _yoy_growth(series: pd.Series, lookback: int = 4) -> float:
    """计算同比增速：取最近值 vs lookback 期前的值."""
    clean = series.dropna()
    if len(clean) < 2:
        return np.nan
    latest = clean.iloc[-1]
    if len(clean) > lookback:
        prev = clean.iloc[-(lookback + 1)]
    else:
        prev = clean.iloc[-2]
    if prev == 0:
        return np.nan
    return (latest - prev) / abs(prev) * 100.0


def compute_revenue_growth(financial_df: pd.DataFrame) -> pd.Series:
    if "revenue" not in financial_df.columns or financial_df.empty:
        all_codes = financial_df.index.get_level_values("code").unique() if not financial_df.empty else pd.Index([])
        return pd.Series(np.nan, index=all_codes)
    codes = financial_df.index.get_level_values("code").unique()
    growth = {}
    for code in codes:
        try:
            rev = financial_df.loc[code]["revenue"].dropna()
            growth[code] = _yoy_growth(rev)
        except Exception:
            growth[code] = np.nan
    return pd.Series(growth, name="F08_score")


def compute_profit_growth(financial_df: pd.DataFrame) -> pd.Series:
    if "net_profit" not in financial_df.columns or financial_df.empty:
        all_codes = financial_df.index.get_level_values("code").unique() if not financial_df.empty else pd.Index([])
        return pd.Series(np.nan, index=all_codes)
    codes = financial_df.index.get_level_values("code").unique()
    growth = {}
    for code in codes:
        try:
            profit = financial_df.loc[code]["net_profit"].dropna()
            growth[code] = _yoy_growth(profit)
        except Exception:
            growth[code] = np.nan
    return pd.Series(growth, name="F09_score")


def compute_gross_margin_trend(indicators_df: pd.DataFrame) -> pd.Series:
    if "gross_margin" not in indicators_df.columns or indicators_df.empty:
        all_codes = indicators_df.index.get_level_values("code").unique() if not indicators_df.empty else pd.Index([])
        return pd.Series(np.nan, index=all_codes)
    codes = indicators_df.index.get_level_values("code").unique()
    scores = {}
    for code in codes:
        try:
            code_data = indicators_df.loc[code]
            if isinstance(code_data, pd.Series):
                scores[code] = np.nan; continue
            gm = code_data["gross_margin"].dropna().tail(3)
            if len(gm) < 3:
                scores[code] = np.nan; continue
            ups = (gm.diff().dropna() > 0).sum()
            scores[code] = ups / 2.0 * 100.0
        except Exception:
            scores[code] = np.nan
    return pd.Series(scores, name="F10_score")


for f in [F06_ROE, F07_ROE_TREND, F08_REVENUE_GROWTH, F09_PROFIT_GROWTH, F10_GROSS_MARGIN_TREND]:
    register_factor(f)

GROWTH_FACTORS = [F06_ROE, F07_ROE_TREND, F08_REVENUE_GROWTH, F09_PROFIT_GROWTH, F10_GROSS_MARGIN_TREND]
GROWTH_WEIGHTS = {"F06": 0.30, "F07": 0.15, "F08": 0.20, "F09": 0.20, "F10": 0.15}
