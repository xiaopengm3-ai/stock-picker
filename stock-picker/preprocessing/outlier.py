"""因子去极值 — MAD 方法."""
import numpy as np
import pandas as pd


def mad_outlier_clip(series: pd.Series, multiplier: float = 5.0) -> pd.Series:
    if series.dropna().empty:
        return series
    median = series.median()
    mad = (series - median).abs().median()
    if mad == 0:
        return series
    upper = median + multiplier * mad
    lower = median - multiplier * mad
    return series.clip(lower=lower, upper=upper)


def mad_outlier_clip_dataframe(df: pd.DataFrame, multiplier: float = 5.0) -> pd.DataFrame:
    result = df.copy()
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            result[col] = mad_outlier_clip(df[col], multiplier)
    return result
