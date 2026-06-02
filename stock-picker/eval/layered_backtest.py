"""分层回测 — 按因子得分分5组，比较各组未来收益."""
import numpy as np
import pandas as pd


def layered_backtest(
    factor_scores: pd.Series,
    forward_returns: pd.Series,
    n_groups: int = 5,
) -> dict:
    """单期分层回测.

    Args:
        factor_scores: index=code, values=因子得分
        forward_returns: index=code, values=N日后收益率
        n_groups: 分组数

    Returns:
        {"group_returns": [...], "long_short_spread": float, "monotonic": bool}
    """
    common = factor_scores.dropna().index.intersection(forward_returns.dropna().index)
    if len(common) < n_groups * 5:
        return {"group_returns": [], "long_short_spread": 0.0, "monotonic": False}

    valid = pd.DataFrame({
        "factor": factor_scores[common],
        "return": forward_returns[common],
    }).dropna()

    if len(valid) < n_groups * 3:
        return {"group_returns": [], "long_short_spread": 0.0, "monotonic": False}

    valid["group"] = pd.qcut(valid["factor"], n_groups, labels=False, duplicates="drop")
    group_returns = valid.groupby("group")["return"].mean().tolist()

    # 多空收益（最高分组 - 最低分组）
    if len(group_returns) >= 2:
        long_short = group_returns[-1] - group_returns[0]
    else:
        long_short = 0.0

    # 单调性：Q1→Q5 收益递增
    monotonic = all(group_returns[i] <= group_returns[i + 1] for i in range(len(group_returns) - 1))

    return {
        "group_returns": group_returns,
        "long_short_spread": round(long_short, 4),
        "monotonic": monotonic,
    }


def quintile_analysis(
    factor_scores: pd.Series,
    forward_returns: pd.Series,
) -> pd.DataFrame:
    """五分组详细分析."""
    common = factor_scores.dropna().index.intersection(forward_returns.dropna().index)
    if len(common) < 25:
        return pd.DataFrame()

    valid = pd.DataFrame({
        "code": common,
        "factor": factor_scores[common].values,
        "return": forward_returns[common].values,
    })

    valid["quintile"] = pd.qcut(valid["factor"], 5, labels=["Q1(低)", "Q2", "Q3", "Q4", "Q5(高)"], duplicates="drop")
    summary = valid.groupby("quintile").agg(
        count=("code", "count"),
        mean_return=("return", "mean"),
        median_return=("return", "median"),
        std_return=("return", "std"),
        win_rate=("return", lambda x: (x > 0).mean()),
    ).reset_index()

    summary["mean_return"] = summary["mean_return"].apply(lambda x: f"{x:.2%}")
    summary["win_rate"] = summary["win_rate"].apply(lambda x: f"{x:.0%}")

    return summary
