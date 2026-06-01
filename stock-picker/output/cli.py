"""CLI 格式化输出 — 打分卡展示."""
import pandas as pd


def print_header(date: str):
    print("=" * 70)
    print("  A股智能选股系统 V2.0")
    print(f"  选股日期: {date}")
    print("=" * 70)


def print_stock_card(
    rank: int, code: str, name: str, industry: str,
    scores: pd.Series, detail_cols: list[str] | None = None,
):
    final = scores.get("final_score", 0)
    conf_label = scores.get("confidence_label", "—")
    rank_level = scores.get("rank_level", "—")

    print(f"\n╔{'=' * 68}╗")
    print(f"║  \U0001f3c6 #{rank}  {name} ({code})")
    print(f"║      推荐等级: {rank_level}  {conf_label}")
    print(f"║      最终得分: {final:.1f} / 100")
    print(f"║      行业: {industry}")
    print(f"═{'=' * 68}║")
    print(f"║  评分明细:")

    dims = [
        ("基本面", "fundamental_total", 0.60),
        ("技术面", "technical_total", 0.25),
        ("资金面", "capital_flow_total", 0.10),
        ("行业面", "industry_total", 0.10),
    ]
    for name, col, _ in dims:
        val = scores.get(col, 0)
        if pd.isna(val):
            val = 0
        print(f"║    {name}: {val:.1f}")

    # 子维度明细
    sub_dims = [
        ("估值", "valuation_total"), ("成长", "growth_total"),
        ("质量", "quality_total"), ("预期", "forward_total"),
        ("趋势", "trend_total"), ("动量", "momentum_total"),
        ("量价", "volume_total"), ("形态", "pattern_total"),
        ("多周期", "multi_tf_total"),
    ]
    for name, col in sub_dims:
        if col in scores.index:
            val = scores[col]
            print(f"║      {name}: {val:.1f}" if not isinstance(val, pd.Series) else f"║      {name}: {float(val):.1f}")

    print(f"╚{'=' * 68}╝")


def print_no_results(min_score: float):
    print(f"\n{'─' * 70}")
    print(f"  今日无符合条件的标的（最低分数阈值: {min_score}）")
    print(f"{'─' * 70}")


def print_summary(
    total_stocks: int, after_filter: int, after_risk: int,
    final_count: int, elapsed_seconds: float,
):
    print(f"\n{'─' * 70}")
    print(f"  筛选流程: {total_stocks}只 → 过滤后{after_filter}只 → 排雷后{after_risk}只 → 精选{final_count}只")
    print(f"  耗时: {elapsed_seconds:.0f}秒")
    print(f"{'=' * 70}")
    print(f"  ⚠️ 免责声明: 本系统仅提供研究参考，不构成投资建议。")
    print(f"  股市有风险，投资需谨慎。")
    print(f"{'=' * 70}")
