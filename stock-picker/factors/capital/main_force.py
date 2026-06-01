"""主力资金因子 F34 (Phase 1: 占位实现)."""
import pandas as pd

from ..registry import FactorMeta, register_factor

F34_MAIN_FORCE = FactorMeta(
    id="F34", name="主力资金净流入", category="capital", sub_category="main_force",
    direction="positive", neutralize_market_cap=True, standardize_method="zscore",
)


def compute_main_force_factors(codes: list[str]) -> pd.DataFrame:
    if not codes:
        return pd.DataFrame()
    results = pd.DataFrame({"F34_score": 50.0}, index=codes)
    results["main_force_total"] = results["F34_score"]
    return results


register_factor(F34_MAIN_FORCE)
