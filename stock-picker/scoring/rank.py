"""排名与置信度标签."""
import pandas as pd


def assign_confidence(final_score: float) -> tuple[str, str]:
    if final_score >= 85:
        return "⭐⭐⭐⭐⭐", "S"
    elif final_score >= 75:
        return "⭐⭐⭐⭐", "A"
    elif final_score >= 60:
        return "⭐⭐⭐", "B"
    else:
        return "—", "不推荐"


def rank_stocks(
    composite_scores: pd.DataFrame,
    top_n: int = 2,
    min_score: float = 60.0,
) -> pd.DataFrame:
    df = composite_scores.copy()
    df = df[df["final_score"] >= min_score]
    if df.empty:
        return pd.DataFrame()
    df = df.head(top_n).copy()
    labels = df["final_score"].apply(assign_confidence)
    df["confidence_label"] = [l[0] for l in labels]
    df["rank_level"] = [l[1] for l in labels]
    return df


def determine_cycle(fundamental_score: float, technical_score: float) -> str:
    if fundamental_score >= 70 and technical_score >= 70:
        return "中线"
    elif technical_score >= 70:
        return "短线"
    else:
        return "长线"
