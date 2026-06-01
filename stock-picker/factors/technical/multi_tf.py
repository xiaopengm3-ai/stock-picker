"""多周期因子 F32 (Phase 1: 日线级别模拟)."""
import numpy as np
import pandas as pd

from ..registry import FactorMeta, register_factor

F32_MULTI_TF = FactorMeta(
    id="F32", name="多周期一致性", category="technical", sub_category="multi_tf",
    direction="positive", standardize_method="zscore",
)


def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def compute_multi_tf_factors(market_df: pd.DataFrame, weekly_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """计算多周期一致性得分.

    Phase 1: 基于日线 EMA 对齐判断方向一致性。
    Phase 2 将接入真实周线和60分钟数据。
    """
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
            if len(close) < 120:
                continue

            ema20 = _ema(close, 20)
            ema50 = _ema(close, 50)
            ema120 = _ema(close, 120)

            # 模拟三周期方向
            daily_bull = ema20.iloc[-1] > ema50.iloc[-1]
            mid_bull = ema50.iloc[-1] > ema120.iloc[-1]  # 模拟周线方向
            short_bull = close.iloc[-1] > ema20.iloc[-1]  # 模拟60m方向

            bullish_count = sum([daily_bull, mid_bull, short_bull])

            if bullish_count == 3:
                results.loc[code, "F32_score"] = 100.0
            elif bullish_count == 2:
                results.loc[code, "F32_score"] = 65.0
            elif bullish_count == 1:
                results.loc[code, "F32_score"] = 35.0
            else:
                results.loc[code, "F32_score"] = 10.0

            # 周线看空强制：EMA50 < EMA120 且还在下跌
            if ema50.iloc[-1] < ema120.iloc[-1] and ema50.diff().tail(10).mean() < 0:
                results.loc[code, "F32_score"] = 0.0  # 大周期铁律：周线看空→技术面归零

        except Exception:
            continue

    results = results.fillna(50.0)
    results["multi_tf_total"] = results["F32_score"]
    return results


register_factor(F32_MULTI_TF)
