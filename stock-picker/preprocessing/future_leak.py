"""防未来函数检查."""
import logging
from datetime import datetime

import pandas as pd

log = logging.getLogger(__name__)


def check_financial_announce_date(
    financial_df: pd.DataFrame, target_date: str | datetime,
) -> pd.DataFrame:
    target = pd.to_datetime(target_date)
    if "announce_date" in financial_df.columns:
        mask = pd.to_datetime(financial_df["announce_date"]) <= target
        return financial_df[mask]
    log.warning("财务数据缺少 announce_date 列，无法执行防未来函数检查")
    return financial_df


def check_data_availability(
    stock_code: str, data_date: str,
    list_date_map: dict[str, str], delist_date_map: dict[str, str],
) -> bool:
    target = pd.to_datetime(data_date)
    list_date = pd.to_datetime(list_date_map.get(stock_code, "19900101"))
    if target < list_date:
        return False
    delist_date = delist_date_map.get(stock_code)
    if delist_date and target > pd.to_datetime(delist_date):
        return False
    return True


def ensure_t1_execution(signal_date: str) -> str:
    return (pd.to_datetime(signal_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
