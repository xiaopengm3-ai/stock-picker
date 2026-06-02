"""因子评价主控 — 汇总 IC/分层/贡献率分析."""
import logging

import numpy as np
import pandas as pd

from .ic_analysis import compute_ic, ic_summary
from .layered_backtest import layered_backtest, quintile_analysis
from .contribution import factor_contribution, auto_weight_adjust

log = logging.getLogger(__name__)

FACTOR_SCORE_COLS = [f"F{i:02d}_score" for i in range(1, 42)]


class FactorEvaluator:
    """因子评价主控."""

    def __init__(self, config: dict):
        self.config = config
        self.eval_cfg = config.get("factor_eval", {})
        self.ic_window = self.eval_cfg.get("ic_window_months", 12)
        self.auto_downgrade = self.eval_cfg.get("auto_downgrade_enabled", True)
        self.icir_threshold = self.eval_cfg.get("auto_retire_icir_threshold", 0.1)

    def evaluate(
        self,
        factor_scores_df: pd.DataFrame,
        forward_returns: pd.Series,
        weights: dict[str, float],
    ) -> dict:
        """运行完整因子评价.

        Args:
            factor_scores_df: index=code, 含 F01_score..F41_score 列
            forward_returns: index=code, N日收益率
            weights: 当前因子权重映射

        Returns:
            {ic_summary, contributions, top_quintile, adjusted_weights, suggestions}
        """
        score_cols = [c for c in FACTOR_SCORE_COLS if c in factor_scores_df.columns]
        if not score_cols:
            return {"error": "无因子得分数据"}

        scores = factor_scores_df[score_cols]

        # IC 分析
        ic_df = ic_summary(scores, forward_returns)

        # ICIR（单期无时序，用占位值）
        ic_df["icir"] = 0.0
        ic_df["positive_ic_rate"] = (ic_df["ic"] > 0).astype(float)

        # 因子贡献率
        contrib_df = factor_contribution(ic_df, weights)

        # 分层回测（取 IC 最高的因子做演示）
        top_factor = ic_df.iloc[0]["factor"] if len(ic_df) > 0 else None
        layered_result = {}
        if top_factor and top_factor in scores.columns:
            layered_result = layered_backtest(scores[top_factor], forward_returns)

        # 自动权重调整
        adjusted_weights, suggestions = auto_weight_adjust(ic_df, weights, self.icir_threshold)

        return {
            "ic_summary": ic_df,
            "contributions": contrib_df,
            "top_factor": top_factor,
            "layered_result": layered_result,
            "adjusted_weights": adjusted_weights,
            "suggestions": suggestions,
        }


def run_factor_evaluation(
    factor_scores_df: pd.DataFrame,
    forward_returns: pd.Series,
    config: dict | None = None,
) -> dict:
    """便捷入口."""
    evaluator = FactorEvaluator(config or {})
    weights = config.get("weights", {}) if config else {}
    # 构建因子级权重映射
    factor_weights = {}
    # 从 registry 获取各因子权重
    from factors.registry import FACTOR_REGISTRY
    for fid, meta in FACTOR_REGISTRY.items():
        factor_weights[f"{fid}_score"] = meta.weight
    return evaluator.evaluate(factor_scores_df, forward_returns, factor_weights)
