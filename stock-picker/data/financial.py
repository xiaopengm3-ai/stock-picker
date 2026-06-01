"""财务数据采集 — 三表 + 财务指标."""
import logging

import akshare as ak
import pandas as pd

from .fetcher import get_fetcher

log = logging.getLogger(__name__)


def fetch_financial_indicators(code: str) -> pd.DataFrame:
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_financial_abstract, symbol=code, ttl_seconds=604800)
        if df is None or df.empty:
            return pd.DataFrame()
        col_map = {
            "报告期": "report_date", "净资产收益率": "roe",
            "总资产报酬率": "roa", "毛利率": "gross_margin",
            "净利率": "net_margin", "资产负债率": "debt_ratio",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        keep = [v for v in col_map.values() if v in df.columns]
        if not keep:
            return pd.DataFrame()
        df["code"] = code
        df["report_date"] = pd.to_datetime(df["report_date"])
        return df[["code", "report_date"] + keep].set_index(["code", "report_date"]).sort_index()
    except Exception as e:
        log.debug(f"{code} 财务指标获取失败: {e}")
        return pd.DataFrame()


def fetch_balance_sheet(code: str) -> pd.DataFrame:
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_balance_sheet_by_report_em, symbol=code, ttl_seconds=604800)
        if df is None or df.empty:
            return pd.DataFrame()
        col_map = {
            "报告期": "report_date", "商誉": "goodwill",
            "预收款项": "advance_receipts", "合同负债": "contract_liabilities",
            "存货": "inventory", "应收账款": "accounts_receivable",
            "资产总计": "total_assets", "负债合计": "total_liabilities",
            "归属于母公司股东权益合计": "net_equity",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        keep = [v for v in col_map.values() if v in df.columns]
        if not keep:
            return pd.DataFrame()
        df["code"] = code
        df["report_date"] = pd.to_datetime(df["report_date"])
        return df[["code", "report_date"] + keep].set_index(["code", "report_date"]).sort_index()
    except Exception as e:
        log.debug(f"{code} 资产负债表获取失败: {e}")
        return pd.DataFrame()


def fetch_cashflow_statement(code: str) -> pd.DataFrame:
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_cash_flow_sheet_by_report_em, symbol=code, ttl_seconds=604800)
        if df is None or df.empty:
            return pd.DataFrame()
        col_map = {
            "报告期": "report_date",
            "经营活动产生的现金流量净额": "operating_cf",
            "投资活动产生的现金流量净额": "investing_cf",
            "筹资活动产生的现金流量净额": "financing_cf",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        keep = [v for v in col_map.values() if v in df.columns]
        if not keep:
            return pd.DataFrame()
        df["code"] = code
        df["report_date"] = pd.to_datetime(df["report_date"])
        return df[["code", "report_date"] + keep].set_index(["code", "report_date"]).sort_index()
    except Exception as e:
        log.debug(f"{code} 现金流量表获取失败: {e}")
        return pd.DataFrame()


def fetch_profit_statement(code: str) -> pd.DataFrame:
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_profit_sheet_by_report_em, symbol=code, ttl_seconds=604800)
        if df is None or df.empty:
            return pd.DataFrame()
        col_map = {
            "报告期": "report_date", "营业总收入": "revenue",
            "净利润": "net_profit", "扣除非经常性损益后的净利润": "net_profit_deducted",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        keep = [v for v in col_map.values() if v in df.columns]
        if not keep:
            return pd.DataFrame()
        df["code"] = code
        df["report_date"] = pd.to_datetime(df["report_date"])
        return df[["code", "report_date"] + keep].set_index(["code", "report_date"]).sort_index()
    except Exception as e:
        log.debug(f"{code} 利润表获取失败: {e}")
        return pd.DataFrame()


def merge_financials(
    indicators: pd.DataFrame, balance: pd.DataFrame,
    cashflow: pd.DataFrame, profit: pd.DataFrame,
) -> pd.DataFrame:
    dfs = [d for d in [indicators, balance, cashflow, profit] if not d.empty]
    if not dfs:
        return pd.DataFrame()
    result = dfs[0]
    for d in dfs[1:]:
        result = result.join(d, how="outer", rsuffix="_dup")
    dup_cols = [c for c in result.columns if c.endswith("_dup")]
    result = result.drop(columns=dup_cols)
    return result
