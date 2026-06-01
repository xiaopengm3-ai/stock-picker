"""行业景气度因子 F37–F38."""
import numpy as np
import pandas as pd

from ..registry import FactorMeta, register_factor

F37_INDUSTRY_PROSPERITY = FactorMeta(
    id="F37", name="行业景气度", category="industry", sub_category="prosperity",
    direction="positive", standardize_method="zscore",
)
F38_INDUSTRY_STRENGTH = FactorMeta(
    id="F38", name="行业相对强度", category="industry", sub_category="prosperity",
    direction="positive", standardize_method="zscore",
)

INDUSTRY_WEIGHTS = {"F37": 0.60, "F38": 0.40}


def compute_industry_scores(
    codes: list[str],
    industry_map: pd.Series,
    industry_index_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """计算行业因子得分.

    Phase 1: 简化为所有行业默认中性分数。
    Phase 2 将接入行业指数涨跌幅和资金流向数据。
    """
    if not codes:
        return pd.DataFrame()

    # 默认所有行业为中性 50 分
    unique_industries = industry_map.reindex(codes).fillna("未知").unique()
    industry_score_map = {ind: 50.0 for ind in unique_industries}

    results = pd.DataFrame(index=codes)
    results["F37_score"] = [industry_score_map.get(industry_map.get(c, "未知"), 50.0) for c in codes]
    results["F38_score"] = results["F37_score"]

    results["industry_total"] = (
        results["F37_score"] * INDUSTRY_WEIGHTS["F37"]
        + results["F38_score"] * INDUSTRY_WEIGHTS["F38"]
    )
    return results


for f in [F37_INDUSTRY_PROSPERITY, F38_INDUSTRY_STRENGTH]:
    register_factor(f)
