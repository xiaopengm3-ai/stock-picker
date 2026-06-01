"""因子标准化 — ZScore 或百分位排名."""
import numpy as np
import pandas as pd


def zscore_standardize(series: pd.Series) -> pd.Series:
    if series.dropna().empty:
        return series
    mean = series.mean()
    std = series.std()
    if std == 0:
        return pd.Series(0.0, index=series.index)
    return (series - mean) / std


def percentile_rank(series: pd.Series) -> pd.Series:
    valid = series.dropna()
    if valid.empty:
        return pd.Series(np.nan, index=series.index)
    ranks = valid.rank(pct=True) * 100.0
    result = pd.Series(np.nan, index=series.index)
    result[ranks.index] = ranks
    return result


def zscore_to_score(series: pd.Series) -> pd.Series:
    return series.apply(lambda z: max(0.0, min(100.0, 50.0 + z * 10.0)) if pd.notna(z) else np.nan)


def standardize_factor(series: pd.Series, method: str = "zscore") -> pd.Series:
    if method == "percentile":
        return percentile_rank(series)
    return zscore_standardize(series)
