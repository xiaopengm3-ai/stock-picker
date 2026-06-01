"""趋势因子 F21–F23."""
import numpy as np
import pandas as pd

from ..registry import FactorMeta, register_factor

F21_EMA_CROSS = FactorMeta(
    id="F21", name="EMA20/50金叉", category="technical", sub_category="trend",
    direction="positive", standardize_method="zscore",
)
F22_ADX_STRENGTH = FactorMeta(
    id="F22", name="ADX趋势强度", category="technical", sub_category="trend",
    direction="positive", standardize_method="zscore",
)
F23_MA_ALIGNMENT = FactorMeta(
    id="F23", name="均线多头排列", category="technical", sub_category="trend",
    direction="positive", standardize_method="zscore",
)

TREND_WEIGHTS = {"F21": 0.35, "F22": 0.30, "F23": 0.35}


def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """简化 ADX 计算."""
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs(),
    ], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1.0 / period, adjust=False).mean()

    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=high.index)
    minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=high.index)

    plus_di = 100.0 * plus_dm.ewm(alpha=1.0 / period, adjust=False).mean() / (atr + 1e-10)
    minus_di = 100.0 * minus_dm.ewm(alpha=1.0 / period, adjust=False).mean() / (atr + 1e-10)

    dx = 100.0 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
    return dx.ewm(alpha=1.0 / period, adjust=False).mean()


def compute_trend_factors(market_df: pd.DataFrame) -> pd.DataFrame:
    """计算三只趋势因子得分.

    Args:
        market_df: MultiIndex (code, date), 含 close 列
    Returns:
        DataFrame index=code, columns: F21_score, F22_score, F23_score, trend_total
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
            if len(close) < 60:
                continue

            ema20 = _ema(close, 20)
            ema50 = _ema(close, 50)
            ema200 = _ema(close, 200)

            # F21: EMA20 > EMA50 且 EMA20 方向向上
            cross_good = (ema20.iloc[-1] > ema50.iloc[-1]) and (ema20.diff().tail(5).sum() > 0)
            results.loc[code, "F21_score"] = 100.0 if cross_good else 30.0

            # F22: ADX 强度
            if "high" in data.columns and "low" in data.columns:
                adx = _adx(data["high"], data["low"], close)
                adx_val = adx.iloc[-1]
                results.loc[code, "F22_score"] = max(0.0, min(100.0, adx_val * 2.0))
            else:
                results.loc[code, "F22_score"] = 50.0

            # F23: 均线多头排列 EMA20 > EMA50 > EMA200
            aligned = ema20.iloc[-1] > ema50.iloc[-1] > ema200.iloc[-1]
            results.loc[code, "F23_score"] = 100.0 if aligned else (
                60.0 if ema20.iloc[-1] > ema50.iloc[-1] else 20.0
            )
        except Exception:
            continue

    results = results.fillna(40.0)
    results["trend_total"] = (
        results["F21_score"] * TREND_WEIGHTS["F21"]
        + results["F22_score"] * TREND_WEIGHTS["F22"]
        + results["F23_score"] * TREND_WEIGHTS["F23"]
    )
    return results


for f in [F21_EMA_CROSS, F22_ADX_STRENGTH, F23_MA_ALIGNMENT]:
    register_factor(f)
