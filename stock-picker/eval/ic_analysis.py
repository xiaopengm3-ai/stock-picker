"""IC / ICIR 分析."""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr


def compute_ic(factor_scores: pd.Series, forward_returns: pd.Series) -> float:
    """计算因子得分与未来收益的 Spearman 秩相关系数.

    Args:
        factor_scores: index=code, values=因子得分
        forward_returns: index=code, values=N日后收益率

    Returns:
        IC 值 [-1, 1]
    """
    common = factor_scores.dropna().index.intersection(forward_returns.dropna().index)
    if len(common) < 10:
        return 0.0
    ic, _ = spearmanr(factor_scores[common], forward_returns[common])
    return ic if not np.isnan(ic) else 0.0


def compute_icir(ic_series: pd.Series) -> float:
    """ICIR = IC均值 / IC标准差."""
    if ic_series.std() == 0:
        return 0.0
    return ic_series.mean() / ic_series.std()


def ic_summary(
    factor_scores_df: pd.DataFrame,
    forward_returns: pd.Series,
) -> pd.DataFrame:
    """对所有因子做 IC 汇总.

    Args:
        factor_scores_df: index=code, columns=F01_score..F41_score
        forward_returns: index=code, N日收益率

    Returns:
        DataFrame columns: factor, ic, icir, positive_ic_rate
    """
    results = []
    for col in factor_scores_df.columns:
        if not col.endswith("_score") and col not in factor_scores_df.columns:
            continue
        ic = compute_ic(factor_scores_df[col], forward_returns)
        results.append({"factor": col, "ic": round(ic, 4)})

    return pd.DataFrame(results).sort_values("ic", ascending=False, key=abs)


def rolling_ic_series(
    factor_scores_dict: dict[str, pd.DataFrame],
    forward_returns_dict: dict[str, pd.Series],
    factor_id: str,
) -> pd.Series:
    """计算单个因子的滚动 IC 时间序列.

    Args:
        factor_scores_dict: {date_str: DataFrame(index=code)}
        forward_returns_dict: {date_str: Series(index=code)}
        factor_id: 因子列名

    Returns:
        Series index=date, values=IC
    """
    common_dates = sorted(set(factor_scores_dict.keys()) & set(forward_returns_dict.keys()))
    ics = {}
    for date in common_dates:
        scores = factor_scores_dict[date]
        returns = forward_returns_dict[date]
        if factor_id in scores.columns:
            ics[date] = compute_ic(scores[factor_id], returns)
    return pd.Series(ics).sort_index()
