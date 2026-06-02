"""流动性过滤."""
import pandas as pd


def check_liquidity(
    codes: list[str],
    valuation_df: pd.DataFrame,
    min_turnover: float = 30_000_000,
    min_turnover_rate: float = 0.003,
    min_float_cap: float = 2_000_000_000,
) -> list[str]:
    """过滤流动性不足的股票.

    Args:
        codes: 股票列表
        valuation_df: 估值数据（含 amount/turnover_rate/float_market_cap 列）
        min_turnover: 最低日成交额（元）
        min_turnover_rate: 最低换手率
        min_float_cap: 最低流通市值（元）

    Returns:
        通过流动性检查的股票列表
    """
    valid = set(codes)

    if "amount" in valuation_df.columns:
        valid &= set(valuation_df[valuation_df["amount"] >= min_turnover].index)

    if "turnover_rate" in valuation_df.columns:
        valid &= set(valuation_df[valuation_df["turnover_rate"] >= min_turnover_rate].index)

    if "float_market_cap" in valuation_df.columns:
        valid &= set(valuation_df[valuation_df["float_market_cap"] >= min_float_cap].index)

    return [c for c in codes if c in valid]
