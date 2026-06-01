"""量价因子 F28–F30."""
import numpy as np
import pandas as pd

from ..registry import FactorMeta, register_factor

F28_VOLUME_BREAKOUT = FactorMeta(
    id="F28", name="放量上涨", category="technical", sub_category="volume",
    direction="positive", standardize_method="zscore",
)
F29_OBV_TREND = FactorMeta(
    id="F29", name="OBV趋势", category="technical", sub_category="volume",
    direction="positive", standardize_method="zscore",
)
F30_TURNOVER_HEALTH = FactorMeta(
    id="F30", name="换手率健康度", category="technical", sub_category="volume",
    direction="neutral", standardize_method="zscore",
)

VOLUME_WEIGHTS = {"F28": 0.45, "F29": 0.30, "F30": 0.25}


def _obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff())
    direction.iloc[0] = 1
    return (direction * volume).cumsum()


def compute_volume_factors(market_df: pd.DataFrame) -> pd.DataFrame:
    if market_df.empty or "close" not in market_df.columns or "volume" not in market_df.columns:
        return pd.DataFrame()

    codes = market_df.index.get_level_values("code").unique()
    results = pd.DataFrame(index=codes)

    for code in codes:
        try:
            data = market_df.loc[code]
            if isinstance(data, pd.Series):
                continue
            close = data["close"].dropna()
            volume = data["volume"].dropna()
            if len(close) < 25:
                continue

            # F28: 放量上涨
            avg_vol_20 = volume.tail(21).head(20).mean()
            last_vol = volume.iloc[-1]
            last_ret = close.pct_change().iloc[-1]
            vol_ratio = last_vol / (avg_vol_20 + 1e-10)

            if last_ret > 0 and 1.5 <= vol_ratio <= 3.0:
                results.loc[code, "F28_score"] = 100.0
            elif last_ret > 0 and 1.2 <= vol_ratio < 1.5:
                results.loc[code, "F28_score"] = 70.0
            elif last_ret > 0 and vol_ratio > 3.0:
                results.loc[code, "F28_score"] = 30.0  # 异常爆量
            elif vol_ratio < 0.5:
                results.loc[code, "F28_score"] = 20.0
            else:
                results.loc[code, "F28_score"] = 50.0

            # F29: OBV 趋势
            obv = _obv(close, volume)
            obv_ema20 = obv.ewm(span=20, adjust=False).mean()
            obv_ok = obv.iloc[-1] > obv_ema20.iloc[-1] and obv.diff().tail(5).sum() > 0
            if obv_ok:
                results.loc[code, "F29_score"] = 100.0
            elif obv.iloc[-1] > obv_ema20.iloc[-1]:
                results.loc[code, "F29_score"] = 60.0
            else:
                results.loc[code, "F29_score"] = 20.0

            # F30: 换手率健康度
            if "turnover_rate" in data.columns:
                to = data["turnover_rate"].dropna()
                if len(to) > 0:
                    to_val = to.iloc[-1]
                    if 2 <= to_val <= 8:
                        results.loc[code, "F30_score"] = 100.0
                    elif 0.5 <= to_val < 2 or 8 < to_val <= 15:
                        results.loc[code, "F30_score"] = 60.0
                    elif to_val > 20:
                        results.loc[code, "F30_score"] = 10.0
                    else:
                        results.loc[code, "F30_score"] = 30.0
                else:
                    results.loc[code, "F30_score"] = 50.0
            else:
                results.loc[code, "F30_score"] = 50.0

        except Exception:
            continue

    results = results.fillna(50.0)
    results["volume_total"] = (
        results["F28_score"] * VOLUME_WEIGHTS["F28"]
        + results["F29_score"] * VOLUME_WEIGHTS["F29"]
        + results["F30_score"] * VOLUME_WEIGHTS["F30"]
    )
    return results


for f in [F28_VOLUME_BREAKOUT, F29_OBV_TREND, F30_TURNOVER_HEALTH]:
    register_factor(f)
