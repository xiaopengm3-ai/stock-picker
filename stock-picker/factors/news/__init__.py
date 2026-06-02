"""消息面因子模块."""
import pandas as pd
from .sentiment import compute_news_sentiment


def compute_news_scores(codes: list[str], stock_names: dict[str, str] | None = None) -> pd.DataFrame:
    return compute_news_sentiment(codes, stock_names)
