"""基本面因子模块 — 汇总估值+成长+质量+预期四个子维度."""
import numpy as np
import pandas as pd

from .valuation import (
    compute_pe_percentile, compute_pb_percentile, compute_ps_percentile,
    compute_pe_absolute, compute_dividend_yield,
    VALUATION_WEIGHTS,
)
from .growth import (
    compute_roe, compute_roe_trend, compute_revenue_growth,
    compute_profit_growth, compute_gross_margin_trend,
    GROWTH_WEIGHTS,
)
from .quality import (
    compute_debt_ratio, compute_cfo_to_profit, compute_goodwill_ratio,
    compute_pledge_ratio, compute_insider_selling,
    QUALITY_WEIGHTS,
)
from .forward import (
    compute_earnings_forecast, compute_analyst_upgrade,
    compute_advance_receipts, compute_cfo_trend, compute_insider_buying,
    FORWARD_WEIGHTS,
)

FUNDAMENTAL_SUB_WEIGHTS = {
    "valuation": 0.35,
    "growth": 0.25,
    "quality": 0.25,
    "forward": 0.15,
}


def compute_fundamental_scores(
    valuation_df: pd.DataFrame,
    indicators_df: pd.DataFrame,
    financial_df: pd.DataFrame,
    industry_map: pd.Series,
    sub_weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """计算所有基本面因子的 0-100 得分并加权汇总.

    Args:
        valuation_df: index=code, 含 pe/pb/ps/dividend_yield 列
        indicators_df: 财务指标 MultiIndex (code, report_date)
        financial_df: 财务宽表 MultiIndex (code, report_date)
        industry_map: index=code, values=申万一级行业名
        sub_weights: 子维度权重覆写

    Returns:
        DataFrame index=code, columns: F01_score..F20_score, valuation/growth/quality/forward/fundamental_total
    """
    w = sub_weights or FUNDAMENTAL_SUB_WEIGHTS
    codes = valuation_df.index.tolist() if not valuation_df.empty else []

    if not codes:
        return pd.DataFrame()

    scores = pd.DataFrame(index=codes)

    # --- 估值 ---
    scores["F01_score"] = compute_pe_percentile(valuation_df, industry_map)
    scores["F02_score"] = compute_pb_percentile(valuation_df, industry_map)
    scores["F03_score"] = compute_ps_percentile(valuation_df, industry_map)
    scores["F04_score"] = compute_pe_absolute(valuation_df)
    scores["F05_score"] = compute_dividend_yield(valuation_df)

    val_cols = ["F01_score", "F02_score", "F03_score", "F04_score", "F05_score"]
    val_w = [VALUATION_WEIGHTS[f"F0{i+1:02d}"] for i in range(5)]
    scores["valuation_total"] = sum(
        scores[c].fillna(50.0) * val_w[i] for i, c in enumerate(val_cols)
    )

    # --- 成长 ---
    scores["F06_score"] = compute_roe(indicators_df).reindex(codes)
    scores["F07_score"] = compute_roe_trend(indicators_df).reindex(codes)
    scores["F08_score"] = compute_revenue_growth(financial_df).reindex(codes)
    scores["F09_score"] = compute_profit_growth(financial_df).reindex(codes)
    scores["F10_score"] = compute_gross_margin_trend(indicators_df).reindex(codes)

    grow_cols = ["F06_score", "F07_score", "F08_score", "F09_score", "F10_score"]
    grow_w = [GROWTH_WEIGHTS[f"F{i+6:02d}"] for i in range(5)]
    scores["growth_total"] = sum(
        scores[c].fillna(50.0) * grow_w[i] for i, c in enumerate(grow_cols)
    )

    # --- 质量 ---
    scores["F11_score"] = compute_debt_ratio(financial_df).reindex(codes).fillna(50.0)
    scores["F12_score"] = compute_cfo_to_profit(financial_df).reindex(codes).fillna(50.0)
    scores["F13_score"] = compute_goodwill_ratio(financial_df).reindex(codes).fillna(50.0)
    scores["F14_score"] = compute_pledge_ratio(financial_df).reindex(codes).fillna(50.0)
    scores["F15_score"] = compute_insider_selling(financial_df).reindex(codes).fillna(50.0)

    qual_cols = ["F11_score", "F12_score", "F13_score", "F14_score", "F15_score"]
    qual_w = [QUALITY_WEIGHTS[f"F{i+11:02d}"] for i in range(5)]
    scores["quality_total"] = sum(
        scores[c].fillna(50.0) * qual_w[i] for i, c in enumerate(qual_cols)
    )

    # --- 预期 ---
    scores["F16_score"] = compute_earnings_forecast(financial_df).reindex(codes).fillna(50.0)
    scores["F17_score"] = compute_analyst_upgrade(financial_df).reindex(codes).fillna(50.0)
    scores["F18_score"] = compute_advance_receipts(financial_df).reindex(codes).fillna(50.0)
    scores["F19_score"] = compute_cfo_trend(financial_df).reindex(codes).fillna(50.0)
    scores["F20_score"] = compute_insider_buying(financial_df).reindex(codes).fillna(50.0)

    fwd_cols = ["F16_score", "F17_score", "F18_score", "F19_score", "F20_score"]
    fwd_w = [FORWARD_WEIGHTS[f"F{i+16:02d}"] for i in range(5)]
    scores["forward_total"] = sum(
        scores[c].fillna(50.0) * fwd_w[i] for i, c in enumerate(fwd_cols)
    )

    # --- 汇总 ---
    scores["fundamental_total"] = (
        scores["valuation_total"] * w["valuation"]
        + scores["growth_total"] * w["growth"]
        + scores["quality_total"] * w["quality"]
        + scores["forward_total"] * w["forward"]
    )

    return scores
