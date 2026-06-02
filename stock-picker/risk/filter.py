"""硬性过滤 — ST/退市/新股/停牌/立案调查."""
import logging
from datetime import datetime, timedelta

import pandas as pd

log = logging.getLogger(__name__)


def apply_hard_filters(
    codes: list[str],
    valuation_df: pd.DataFrame,
    config: dict,
    blacklist: set[str] | None = None,
) -> list[str]:
    """对股票池执行硬性过滤.

    Args:
        codes: 原始股票列表
        valuation_df: 估值数据（用于 PE 过滤）
        config: 全局配置
        blacklist: 黑名单集合

    Returns:
        过滤后的股票列表
    """
    filters = config.get("screening", {}).get("filters", {})
    risk_cfg = config.get("screening", {}).get("risk_thresholds", {})
    result = list(codes)

    # 黑名单
    if blacklist:
        result = [c for c in result if c not in blacklist]
        log.debug(f"黑名单过滤后: {len(result)}")

    # ST 过滤
    if filters.get("exclude_st", True) and "st_status" in valuation_df.columns:
        st_codes = set(valuation_df[valuation_df["st_status"] == True].index)
        result = [c for c in result if c not in st_codes]
        log.debug(f"ST过滤后: {len(result)}")

    # PE 硬过滤
    if "pe" in valuation_df.columns:
        pe_max = risk_cfg.get("pe_absolute_max", 50)
        pe_valid = valuation_df[valuation_df["pe"].between(0, pe_max)].index
        result = [c for c in result if c in pe_valid]

    # 商誉过滤
    if "goodwill_ratio" in valuation_df.columns:
        gw_max = risk_cfg.get("goodwill_to_equity_max", 0.50)
        gw_valid = valuation_df[valuation_df["goodwill_ratio"] <= gw_max].index
        result = [c for c in result if c in gw_valid]

    # 质押过滤
    if "pledge_ratio" in valuation_df.columns:
        pledge_max = risk_cfg.get("pledge_ratio_max", 0.60)
        pledge_valid = valuation_df[valuation_df["pledge_ratio"] <= pledge_max].index
        result = [c for c in result if c in pledge_valid]

    # 连续亏损过滤
    cons_loss = risk_cfg.get("consecutive_loss_quarters", 2)
    if cons_loss > 0 and "consecutive_losses" in valuation_df.columns:
        loss_valid = valuation_df[valuation_df["consecutive_losses"] < cons_loss].index
        result = [c for c in result if c in loss_valid]

    # 流动性
    min_turnover = filters.get("min_daily_turnover_yuan", 30000000)
    if "amount" in valuation_df.columns:
        liq_valid = valuation_df[valuation_df["amount"] >= min_turnover].index
        result = [c for c in result if c in liq_valid]

    return result
