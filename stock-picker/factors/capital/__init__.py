"""资金行为因子模块."""
import pandas as pd

from .north_bound import compute_north_bound_factors
from .main_force import compute_main_force_factors
from .chips import compute_chips_factors

CAPITAL_SUB_WEIGHTS = {
    "north_bound": 0.40,
    "main_force": 0.35,
    "chips": 0.25,
}


def compute_capital_scores(
    codes: list[str],
    sub_weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    w = sub_weights or CAPITAL_SUB_WEIGHTS
    if not codes:
        return pd.DataFrame()

    north = compute_north_bound_factors(codes)
    main = compute_main_force_factors(codes)
    chips = compute_chips_factors(codes)

    result = pd.DataFrame(index=codes)
    result["F33_score"] = north["F33_score"]
    result["F34_score"] = main["F34_score"]
    result["F35_score"] = chips["F35_score"]
    result["F36_score"] = chips["F36_score"]

    result["capital_flow_total"] = (
        north["north_bound_total"].reindex(codes).fillna(50.0) * w["north_bound"]
        + main["main_force_total"].reindex(codes).fillna(50.0) * w["main_force"]
        + chips["chips_total"].reindex(codes).fillna(50.0) * w["chips"]
    )
    return result
