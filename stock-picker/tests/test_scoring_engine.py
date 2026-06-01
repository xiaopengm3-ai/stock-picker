"""测试评分融合引擎."""
import pandas as pd
from scoring.engine import compute_composite_score


def test_composite_score_basic():
    codes = ["A", "B", "C"]
    fundamental = pd.DataFrame({"fundamental_total": [80.0, 60.0, 40.0], "F01_score": [90.0, 60.0, 30.0]}, index=codes)
    technical = pd.DataFrame({"technical_total": [70.0, 80.0, 50.0]}, index=codes)
    capital = pd.DataFrame({"capital_flow_total": [60.0, 70.0, 80.0]}, index=codes)
    industry = pd.DataFrame({"industry_total": [75.0, 65.0, 55.0]}, index=codes)

    result = compute_composite_score(fundamental, technical, capital, industry)
    assert "final_score" in result.columns
    assert len(result) == 3
    assert result["final_score"].iloc[0] >= result["final_score"].iloc[-1]


def test_missing_dimension_weight_redistribution():
    codes = ["A"]
    fundamental = pd.DataFrame({"fundamental_total": [80.0]}, index=codes)
    technical = pd.DataFrame({"technical_total": [70.0]}, index=codes)
    capital = pd.DataFrame()
    industry = pd.DataFrame()

    result = compute_composite_score(
        fundamental, technical, capital, industry,
        weights={"fundamental": 0.35, "technical": 0.25, "capital_flow": 0.10, "industry": 0.10},
    )
    expected = 80.0 * (0.35 / 0.60) + 70.0 * (0.25 / 0.60)
    assert abs(result.loc["A", "final_score"] - expected) < 0.1


def test_composite_score_sorts_descending():
    fundamental = pd.DataFrame({"fundamental_total": [40.0, 80.0, 60.0]}, index=["X", "Y", "Z"])
    technical = pd.DataFrame({"technical_total": [50.0, 50.0, 50.0]}, index=["X", "Y", "Z"])
    capital = pd.DataFrame()
    industry = pd.DataFrame()
    result = compute_composite_score(fundamental, technical, capital, industry)
    assert result.index[0] == "Y"
