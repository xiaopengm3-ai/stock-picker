"""动量因子 F24–F27."""
import numpy as np
import pandas as pd

from ..registry import FactorMeta, register_factor

F24_RSI = FactorMeta(
    id="F24", name="RSI位置", category="technical", sub_category="momentum",
    direction="positive", standardize_method="zscore",
)
F25_MACD = FactorMeta(
    id="F25", name="MACD状态", category="technical", sub_category="momentum",
    direction="positive", standardize_method="zscore",
)
F26_RSI_DIVERGENCE = FactorMeta(
    id="F26", name="RSI背离", category="technical", sub_category="momentum",
    direction="positive", standardize_method="zscore",
)
F27_PRICE_MOMENTUM = FactorMeta(
    id="F27", name="价格动量(20日)", category="technical", sub_category="momentum",
    direction="positive", standardize_method="zscore",
)

MOMENTUM_WEIGHTS = {"F24": 0.35, "F25": 0.35, "F26": 0.10, "F27": 0.20}


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-10)
    return 100.0 - 100.0 / (1.0 + rs)


def _macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    hist = dif - dea
    return dif, dea, hist


def compute_momentum_factors(market_df: pd.DataFrame) -> pd.DataFrame:
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
            if len(close) < 30:
                continue

            # F24: RSI(14) 位置
            rsi = _rsi(close)
            rsi_val = rsi.iloc[-1]
            if 50 <= rsi_val <= 65:
                results.loc[code, "F24_score"] = 100.0
            elif 30 <= rsi_val < 50:
                results.loc[code, "F24_score"] = 80.0  # 超卖反弹期
            elif 65 < rsi_val <= 75:
                results.loc[code, "F24_score"] = 50.0
            elif rsi_val > 80:
                results.loc[code, "F24_score"] = 10.0
            else:
                results.loc[code, "F24_score"] = 30.0

            # F25: MACD 状态
            dif, dea, hist = _macd(close)
            macd_ok = dif.iloc[-1] > dea.iloc[-1]
            hist_rising = hist.diff().tail(3).sum() > 0
            if macd_ok and hist_rising:
                results.loc[code, "F25_score"] = 100.0
            elif macd_ok:
                results.loc[code, "F25_score"] = 65.0
            else:
                results.loc[code, "F25_score"] = 20.0

            # F26: RSI 底背离检测（简化版）
            price_low_idx = close.tail(40).idxmin()
            rsi_low_idx = rsi.tail(40).idxmin()
            if price_low_idx != rsi_low_idx:
                if close[price_low_idx] < close.iloc[-20] and rsi[price_low_idx] > rsi.tail(20).min():
                    results.loc[code, "F26_score"] = 80.0  # 底背离
                else:
                    results.loc[code, "F26_score"] = 50.0
            else:
                results.loc[code, "F26_score"] = 50.0

            # F27: 20日价格动量
            ret = close.pct_change(20).iloc[-1] * 100
            # 在行业中上位置最好（不买最热的），满分在 5-15% 涨幅
            if 5 <= ret <= 15:
                results.loc[code, "F27_score"] = 100.0
            elif 0 < ret < 5:
                results.loc[code, "F27_score"] = 60.0
            elif 15 < ret <= 30:
                results.loc[code, "F27_score"] = 40.0
            elif ret <= -10:
                results.loc[code, "F27_score"] = 10.0
            else:
                results.loc[code, "F27_score"] = 20.0

        except Exception:
            continue

    results = results.fillna(50.0)
    results["momentum_total"] = (
        results["F24_score"] * MOMENTUM_WEIGHTS["F24"]
        + results["F25_score"] * MOMENTUM_WEIGHTS["F25"]
        + results["F26_score"] * MOMENTUM_WEIGHTS["F26"]
        + results["F27_score"] * MOMENTUM_WEIGHTS["F27"]
    )
    return results


for f in [F24_RSI, F25_MACD, F26_RSI_DIVERGENCE, F27_PRICE_MOMENTUM]:
    register_factor(f)
