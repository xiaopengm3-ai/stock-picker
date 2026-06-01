"""测试估值因子."""
import numpy as np
import pandas as pd
from factors.fundamental.valuation import (
    compute_pe_absolute, compute_pe_percentile, compute_dividend_yield,
)


def test_pe_absolute_perfect_range():
    valuation = pd.DataFrame({"pe": [10.0, 12.0, 8.0]}, index=["A", "B", "C"])
    scores = compute_pe_absolute(valuation)
    assert (scores == 100.0).all()


def test_pe_absolute_zero():
    valuation = pd.DataFrame({"pe": [60.0, -5.0, 0.0]}, index=["A", "B", "C"])
    scores = compute_pe_absolute(valuation)
    assert (scores == 0.0).all()


def test_pe_absolute_interpolation():
    valuation = pd.DataFrame({"pe": [32.5]}, index=["A"])
    scores = compute_pe_absolute(valuation)
    assert 45 < scores["A"] < 55


def test_pe_percentile_lower_gets_higher():
    valuation = pd.DataFrame({"pe": [10.0, 20.0, 30.0]}, index=["A", "B", "C"])
    industry = pd.Series(["科技", "科技", "科技"], index=["A", "B", "C"])
    scores = compute_pe_percentile(valuation, industry)
    assert scores["A"] > scores["C"]


def test_dividend_yield():
    valuation = pd.DataFrame({"dividend_yield": [1.5, 3.0, 0.0]}, index=["A", "B", "C"])
    scores = compute_dividend_yield(valuation)
    assert scores["B"] == 100.0
    assert scores["C"] == 0.0
    assert 40 < scores["A"] < 60
