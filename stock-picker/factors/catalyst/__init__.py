"""催化剂因子模块."""
import pandas as pd
from .detector import compute_catalyst_score


def compute_catalyst_scores(codes: list[str]) -> pd.DataFrame:
    return compute_catalyst_score(codes)
