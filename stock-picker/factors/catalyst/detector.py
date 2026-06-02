"""催化剂因子 F41 (Phase 2)."""
import pandas as pd

from ..registry import FactorMeta, register_factor

F41_CATALYST = FactorMeta(
    id="F41", name="催化剂事件", category="catalyst", sub_category="catalyst",
    direction="positive", standardize_method="zscore",
)

# 催化剂类型及有效期（天）
CATALYST_TYPES = {
    "业绩预增": {"weight": 0.25, "expire_days": 90},
    "回购": {"weight": 0.15, "expire_days": 60},
    "增持": {"weight": 0.15, "expire_days": 60},
    "并购重组": {"weight": 0.15, "expire_days": 180},
    "重大订单": {"weight": 0.15, "expire_days": 90},
    "政策利好": {"weight": 0.15, "expire_days": 365},
}


def compute_catalyst_score(codes: list[str]) -> pd.DataFrame:
    """计算催化剂得分.

    Phase 2: 占位实现，所有股票默认 50 分。
    完整实现需要接入公告爬虫 + LLM 分析进行催化剂识别。
    """
    if not codes:
        return pd.DataFrame()
    results = pd.DataFrame({
        "F41_score": 50.0,
        "catalyst_total": 50.0,
    }, index=codes)
    return results


def detect_catalysts_from_announcements(
    announcements: list[dict],
    llm_client=None,
) -> list[dict]:
    """从公告中检测催化剂（需 LLM 接入）.

    Args:
        announcements: [{"code": str, "title": str, "content": str, "date": str}, ...]
        llm_client: AI 分析客户端实例

    Returns:
        [{"code": str, "type": str, "confidence": float, "expire_date": str}, ...]
    """
    return []


register_factor(F41_CATALYST)
