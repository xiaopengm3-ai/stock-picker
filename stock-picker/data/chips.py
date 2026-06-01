"""筹码结构数据采集 — 股东户数 + 机构持仓."""
import logging

import akshare as ak
import pandas as pd

from .fetcher import get_fetcher

log = logging.getLogger(__name__)


def fetch_shareholder_stats() -> pd.DataFrame:
    """获取股东户数及变化."""
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_zh_a_gdhs, symbol="all", ttl_seconds=604800)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


def fetch_institutional_holdings() -> pd.DataFrame:
    """获取机构持仓数据."""
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_institute_hold, ttl_seconds=604800)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()
