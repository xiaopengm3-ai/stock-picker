"""复合评分融合引擎 — 7维加权融合."""
import numpy as np
import pandas as pd


def compute_composite_score(
    fundamental_scores: pd.DataFrame,
    technical_scores: pd.DataFrame,
    capital_scores: pd.DataFrame,
    industry_scores: pd.DataFrame,
    news_scores: pd.DataFrame | None = None,
    catalyst_scores: pd.DataFrame | None = None,
    regime_score: float = 50.0,
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """融合七维得分 → 最终得分.

    Args:
        fundamental_scores: 含 fundamental_total 列
        technical_scores: 含 technical_total 列
        capital_scores: 含 capital_flow_total 列
        industry_scores: 含 industry_total 列
        news_scores: 含 news_total 列（可选）
        catalyst_scores: 含 catalyst_total 列（可选）
        regime_score: 市场环境得分 0-100
        weights: 维度权重字典

    Returns:
        DataFrame index=code, columns: final_score + 各维度总分 + 因子细节
    """
    w = weights or {
        "fundamental": 0.35, "technical": 0.25, "capital_flow": 0.10,
        "industry": 0.10, "news": 0.10, "catalyst": 0.05, "market_regime": 0.05,
    }

    dim_configs = [
        ("fundamental", fundamental_scores, "fundamental_total"),
        ("technical", technical_scores, "technical_total"),
        ("capital_flow", capital_scores, "capital_flow_total"),
        ("industry", industry_scores, "industry_total"),
        ("news", news_scores or pd.DataFrame(), "news_total"),
        ("catalyst", catalyst_scores or pd.DataFrame(), "catalyst_total"),
    ]

    # 收集所有 code
    all_codes_set = set()
    for _, df, _ in dim_configs:
        if not df.empty:
            all_codes_set.update(df.index.tolist())
    all_codes = sorted(all_codes_set)

    if not all_codes:
        return pd.DataFrame()

    result = pd.DataFrame(index=all_codes)
    dim_data = {}

    for dim, df, col_name in dim_configs:
        if not df.empty and col_name in df.columns:
            dim_data[dim] = df[col_name].reindex(all_codes)
            result[f"{dim}_total"] = dim_data[dim]
        elif dim in ("news", "catalyst"):
            dim_data[dim] = pd.Series(50.0, index=all_codes)  # 默认中性
            result[f"{dim}_total"] = 50.0
        else:
            dim_data[dim] = pd.Series(np.nan, index=all_codes)
            result[f"{dim}_total"] = np.nan

    # market_regime 维度：统一赋值
    dim_data["market_regime"] = pd.Series(regime_score, index=all_codes)
    result["market_regime_total"] = regime_score

    # 缺失维度：权重按比例重分配
    available_dims = {k: v for k, v in dim_data.items() if not v.isna().all()}
    total_weight = sum(w.get(k, 0) for k in available_dims)

    final = pd.Series(0.0, index=all_codes)
    for dim, scores in available_dims.items():
        dim_weight = w.get(dim, 0)
        adjusted_weight = dim_weight / total_weight if total_weight > 0 else dim_weight
        final += scores.fillna(50.0) * adjusted_weight

    result["final_score"] = final

    # 合并因子细节
    for df in [fundamental_scores, technical_scores, capital_scores, industry_scores,
               news_scores, catalyst_scores]:
        if df is None or df.empty:
            continue
        for col in df.columns:
            if col not in result.columns and "_total" not in col:
                result[col] = df[col].reindex(all_codes)

    return result.sort_values("final_score", ascending=False)
