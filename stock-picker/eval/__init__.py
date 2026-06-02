"""因子评价体系."""
from .ic_analysis import compute_ic, compute_icir, ic_summary
from .layered_backtest import layered_backtest, quintile_analysis
from .contribution import factor_contribution, auto_weight_adjust
from .evaluator import FactorEvaluator, run_factor_evaluation
