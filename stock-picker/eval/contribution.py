"""因子贡献率 + 自动降权/淘汰."""
import logging

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def factor_contribution(
    ic_df: pd.DataFrame,
    weights: dict[str, float],
) -> pd.DataFrame:
    """计算因子贡献率 = 权重 × |IC| / Σ(权重 × |IC|).

    Args:
        ic_df: columns: factor, ic
        weights: {factor_id: weight}

    Returns:
        DataFrame columns: factor, ic, weight, contribution
    """
    df = ic_df.copy()
    df["weight"] = df["factor"].map(weights).fillna(0)
    df["abs_ic"] = df["ic"].abs()
    df["weighted_ic"] = df["weight"] * df["abs_ic"]
    total = df["weighted_ic"].sum()
    df["contribution"] = np.where(total > 0, df["weighted_ic"] / total * 100, 0)
    df["contribution"] = df["contribution"].round(1)

    df["status"] = df["contribution"].apply(_contribution_status)
    return df.sort_values("contribution", ascending=False)


def _contribution_status(contrib: float) -> str:
    if contrib > 10:
        return "★ 核心"
    elif contrib > 5:
        return "✓ 有效"
    elif contrib > 2:
        return "⚠ 降权中"
    else:
        return "✗ 建议淘汰"


def auto_weight_adjust(
    ic_df: pd.DataFrame,
    current_weights: dict[str, float],
    icir_threshold: float = 0.1,
) -> tuple[dict[str, float], list[str]]:
    """基于 IC 表现自动调整因子权重.

    Args:
        ic_df: columns: factor, ic, icir
        current_weights: {factor_id: weight}
        icir_threshold: ICIR 低于此值降权 50%

    Returns:
        (adjusted_weights, deprecation_suggestions)
    """
    adjusted = dict(current_weights)
    suggestions = []

    for _, row in ic_df.iterrows():
        fid = row["factor"]
        icir = row.get("icir", None)
        ic = row.get("ic", 0)

        if fid not in adjusted:
            continue

        if icir is not None and icir < icir_threshold:
            old = adjusted[fid]
            adjusted[fid] = old * 0.5
            suggestions.append(f"{fid}: ICIR={icir:.2f} < {icir_threshold}, 降权 {old:.2f} → {adjusted[fid]:.2f}")

        if abs(ic) < 0.01:
            suggestions.append(f"{fid}: IC≈0 ({ic:.4f}), 建议淘汰")

    # 归一化
    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: v / total for k, v in adjusted.items()}

    return adjusted, suggestions
