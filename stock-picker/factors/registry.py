"""因子注册表 — 统一管理所有因子的元数据、计算函数和中性化策略."""
from dataclasses import dataclass, field
from collections.abc import Callable


@dataclass
class FactorMeta:
    id: str
    name: str
    category: str
    sub_category: str
    direction: str = "positive"   # positive | negative | neutral
    compute_fn: Callable | None = None
    neutralize_industry: bool = False
    neutralize_market_cap: bool = False
    standardize_method: str = "zscore"   # zscore | percentile
    hard_thresholds: dict[str, float] = field(default_factory=dict)
    weight: float = 0.0


FACTOR_REGISTRY: dict[str, FactorMeta] = {}


def register_factor(meta: FactorMeta) -> FactorMeta:
    FACTOR_REGISTRY[meta.id] = meta
    return meta


def get_factors_by_category(category: str) -> list[FactorMeta]:
    return [f for f in FACTOR_REGISTRY.values() if f.category == category]


def get_factors_by_sub_category(category: str, sub_category: str) -> list[FactorMeta]:
    return [f for f in FACTOR_REGISTRY.values() if f.category == category and f.sub_category == sub_category]
