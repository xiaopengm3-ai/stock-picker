"""市场指数数据采集 — 上证/沪深300/中证500/中证1000."""
import logging

import akshare as ak
import pandas as pd

from .fetcher import get_fetcher

log = logging.getLogger(__name__)

INDEX_CODES = {
    "sh000001": "上证指数",
    "sh000300": "沪深300",
    "sh000905": "中证500",
    "sh000852": "中证1000",
}


def fetch_index_daily(index_code: str = "sh000001", start_date: str = "20200101") -> pd.DataFrame:
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_zh_index_daily, symbol=index_code, ttl_seconds=86400)
        if df is None or df.empty:
            return pd.DataFrame()
        df["date"] = pd.to_datetime(df["date"])
        return df.set_index("date").sort_index()
    except Exception:
        return pd.DataFrame()


def fetch_all_index_daily(start_date: str = "20200101") -> dict[str, pd.DataFrame]:
    result = {}
    for code, name in INDEX_CODES.items():
        df = fetch_index_daily(code, start_date)
        if not df.empty:
            result[name] = df
    return result
