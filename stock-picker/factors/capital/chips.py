"""筹码因子 F35–F36 (Phase 1: 占位实现)."""
import pandas as pd

from ..registry import FactorMeta, register_factor

F35_SHAREHOLDER_CHANGE = FactorMeta(
    id="F35", name="股东户数变化", category="capital", sub_category="chips",
    direction="negative", neutralize_market_cap=True, standardize_method="zscore",
)
F36_INST_HOLDING = FactorMeta(
    id="F36", name="机构持仓变化", category="capital", sub_category="chips",
    direction="positive", neutralize_industry=True, standardize_method="zscore",
)

CHIPS_WEIGHTS = {"F35": 0.50, "F36": 0.50}


def compute_chips_factors(codes: list[str]) -> pd.DataFrame:
    if not codes:
        return pd.DataFrame()
    results = pd.DataFrame({"F35_score": 50.0, "F36_score": 50.0}, index=codes)
    results["chips_total"] = 50.0
    return results


for f in [F35_SHAREHOLDER_CHANGE, F36_INST_HOLDING]:
    register_factor(f)
