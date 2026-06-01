"""幸存者偏差处理 — 退市股票 + ST 历史状态."""
import logging

import pandas as pd

log = logging.getLogger(__name__)

DELISTED_STOCKS: dict[str, str] = {}


def get_delisted_stocks() -> dict[str, str]:
    try:
        import akshare as ak
        ak.stock_info_sz_delist()
        return {}
    except Exception:
        return DELISTED_STOCKS


def build_st_status_history() -> pd.DataFrame:
    return pd.DataFrame()


def get_active_universe(
    date: str, all_codes: list[str], list_dates: dict[str, str],
    delist_dates: dict[str, str], st_status: dict[str, bool],
) -> list[str]:
    target = pd.to_datetime(date)
    active = []
    for code in all_codes:
        list_date = pd.to_datetime(list_dates.get(code, "19900101"))
        if target < list_date:
            continue
        delist_date = delist_dates.get(code)
        if delist_date and target > pd.to_datetime(delist_date):
            continue
        if st_status.get(code, False):
            continue
        active.append(code)
    return active
