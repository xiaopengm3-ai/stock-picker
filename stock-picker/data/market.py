"""行情数据采集 — 日线/周线/60分钟线."""
import logging
from datetime import datetime

import akshare as ak
import numpy as np
import pandas as pd

from .fetcher import get_fetcher

log = logging.getLogger(__name__)

_COLUMN_MAP = {
    "日期": "date", "开盘": "open", "收盘": "close", "最高": "high",
    "最低": "low", "成交量": "volume", "成交额": "amount",
    "换手率": "turnover_rate", "总市值": "total_market_cap",
    "流通市值": "float_market_cap",
}

REQUIRED_COLS = ["open", "high", "low", "close", "volume"]


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=_COLUMN_MAP)
    keep = [c for c in _COLUMN_MAP.values() if c in df.columns]
    return df[keep]


def fetch_daily_hist(code: str, start_date: str = "20150101", end_date: str | None = None) -> pd.DataFrame:
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    fetcher = get_fetcher()
    df = fetcher.fetch(
        ak.stock_zh_a_hist,
        symbol=code, period="daily", start_date=start_date, end_date=end_date,
        adjust="qfq", ttl_seconds=86400,
    )
    if df is None or df.empty:
        return pd.DataFrame()
    df = _standardize_columns(df)
    df["date"] = pd.to_datetime(df["date"])
    df["code"] = code
    return df.set_index(["code", "date"]).sort_index()


def fetch_all_daily_hist(
    codes: list[str], start_date: str = "20200101", end_date: str | None = None,
) -> pd.DataFrame:
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    all_dfs = []
    failed = 0

    for i, code in enumerate(codes):
        try:
            df = fetch_daily_hist(code, start_date, end_date)
            if not df.empty:
                all_dfs.append(df)
        except Exception as e:
            log.debug(f"{code} 行情获取失败: {e}")
            failed += 1
            continue
        if (i + 1) % 100 == 0:
            log.info(f"行情采集进度: {i + 1}/{len(codes)}")

    log.info(f"行情采集完成: {len(all_dfs)} 成功, {failed} 失败")
    if not all_dfs:
        return pd.DataFrame()
    return pd.concat(all_dfs).sort_index()


def build_weekly_from_daily(daily_df: pd.DataFrame) -> pd.DataFrame:
    df = daily_df.reset_index()
    df["iso_year"] = df["date"].dt.isocalendar().year.astype(str)
    df["iso_week"] = df["date"].dt.isocalendar().week.astype(str).str.zfill(2)
    df["week"] = df["iso_year"] + "-W" + df["iso_week"]

    weekly = df.groupby(["code", "week"], as_index=False).agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"),
        close=("close", "last"), volume=("volume", "sum"), date=("date", "last"),
    )
    weekly["date"] = pd.to_datetime(weekly["date"])
    return weekly.set_index(["code", "date"]).sort_index()


def fetch_daily_hist_batch(
    codes: list[str], start_date: str = "20200101", end_date: str | None = None,
) -> pd.DataFrame:
    """批量获取日线（包装器，与 fetch_all_daily_hist 等价）."""
    return fetch_all_daily_hist(codes, start_date, end_date)
