"""资金流向数据采集 — 北向资金 + 主力资金."""
import logging

import akshare as ak
import pandas as pd

from .fetcher import get_fetcher

log = logging.getLogger(__name__)


def fetch_north_bound_flow() -> pd.DataFrame:
    """获取北向资金持股及净买入."""
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_hsgt_hold_em, symbol="沪股通", ttl_seconds=86400)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


def fetch_main_force_flow(market: str = "sh") -> pd.DataFrame:
    """获取主力资金流向（超大单/大单/中单/小单）."""
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(
            ak.stock_individual_fund_flow, stock="all", market=market, ttl_seconds=86400,
        )
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()
