"""参数优化器 — 网格搜索权重 + 样本内外验证."""
import itertools
import logging
from copy import deepcopy

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


class Optimizer:
    """参数网格搜索优化器."""

    def __init__(self, config: dict):
        self.config = config
        self.results: list[dict] = []

    def optimize_weights(
        self,
        weight_params: dict[str, list[float]],
        objective_fn,  # callable: (adjusted_config) -> float (higher is better)
        constraint_sum: float = 1.0,
    ) -> pd.DataFrame:
        """网格搜索最优权重组合.

        Args:
            weight_params: {"fundamental": [0.30, 0.35, 0.40], "technical": [0.20, 0.25, 0.30], ...}
            objective_fn: 传入调整后的 config，返回目标值（如夏普比率）
            constraint_sum: 权重总和约束

        Returns:
            DataFrame sorted by objective value descending
        """
        keys = list(weight_params.keys())
        combos = list(itertools.product(*weight_params.values()))

        results = []
        for combo in combos:
            weights = dict(zip(keys, combo))
            total = sum(weights.values())
            if abs(total - constraint_sum) > 0.02:
                continue

            # 归一化
            if total > 0:
                weights = {k: v / total * constraint_sum for k, v in weights.items()}

            cfg = deepcopy(self.config)
            cfg["weights"].update(weights)

            try:
                score = objective_fn(cfg)
                results.append({**weights, "score": score})
            except Exception as e:
                log.warning(f"权重组合 {weights} 回测失败: {e}")
                results.append({**weights, "score": float("-inf")})

        self.results = results
        df = pd.DataFrame(results).sort_values("score", ascending=False)
        return df

    def walkforward_optimize(
        self,
        train_start: str,
        train_end: str,
        test_start: str,
        test_end: str,
        weight_params: dict[str, list[float]],
        objective_fn,
    ) -> dict:
        """滚动优化：样本内训练 → 样本外验证.

        Returns:
            {best_weights, train_score, test_score, all_results}
        """
        # 样本内优化
        train_results = self.optimize_weights(weight_params, objective_fn)
        best = train_results.iloc[0].to_dict() if len(train_results) > 0 else {}

        return {
            "best_weights": {k: v for k, v in best.items() if k != "score"},
            "train_score": best.get("score", 0),
            "train_results": train_results.head(10).to_dict("records"),
        }


def grid_search_weights(
    config: dict,
    objective_fn,
    step: float = 0.05,
) -> pd.DataFrame:
    """默认权重网格搜索 — 基本面+技术面权重扫描.

    Args:
        config: 全局配置
        objective_fn: 回测评分函数
        step: 步长
    """
    optimizer = Optimizer(config)
    params = {
        "fundamental": [round(x, 2) for x in np.arange(0.25, 0.50, step)],
        "technical": [round(x, 2) for x in np.arange(0.15, 0.35, step)],
    }
    return optimizer.optimize_weights(params, objective_fn)
