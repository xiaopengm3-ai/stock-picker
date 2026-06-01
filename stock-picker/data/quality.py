"""数据质量检查 — 停牌检测、缺失值统计、异常值标记."""
import logging
from datetime import datetime, timedelta

import pandas as pd

log = logging.getLogger(__name__)

CRITICAL_SOURCES = ["market", "financial", "valuation"]


def check_missing_sources(
    market_available: bool, financial_available: bool, valuation_available: bool,
) -> dict:
    status = {"market": market_available, "financial": financial_available, "valuation": valuation_available}
    missing = [k for k, v in status.items() if not v]
    passed = len(missing) <= 1
    warning = ""
    if missing:
        warning = f"关键数据源缺失: {', '.join(missing)}"
        if not passed:
            warning += " — 超过容忍上限，选股结果不可靠"
    return {"passed": passed, "missing": missing, "warning": warning}


def filter_suspended(codes: list[str], market_df: pd.DataFrame, date: str) -> list[str]:
    cutoff = pd.to_datetime(date) - timedelta(days=7)
    idx = market_df.index.get_level_values("date") if "date" in market_df.index.names else market_df.index
    active_codes = set()
    if "code" in market_df.index.names and "date" in market_df.index.names:
        recent = market_df.loc[(slice(None), market_df.index.get_level_values("date") >= cutoff), :]
        active_codes = set(recent[recent["volume"] > 0].index.get_level_values("code").unique())
    return [c for c in codes if c in active_codes]


def filter_new_listings(
    codes_with_dates: dict[str, str], date: str, min_days: int = 180,
) -> list[str]:
    target = pd.to_datetime(date)
    return [
        code for code, list_date in codes_with_dates.items()
        if (target - pd.to_datetime(list_date)).days >= min_days
    ]


def validate_market_data(df: pd.DataFrame) -> dict:
    issues = []
    if df.empty:
        return {"passed": False, "issues": ["行情数据为空"]}
    required_cols = ["open", "high", "low", "close", "volume"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        issues.append(f"缺少列: {missing}")
    if "close" in df.columns and (df["close"] <= 0).any():
        issues.append("存在非正收盘价")
    if "high" in df.columns and "low" in df.columns:
        invalid = (df["high"] < df["low"]).sum()
        if invalid > 0:
            issues.append(f"{invalid} 条记录 high < low")
    return {"passed": len(issues) == 0, "issues": issues}
