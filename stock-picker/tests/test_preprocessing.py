"""测试预处理层."""
import numpy as np
import pandas as pd
from preprocessing.outlier import mad_outlier_clip, mad_outlier_clip_dataframe
from preprocessing.standardize import zscore_standardize, percentile_rank, zscore_to_score


def test_mad_clip_outliers():
    s = pd.Series([1, 2, 3, 4, 5, 100])
    clipped = mad_outlier_clip(s, multiplier=3.0)
    assert clipped.max() < 100
    assert clipped.min() >= 1


def test_mad_clip_no_outliers():
    s = pd.Series([10, 11, 12, 13, 14])
    clipped = mad_outlier_clip(s)
    assert clipped.equals(s)


def test_mad_clip_with_nan():
    s = pd.Series([1, 2, np.nan, 100])
    clipped = mad_outlier_clip(s)
    assert np.isnan(clipped.iloc[2])
    assert clipped.iloc[3] < 100


def test_zscore_mean_near_zero():
    s = pd.Series([10, 20, 30, 40, 50])
    z = zscore_standardize(s)
    assert abs(z.mean()) < 1e-10


def test_percentile_rank():
    s = pd.Series([1, 2, 3, 4, 5])
    ranks = percentile_rank(s)
    assert ranks.max() == 100.0
    assert ranks.min() > 0


def test_zscore_to_score_range():
    s = pd.Series([-5, 0, 5])
    scores = zscore_to_score(s)
    assert scores.min() >= 0
    assert scores.max() <= 100
