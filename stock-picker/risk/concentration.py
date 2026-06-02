"""行业集中度限制."""
import pandas as pd


def check_concentration(
    top_codes: list[str],
    industry_map: pd.Series,
    max_single_pct: float = 0.30,
    max_same_industry_in_top: int = 2,
) -> tuple[list[str], dict]:
    """检查行业集中度，超过限制的剔除.

    Args:
        top_codes: 排名靠前的股票列表
        industry_map: code → 行业名
        max_single_pct: 单行业最大占比
        max_same_industry_in_top: 同一行业在 Top N 中的最大数量

    Returns:
        (调整后的列表, 违规记录)
    """
    violations = {}
    result = []
    industry_count = {}

    for code in top_codes:
        ind = industry_map.get(code, "未知")
        if isinstance(ind, pd.Series):
            ind = str(ind.iloc[0]) if len(ind) > 0 else "未知"

        # 检查单行业数量限制
        if industry_count.get(ind, 0) >= max_same_industry_in_top:
            violations[code] = f"行业'{ind}'已满{max_same_industry_in_top}只"
            continue

        industry_count[ind] = industry_count.get(ind, 0) + 1

    # 重新构建 result 考虑行业配额
    industry_count = {}
    for code in top_codes:
        if code in violations:
            continue
        ind = industry_map.get(code, "未知")
        if isinstance(ind, pd.Series):
            ind = str(ind.iloc[0]) if len(ind) > 0 else "未知"

        if industry_count.get(ind, 0) >= max_same_industry_in_top:
            continue

        result.append(code)
        industry_count[ind] = industry_count.get(ind, 0) + 1

    return result, violations


def limit_same_industry(
    codes: list[str],
    industry_map: pd.Series,
    max_count: int = 2,
) -> list[str]:
    """限制同一行业最多 max_count 只."""
    industry_count = {}
    result = []
    for code in codes:
        ind = industry_map.get(code, "未知")
        if isinstance(ind, pd.Series):
            ind = str(ind.iloc[0]) if len(ind) > 0 else "未知"
        if industry_count.get(ind, 0) < max_count:
            result.append(code)
            industry_count[ind] = industry_count.get(ind, 0) + 1
    return result
