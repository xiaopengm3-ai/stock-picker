"""估值数据采集 — PE/PB/PS 及历史分位数.

数据源: stock_zh_a_spot (Sina) 获取实时价格 + stock_yjbb_em 获取 EPS/BVPS
"""
import logging

import akshare as ak
import numpy as np
import pandas as pd

from .fetcher import get_fetcher

log = logging.getLogger(__name__)


def _strip_code_prefix(code: str) -> str:
    """去掉 sh/sz/bj 前缀，保留 6 位纯数字."""
    c = str(code)
    if len(c) > 6 and c[:2].isalpha():
        return c[2:]
    return c.zfill(6)


def fetch_valuation_today() -> pd.DataFrame:
    """获取全市场当日的估值指标.

    合并 Sina 实时价格 + 东方财富批量财报(EPS/BVPS) 计算 PE/PB。

    Returns: DataFrame, index=code, columns: pe, pb, eps, bvps, price,
             revenue_growth, profit_growth, gross_margin
    """
    fetcher = get_fetcher()

    # 1. 获取实时价格 (Sina)
    try:
        price_df = fetcher.fetch(ak.stock_zh_a_spot, ttl_seconds=3600)
        if price_df is None or price_df.empty:
            log.warning("stock_zh_a_spot 返回空")
            return pd.DataFrame()
        price_df["code"] = price_df["代码"].apply(_strip_code_prefix)
        price_df["price"] = pd.to_numeric(price_df["最新价"], errors="coerce")
        price_df = price_df[price_df["price"] > 0]
        price_df = price_df.set_index("code")[["price"]]
        log.info(f"  实时价格: {len(price_df)} 只")
    except Exception as e:
        log.warning(f"实时价格获取失败: {e}")
        return pd.DataFrame()

    # 2. 获取批量财报 (EPS, BVPS, 营收增速, 利润增速, 毛利率)
    try:
        from .bulk_financial import fetch_bulk_earnings
        earnings = fetch_bulk_earnings()
        if not earnings.empty:
            log.info(f"  批量财报: {len(earnings)} 只")
        else:
            log.warning("批量财报为空")
            earnings = pd.DataFrame()
    except Exception as e:
        log.warning(f"批量财报获取失败: {e}")
        earnings = pd.DataFrame()

    # 3. 合并计算 PE/PB
    result = price_df.copy()

    if not earnings.empty:
        result = result.join(earnings, how="left")
        # PE = price / EPS (年化)
        if "eps" in result.columns:
            result["pe"] = result["price"] / result["eps"].replace(0, np.nan)
            result["pe"] = result["pe"].where(result["pe"] > 0, np.nan)
        # PB = price / BVPS
        if "bvps" not in result.columns and "每股净资产" in result.columns:
            result["bvps"] = pd.to_numeric(result["每股净资产"], errors="coerce")
        if "bvps" in result.columns:
            result["pb"] = result["price"] / result["bvps"].replace(0, np.nan)
            result["pb"] = result["pb"].where(result["pb"] > 0, np.nan)

    # 保留需要的列
    keep = [c for c in ["price", "pe", "pb", "ps", "dividend_yield", "eps", "bvps",
                         "revenue_growth", "profit_growth", "gross_margin", "roe",
                         "net_profit", "revenue"] if c in result.columns]
    result = result[keep]

    pe_count = result['pe'].notna().sum() if 'pe' in result.columns else 0
    pb_count = result['pb'].notna().sum() if 'pb' in result.columns else 0
    log.info(f"  估值数据: {len(result)} 只 (PE: {pe_count}, PB: {pb_count})")
    return result


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
