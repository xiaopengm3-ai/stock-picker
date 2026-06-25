"""批量财务数据采集 — 使用东方财富批量接口，一次调用获取全市场数据.

用于替代逐股调用的方式，大幅提升数据获取速度。
"""
import logging
from datetime import datetime

import pandas as pd

from .fetcher import get_fetcher

log = logging.getLogger(__name__)


def _latest_report_date() -> str:
    """返回最近一个季末报告期 YYYYMMDD."""
    now = datetime.now()
    year = now.year
    # 最近已披露的报告期（滞后1-2个月）
    quarters = [
        (f"{year}0331", (4, 30)),   # Q1 4月底前披露
        (f"{year}0630", (8, 31)),   # Q2 8月底前披露
        (f"{year}0930", (10, 31)),  # Q3 10月底前披露
        (f"{year}1231", (4, 30)),   # 年报次年4月底前披露
    ]
    for date_str, (end_month, end_day) in reversed(quarters):
        dt = datetime.strptime(date_str, "%Y%m%d")
        deadline = datetime(year if end_month >= dt.month else year + 1, end_month, end_day)
        if now >= deadline:
            return date_str
    # 回退到上年年报
    return f"{year - 1}1231"


def fetch_bulk_earnings(report_date: str | None = None) -> pd.DataFrame:
    """批量获取业绩报表 — ROE/营收增速/利润增速/毛利率/EPS.

    Returns:
        DataFrame index=code, columns: roe, revenue_growth, profit_growth,
        gross_margin, eps, net_profit, revenue
    """
    fetcher = get_fetcher()
    date = report_date or _latest_report_date()
    try:
        df = fetcher.fetch(
            __import__("akshare").stock_yjbb_em,
            date=date, ttl_seconds=86400 * 3,
        )
        if df is None or df.empty:
            log.warning(f"stock_yjbb_em({date}) 返回空")
            return pd.DataFrame()

        col_map = {
            "股票代码": "code",
            "净资产收益率": "roe",
            "营业总收入-同比增长": "revenue_growth",
            "净利润-同比增长": "profit_growth",
            "销售毛利率": "gross_margin",
            "每股收益": "eps",
            "净利润-净利润": "net_profit",
            "营业总收入-营业总收入": "revenue",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        if "code" not in df.columns:
            return pd.DataFrame()
        df["code"] = df["code"].astype(str).str.zfill(6)
        df = df.set_index("code")
        keep = [c for c in ["roe", "revenue_growth", "profit_growth", "gross_margin",
                             "eps", "net_profit", "revenue"] if c in df.columns]
        return df[keep].apply(pd.to_numeric, errors="coerce")
    except Exception as e:
        log.warning(f"批量业绩报表获取失败: {e}")
        return pd.DataFrame()


def fetch_bulk_balance_sheet(report_date: str | None = None) -> pd.DataFrame:
    """批量获取资产负债表 — 资产/负债/权益/资产负债率.

    Returns:
        DataFrame index=code, columns: total_assets, total_liabilities,
        debt_ratio, net_equity, advance_receipts
    """
    fetcher = get_fetcher()
    date = report_date or _latest_report_date()
    try:
        df = fetcher.fetch(
            __import__("akshare").stock_zcfz_em,
            date=date, ttl_seconds=86400 * 3,
        )
        if df is None or df.empty:
            log.warning(f"stock_zcfz_em({date}) 返回空")
            return pd.DataFrame()

        col_map = {
            "股票代码": "code",
            "资产-总资产": "total_assets",
            "负债-总负债": "total_liabilities",
            "资产负债率": "debt_ratio",
            "股东权益合计": "net_equity",
            "负债-预收账款": "advance_receipts",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        if "code" not in df.columns:
            return pd.DataFrame()
        df["code"] = df["code"].astype(str).str.zfill(6)
        df = df.set_index("code")
        keep = [c for c in ["total_assets", "total_liabilities", "debt_ratio",
                             "net_equity", "advance_receipts"] if c in df.columns]
        return df[keep].apply(pd.to_numeric, errors="coerce")
    except Exception as e:
        log.warning(f"批量资产负债表获取失败: {e}")
        return pd.DataFrame()


def fetch_bulk_cashflow(report_date: str | None = None) -> pd.DataFrame:
    """批量获取现金流量表 — 经营/投资/筹资现金流.

    Returns:
        DataFrame index=code, columns: operating_cf, investing_cf, financing_cf
    """
    fetcher = get_fetcher()
    date = report_date or _latest_report_date()
    try:
        df = fetcher.fetch(
            __import__("akshare").stock_xjll_em,
            date=date, ttl_seconds=86400 * 3,
        )
        if df is None or df.empty:
            log.warning(f"stock_xjll_em({date}) 返回空")
            return pd.DataFrame()

        col_map = {
            "股票代码": "code",
            "经营性现金流-现金流量净额": "operating_cf",
            "投资性现金流-现金流量净额": "investing_cf",
            "融资性现金流-现金流量净额": "financing_cf",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        if "code" not in df.columns:
            return pd.DataFrame()
        df["code"] = df["code"].astype(str).str.zfill(6)
        df = df.set_index("code")
        keep = [c for c in ["operating_cf", "investing_cf", "financing_cf"] if c in df.columns]
        return df[keep].apply(pd.to_numeric, errors="coerce")
    except Exception as e:
        log.warning(f"批量现金流量表获取失败: {e}")
        return pd.DataFrame()


def fetch_all_bulk_financials(
    report_date: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """一次性获取全市场财务数据，返回 (indicators_df, financial_df).

    indicators_df: index=code, columns: roe, gross_margin, revenue_growth,
                   profit_growth, debt_ratio, net_equity, operating_cf, advance_receipts
    financial_df:  MultiIndex (code, report_date), columns: revenue, net_profit,
                   operating_cf, debt_ratio, net_equity, advance_receipts

    financial_df 为兼容 growth/quality/forward 因子函数的 MultiIndex 格式。
    """
    date = report_date or _latest_report_date()
    log.info(f"  批量获取财务数据 (报告期: {date})...")

    earnings = fetch_bulk_earnings(date)
    balance = fetch_bulk_balance_sheet(date)
    cashflow = fetch_bulk_cashflow(date)

    # --- indicators_df: 单期宽表 ---
    parts = [df for df in [earnings, balance, cashflow] if not df.empty]
    if not parts:
        return pd.DataFrame(), pd.DataFrame()

    indicators = parts[0]
    for p in parts[1:]:
        dup_cols = indicators.columns.intersection(p.columns)
        p = p.drop(columns=dup_cols, errors="ignore")
        indicators = indicators.join(p, how="outer")

    log.info(f"  财务指标: {len(indicators)} 只")

    # --- financial_df: MultiIndex 格式，兼容因子函数 ---
    # 用单期数据构造 MultiIndex (code, report_date)
    rows = []
    for code in indicators.index:
        row = {"code": code, "report_date": pd.Timestamp(date)}
        for col in indicators.columns:
            row[col] = indicators.loc[code, col]
        rows.append(row)

    if not rows:
        return indicators, pd.DataFrame()

    financial = pd.DataFrame(rows)
    financial = financial.set_index(["code", "report_date"]).sort_index()

    return indicators, financial
