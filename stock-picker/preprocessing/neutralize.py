"""因子中性化 — 行业中性化 + 市值中性化."""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def industry_neutralize(factor_values: pd.Series, industry_map: pd.Series) -> pd.Series:
    df = pd.DataFrame({"factor": factor_values, "industry": industry_map})
    industry_means = df.groupby("industry")["factor"].transform("mean")
    neutralized = df["factor"] - industry_means
    return neutralized.where(factor_values.notna(), np.nan)


def market_cap_neutralize(factor_values: pd.Series, market_caps: pd.Series) -> pd.Series:
    valid_mask = factor_values.notna() & market_caps.notna() & (market_caps > 0)
    if valid_mask.sum() < 10:
        return factor_values.copy()
    X = np.log(market_caps[valid_mask]).values.reshape(-1, 1)
    y = factor_values[valid_mask].values
    model = LinearRegression()
    model.fit(X, y)
    predicted = model.predict(X)
    result = pd.Series(np.nan, index=factor_values.index)
    result[valid_mask] = y - predicted
    return result


def dual_neutralize(
    factor_values: pd.Series, industry_map: pd.Series, market_caps: pd.Series,
) -> pd.Series:
    ind_neut = industry_neutralize(factor_values, industry_map)
    return market_cap_neutralize(ind_neut, market_caps)
