"""因子权重动态调节 — 基于市场环境."""
from .market_state import MarketState

# 震荡市默认权重（基准）
DEFAULT_WEIGHTS = {
    "fundamental": 0.35,
    "technical": 0.25,
    "capital_flow": 0.10,
    "industry": 0.10,
    "news": 0.10,
    "catalyst": 0.05,
    "market_regime": 0.05,
}


def adjust_weights_for_regime(
    state: MarketState,
    base_weights: dict[str, float] | None = None,
) -> dict[str, float]:
    """根据市场环境调节因子权重.

    牛市：技术面 +5%，利用趋势惯性
    熊市：技术面归零，权重分配给基本面+消息面+催化剂
    震荡：默认权重

    Returns:
        调整后的权重字典，总和 = 100%
    """
    w = (base_weights or DEFAULT_WEIGHTS).copy()

    if state.regime == "牛市" and state.temperature >= 75:
        # 技术面 +5%，基本面 -5%
        w["technical"] = min(0.35, w.get("technical", 0.25) + 0.05)
        w["fundamental"] = max(0.25, w.get("fundamental", 0.35) - 0.05)

    elif state.regime == "熊市" and state.temperature < 25:
        # 技术面归零，分配给其他维度
        tech_weight = w.get("technical", 0.25)
        w["technical"] = 0.0
        w["fundamental"] = w.get("fundamental", 0.35) + tech_weight * 0.4
        w["news"] = w.get("news", 0.10) + tech_weight * 0.2
        w["catalyst"] = w.get("catalyst", 0.05) + tech_weight * 0.2
        w["capital_flow"] = w.get("capital_flow", 0.10) + tech_weight * 0.2

    # 归一化确保总和 = 1.0 — 只处理数字值，过滤子字典
    numeric_weights = {k: v for k, v in w.items() if isinstance(v, (int, float))}
    total = sum(numeric_weights.values())
    if total > 0 and abs(total - 1.0) > 0.01:
        factor = 1.0 / total
        for k in numeric_weights:
            w[k] = numeric_weights[k] * factor

    return w
