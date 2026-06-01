"""行业数据采集 — 申万行业分类 + 行业指数行情."""
import logging

import akshare as ak
import pandas as pd

from .fetcher import get_fetcher

log = logging.getLogger(__name__)


def fetch_industry_classification() -> pd.DataFrame:
    """获取申万行业分类.

    Returns: DataFrame, 包含 code + industry_sw1 + industry_sw2
    """
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_board_industry_name_em, ttl_seconds=2592000)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


def fetch_industry_index_daily() -> pd.DataFrame:
    """获取申万一级行业指数日线行情."""
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_board_industry_index_em, ttl_seconds=86400)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()
