"""资讯情绪因子 F39–F40 (Phase 2)."""
import pandas as pd

from ..registry import FactorMeta, register_factor

F39_NEWS_SENTIMENT = FactorMeta(
    id="F39", name="资讯情绪得分", category="news", sub_category="sentiment",
    direction="positive", standardize_method="zscore",
)
F40_SOCIAL_SENTIMENT = FactorMeta(
    id="F40", name="社区情绪得分", category="news", sub_category="sentiment",
    direction="positive", standardize_method="zscore",
)

NEWS_WEIGHTS = {"F39": 0.70, "F40": 0.30}


def compute_news_sentiment(codes: list[str], stock_names: dict[str, str] | None = None) -> pd.DataFrame:
    """计算消息面因子得分.

    Phase 2: 默认使用占位值。接入 LLM 分析后可计算真实情绪得分。
    """
    if not codes:
        return pd.DataFrame()
    results = pd.DataFrame({
        "F39_score": 50.0,
        "F40_score": 50.0,
    }, index=codes)
    results["news_total"] = (
        results["F39_score"] * NEWS_WEIGHTS["F39"]
        + results["F40_score"] * NEWS_WEIGHTS["F40"]
    )
    return results


for f in [F39_NEWS_SENTIMENT, F40_SOCIAL_SENTIMENT]:
    register_factor(f)
