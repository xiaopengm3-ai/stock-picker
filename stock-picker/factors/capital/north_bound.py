"""北向资金因子 F33 (Phase 1: 占位实现)."""
import numpy as np
import pandas as pd

from ..registry import FactorMeta, register_factor

F33_NORTH_BOUND = FactorMeta(
    id="F33", name="北向资金净流入", category="capital", sub_category="north_bound",
    direction="positive", neutralize_industry=True, standardize_method="zscore",
)


def compute_north_bound_factors(codes: list[str]) -> pd.DataFrame:
    if not codes:
        return pd.DataFrame()
    results = pd.DataFrame({"F33_score": 50.0}, index=codes)
    results["north_bound_total"] = results["F33_score"]
    return results


register_factor(F33_NORTH_BOUND)
