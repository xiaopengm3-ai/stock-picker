"""形态因子 F31 (Phase 1: 简化规则引擎)."""
import numpy as np
import pandas as pd

from ..registry import FactorMeta, register_factor

F31_PATTERN = FactorMeta(
    id="F31", name="看涨形态", category="technical", sub_category="pattern",
    direction="positive", standardize_method="zscore",
)


def _detect_w_bottom(close: pd.Series, days: int = 60) -> bool:
    """检测 W 底形态."""
    c = close.tail(days).values
    if len(c) < 40:
        return False
    # 简化：找两个低点和一个中间高点
    mid = len(c) // 2
    left_min = c[:mid].min()
    right_min = c[mid:].min()
    mid_high = c[mid - 5:mid + 5].max()
    # 两个低点接近 + 中间高点明显
    return (abs(left_min - right_min) / (abs(left_min) + 1e-10) < 0.08
            and mid_high > min(left_min, right_min) * 1.05
            and c[-1] > mid_high * 0.97)


def _detect_flag_breakout(close: pd.Series, volume: pd.Series | None = None) -> bool:
    """检测旗形突破（简化版）."""
    c = close.tail(40).values
    if len(c) < 30:
        return False
    # 前 1/3 急涨，后 2/3 整理
    pole = (c[len(c) // 3] - c[0]) / (abs(c[0]) + 1e-10)
    flag_range = (c[-10:].max() - c[-10:].min()) / (abs(c[-10:].mean()) + 1e-10)
    return pole > 0.08 and flag_range < 0.05 and c[-1] > c[-10:].mean()


def _detect_consolidation_breakout(close: pd.Series, volume: pd.Series | None = None) -> bool:
    """检测底部盘整突破: ≥30天窄幅震荡 + 放量突破."""
    c = close.tail(40).values
    if len(c) < 35:
        return False
    consolidation = c[:-5]
    amp = (consolidation.max() - consolidation.min()) / (abs(consolidation.mean()) + 1e-10)
    breakout = c[-1] > consolidation.max() * 1.01
    return amp < 0.15 and breakout


def compute_pattern_factors(market_df: pd.DataFrame) -> pd.DataFrame:
    if market_df.empty or "close" not in market_df.columns:
        return pd.DataFrame()

    codes = market_df.index.get_level_values("code").unique()
    results = pd.DataFrame(index=codes)

    for code in codes:
        try:
            data = market_df.loc[code]
            if isinstance(data, pd.Series):
                continue
            close = data["close"].dropna()
            volume = data["volume"].dropna() if "volume" in data.columns else None
            if len(close) < 50:
                continue

            bullish_count = 0
            if _detect_w_bottom(close):
                bullish_count += 1
            if _detect_flag_breakout(close, volume):
                bullish_count += 1
            if _detect_consolidation_breakout(close, volume):
                bullish_count += 1

            scores_map = {0: 40.0, 1: 70.0, 2: 85.0, 3: 100.0}
            results.loc[code, "F31_score"] = scores_map.get(bullish_count, 40.0)

        except Exception:
            continue

    results = results.fillna(50.0)
    results["pattern_total"] = results["F31_score"]
    return results


register_factor(F31_PATTERN)
