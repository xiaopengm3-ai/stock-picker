"""复合评分融合引擎 — 多维度加权融合."""
import numpy as np
import pandas as pd


def compute_composite_score(
    fundamental_scores: pd.DataFrame,
    technical_scores: pd.DataFrame,
    capital_scores: pd.DataFrame,
    industry_scores: pd.DataFrame,
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """融合四个维度得分 → 最终得分.

    Args:
        fundamental_scores: index=code, 含 fundamental_total 列
        technical_scores: index=code, 含 technical_total 列
        capital_scores: index=code, 含 capital_flow_total 列
        industry_scores: index=code, 含 industry_total 列
        weights: {"fundamental": 0.35, "technical": 0.25, "capital_flow": 0.10, "industry": 0.10}

    Returns:
        DataFrame index=code, columns: final_score + 各维度总分 + 因子细节
    """
    w = weights or {
        "fundamental": 0.35, "technical": 0.25,
        "capital_flow": 0.10, "industry": 0.10,
    }

    all_codes = sorted(set(
        list(fundamental_scores.index) + list(technical_scores.index)
        + list(capital_scores.index) + list(industry_scores.index)
    ))
    if not all_codes:
        return pd.DataFrame()

    result = pd.DataFrame(index=all_codes)

    # 提取各维度总分
    dim_data = {}
    for dim, df, col_name in [
        ("fundamental", fundamental_scores, "fundamental_total"),
        ("technical", technical_scores, "technical_total"),
        ("capital_flow", capital_scores, "capital_flow_total"),
        ("industry", industry_scores, "industry_total"),
    ]:
        if col_name in df.columns:
            dim_data[dim] = df[col_name].reindex(all_codes)
            result[f"{dim}_total"] = dim_data[dim]
        else:
            dim_data[dim] = pd.Series(np.nan, index=all_codes)
            result[f"{dim}_total"] = np.nan

    # 缺失维度处理：权重按比例重分配到可用维度
    available_dims = {k: v for k, v in dim_data.items() if not v.isna().all()}
    total_weight = sum(w.get(k, 0) for k in available_dims)

    final = pd.Series(0.0, index=all_codes)
    for dim, scores in available_dims.items():
        dim_weight = w.get(dim, 0)
        adjusted_weight = dim_weight / total_weight if total_weight > 0 else dim_weight
        final += scores.fillna(50.0) * adjusted_weight

    result["final_score"] = final

    # 合并因子细节列
    for src_df in [fundamental_scores, technical_scores, capital_scores, industry_scores]:
        extra_cols = [c for c in src_df.columns if c not in result.columns and "_total" not in c]
        for col in extra_cols:
            if col in src_df.columns:
                result[col] = src_df[col].reindex(all_codes)

    return result.sort_values("final_score", ascending=False)
