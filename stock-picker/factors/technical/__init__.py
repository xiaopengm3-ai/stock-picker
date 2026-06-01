"""技术面因子模块 — 汇总趋势+动量+量价+形态+多周期."""
import pandas as pd

from .trend import compute_trend_factors, TREND_WEIGHTS
from .momentum import compute_momentum_factors, MOMENTUM_WEIGHTS
from .volume import compute_volume_factors, VOLUME_WEIGHTS
from .pattern import compute_pattern_factors
from .multi_tf import compute_multi_tf_factors

TECHNICAL_SUB_WEIGHTS = {
    "trend": 0.35,
    "momentum": 0.25,
    "volume": 0.20,
    "pattern": 0.10,
    "multi_tf": 0.10,
}


def compute_technical_scores(
    market_df: pd.DataFrame,
    weekly_df: pd.DataFrame | None = None,
    sub_weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """计算技术面所有因子得分并加权汇总.

    Args:
        market_df: MultiIndex (code, date), 含 OHLCV 列
        weekly_df: 周线数据（Phase 1 可选）
        sub_weights: 子维度权重覆写

    Returns:
        DataFrame index=code, columns: F21_score..F32_score, trend/momentum/volume/pattern/multi_tf/technical_total
    """
    w = sub_weights or TECHNICAL_SUB_WEIGHTS

    # 计算各子维度
    trend_df = compute_trend_factors(market_df)
    momentum_df = compute_momentum_factors(market_df)
    volume_df = compute_volume_factors(market_df)
    pattern_df = compute_pattern_factors(market_df)
    multi_df = compute_multi_tf_factors(market_df, weekly_df)

    # 对齐 code
    all_dfs = [trend_df, momentum_df, volume_df, pattern_df, multi_df]
    all_codes = sorted(set().union(*[d.index for d in all_dfs if not d.empty]))
    if not all_codes:
        return pd.DataFrame()

    result = pd.DataFrame(index=all_codes)

    # 合并各子维度得分
    for prefix, df in [("", trend_df), ("", momentum_df), ("", volume_df), ("", pattern_df), ("", multi_df)]:
        for col in df.columns:
            if col not in result.columns and col != "technical_total":
                result[col] = df[col].reindex(all_codes)

    # 提取子维度总分
    result["trend_total"] = trend_df["trend_total"].reindex(all_codes).fillna(40.0) if "trend_total" in trend_df.columns else 40.0
    result["momentum_total"] = momentum_df["momentum_total"].reindex(all_codes).fillna(40.0) if "momentum_total" in momentum_df.columns else 40.0
    result["volume_total"] = volume_df["volume_total"].reindex(all_codes).fillna(40.0) if "volume_total" in volume_df.columns else 40.0
    result["pattern_total"] = pattern_df["pattern_total"].reindex(all_codes).fillna(50.0) if "pattern_total" in pattern_df.columns else 50.0
    result["multi_tf_total"] = multi_df["multi_tf_total"].reindex(all_codes).fillna(50.0) if "multi_tf_total" in multi_df.columns else 50.0

    # 多周期铁律：multi_tf_total == 0 → 技术面总分 = 0
    # 共振加成：趋势+动量+量价都好 → bonus
    bonus = pd.Series(0.0, index=all_codes)
    for code in all_codes:
        t = result.loc[code, "trend_total"]
        m = result.loc[code, "momentum_total"]
        v = result.loc[code, "volume_total"]
        p = result.loc[code, "pattern_total"]
        mt = result.loc[code, "multi_tf_total"]

        if t >= 60 and m >= 60 and v >= 60:
            bonus[code] = 0.20
        elif t >= 60 and m >= 60:
            bonus[code] = 0.10
        elif t >= 60 and v >= 60:
            bonus[code] = 0.10
        if p >= 70 and mt >= 70:
            bonus[code] += 0.15

    base = (
        result["trend_total"] * w["trend"]
        + result["momentum_total"] * w["momentum"]
        + result["volume_total"] * w["volume"]
        + result["pattern_total"] * w["pattern"]
        + result["multi_tf_total"] * w["multi_tf"]
    )

    result["technical_total"] = (base * (1.0 + bonus)).clip(upper=100.0)

    # 周线看空 → 技术面总分 = 0
    zero_mask = result["multi_tf_total"] == 0
    result.loc[zero_mask, "technical_total"] = 0.0

    return result
