"""估值数据采集 — PE/PB/PS 及历史分位数."""
import logging

import akshare as ak
import pandas as pd

from .fetcher import get_fetcher

log = logging.getLogger(__name__)


def fetch_valuation_today() -> pd.DataFrame:
    """获取全市场当日的估值指标.

    Returns: DataFrame, index=code, columns: pe, pb, ps, pcf, dividend_yield, total_market_cap, float_market_cap
    """
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_a_lg_indicator, symbol="all", ttl_seconds=86400)
        if df is None or df.empty:
            return pd.DataFrame()

        col_map = {
            "code": "code", "pe": "pe", "pb": "pb", "ps": "ps", "pcf": "pcf",
            "股息率": "dividend_yield", "总市值": "total_market_cap",
            "流通市值": "float_market_cap",
        }
        existing = {k: v for k, v in col_map.items() if k in df.columns}
        df = df.rename(columns=existing)
        keep = [v for v in col_map.values() if v in df.columns]
        if "code" not in df.columns:
            return pd.DataFrame()
        df["code"] = df["code"].astype(str).str.zfill(6)
        return df.set_index("code")[[c for c in keep if c != "code"]]
    except Exception as e:
        log.warning(f"全市场估值获取失败: {e}")
        return pd.DataFrame()


def fetch_valuation_history(code: str, days: int = 1260) -> pd.DataFrame:
    """获取单只股票历史估值数据（用于分位数计算）."""
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_zh_valuation_baidu, symbol=code, ttl_seconds=86400)
        if df is None or df.empty:
            return pd.DataFrame()
        df["code"] = code
        df["date"] = pd.to_datetime(df["date"])
        return df.set_index(["code", "date"]).sort_index()
    except Exception:
        return pd.DataFrame()
