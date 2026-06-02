"""市场状态识别 — 牛/熊/震荡判断 + 市场温度."""
from dataclasses import dataclass

import numpy as np
import pandas as pd

INDEX_NAMES = ["上证指数", "沪深300", "中证500", "中证1000"]


@dataclass
class MarketState:
    temperature: float        # 0-100 市场温度
    regime: str               # "牛市"/"震荡偏多"/"震荡偏空"/"熊市"
    suggested_position: float # 0.0-1.0 建议仓位
    details: dict             # 各指数详情


def detect_market_state(index_data: dict[str, pd.DataFrame]) -> MarketState:
    """根据四大指数判断市场状态.

    Args:
        index_data: {指数名称: DataFrame(index=date, columns=close/open/high/low)}

    Returns:
        MarketState 对象
    """
    if not index_data:
        return MarketState(
            temperature=50.0, regime="震荡偏多",
            suggested_position=0.60, details={},
        )

    scores = []
    details = {}

    for name in INDEX_NAMES:
        df = index_data.get(name)
        if df is None or df.empty or "close" not in df.columns:
            details[name] = {"score": 50.0, "trend": "N/A"}
            scores.append(50.0)
            continue

        close = df["close"].dropna()
        if len(close) < 120:
            details[name] = {"score": 50.0, "trend": "N/A"}
            scores.append(50.0)
            continue

        ema60 = close.ewm(span=60, adjust=False).mean()
        ema200 = close.ewm(span=200, adjust=False).mean()

        # 均线位置得分（价格在均线上方 = 多头）
        above_ema60 = close.iloc[-1] > ema60.iloc[-1]
        above_ema200 = close.iloc[-1] > ema200.iloc[-1]

        # 均线方向得分
        ema60_slope = ema60.diff().tail(20).sum() / (abs(close.iloc[-20]) + 1e-10)  # 归一化斜率
        ema60_up = ema60_slope > 0.001

        # 动量得分
        ret60 = (close.iloc[-1] / close.iloc[-min(60, len(close))] - 1) * 100

        # 综合评分
        pos_score = 50.0
        if above_ema60:
            pos_score += 15.0
        if above_ema200:
            pos_score += 10.0
        if ema60_up:
            pos_score += 15.0
        if ret60 > 5:
            pos_score += 10.0
        elif ret60 < -5:
            pos_score -= 10.0

        score = max(0.0, min(100.0, pos_score))
        scores.append(score)

        trend = "多头" if score >= 55 else ("空头" if score <= 45 else "震荡")
        details[name] = {
            "score": round(score, 1),
            "trend": trend,
            "close": round(close.iloc[-1], 2),
            "above_ema60": above_ema60,
            "above_ema200": above_ema200,
            "ret_60d": f"{ret60:.1f}%",
        }

    # 四大指数加权平均
    weights = [0.30, 0.30, 0.20, 0.20]  # 上证+沪深300各30%, 中证500+中证1000各20%
    temperature = sum(s * w for s, w in zip(scores, weights))

    # 判定 regime
    if temperature >= 75:
        regime = "牛市"
        position = 0.85
    elif temperature >= 50:
        regime = "震荡偏多"
        position = 0.60
    elif temperature >= 25:
        regime = "震荡偏空"
        position = 0.40
    else:
        regime = "熊市"
        position = 0.20

    return MarketState(
        temperature=round(temperature, 1),
        regime=regime,
        suggested_position=position,
        details=details,
    )
