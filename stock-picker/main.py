#!/usr/bin/env python3
"""A股智能选股系统 V2.0 — GUI + CLI 双模式入口.

默认启动 GUI (PyQt6 桌面程序)。CLI 模式: python main.py --cli
"""
import argparse
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from data.fetcher import DataFetcher
from data.valuation import fetch_valuation_today
from data.industry import fetch_industry_classification
from data.market import fetch_all_daily_hist
from data.index import fetch_all_index_daily
from data.bulk_financial import fetch_all_bulk_financials

from factors.fundamental import compute_fundamental_scores
from factors.technical import compute_technical_scores
from factors.capital import compute_capital_scores
from factors.industry import compute_industry_scores
from factors.news import compute_news_scores
from factors.catalyst import compute_catalyst_scores

from environment import detect_market_state, adjust_weights_for_regime
from ai import get_ai_client
from exit import check_exit_conditions, Position as ExitPosition

from risk import apply_hard_filters, Blacklist
from scoring.engine import compute_composite_score
from scoring.rank import rank_stocks, determine_cycle
from output.cli import print_header, print_stock_card, print_no_results, print_summary

def _expand_env_vars(obj):
    """递归展开 ${VAR_NAME} 引用为 os.environ 值."""
    if isinstance(obj, str):
        def replacer(m):
            return os.environ.get(m.group(1), m.group(0))
        return re.sub(r'\$\{(\w+)\}', replacer, obj)
    elif isinstance(obj, dict):
        return {k: _expand_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_expand_env_vars(v) for v in obj]
    return obj


# 日志级别在 load_config 后设置，这里先用默认值
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("stock_picker")


def get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def load_config(path: str = "config.yaml") -> dict:
    if not os.path.isabs(path):
        # PyInstaller 打包后，config.yaml 在 _MEIPASS 临时目录中
        if getattr(sys, 'frozen', False):
            base = Path(sys._MEIPASS)
        else:
            base = get_base_dir()
        path = str(base / path)
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    # 展开 ${ENV_VAR} 引用
    config = _expand_env_vars(config)
    # 应用配置中的日志级别
    log_level = config.get("system", {}).get("log_level", "INFO").upper()
    if hasattr(logging, log_level):
        logging.getLogger().setLevel(getattr(logging, log_level))
    return config


def get_stock_list(fetcher: DataFetcher) -> pd.DataFrame:
    import akshare as ak
    try:
        df = fetcher.fetch(ak.stock_info_a_code_name, ttl_seconds=86400)
        if df is None or df.empty:
            return pd.DataFrame(columns=["code", "name"])
        if "code" not in df.columns:
            col0 = df.columns[0]
            df = pd.DataFrame({"code": df[col0].astype(str).str.zfill(6),
                               "name": df.iloc[:, 1] if df.shape[1] > 1 else df[col0]})
        else:
            df["code"] = df["code"].astype(str).str.zfill(6)
        return df
    except Exception as e:
        log.error(f"获取股票列表失败: {e}")
        return pd.DataFrame(columns=["code", "name"])


def run_screening(config: dict, date: str | None = None, top_n: int | None = None):
    t0 = time.time()
    top_n = top_n or config["screening"]["top_n"]
    min_score = config["screening"]["min_score"]
    target_date = date or datetime.now().strftime("%Y-%m-%d")

    print_header(target_date)

    cache_dir = config.get("system", {}).get("cache_dir", "./data/cache")
    if not os.path.isabs(cache_dir):
        cache_dir = str(get_base_dir() / cache_dir)

    fetcher = DataFetcher(
        cache_dir=cache_dir,
        timeout=config.get("data", {}).get("timeout_seconds", 30),
        retry=config.get("data", {}).get("retry_count", 1),
    )

    # ===== Step 1: 股票列表 + 市场环境 =====
    log.info("Step 1/8: 获取股票列表 + 市场环境...")
    stock_list = get_stock_list(fetcher)
    all_codes = stock_list["code"].tolist()
    code_to_name = dict(zip(stock_list["code"], stock_list.get("name", stock_list["code"])))
    log.info(f"  全市场: {len(all_codes)} 只")

    # 市场环境识别
    index_data = fetch_all_index_daily()
    market_state = detect_market_state(index_data)
    adjusted_weights = adjust_weights_for_regime(market_state, config.get("weights"))

    log.info(f"  市场温度: {market_state.temperature:.0f}/100  {market_state.regime}")
    log.info(f"  建议仓位: {market_state.suggested_position:.0%}")

    # ===== Step 2: 行业分类 =====
    log.info("Step 2/8: 获取行业分类...")
    industry_df = fetch_industry_classification()
    if not industry_df.empty:
        if "code" in industry_df.columns and "板块名称" in industry_df.columns:
            industry_map = industry_df.set_index("code")["板块名称"]
        else:
            cols = industry_df.columns.tolist()
            possible_code = [c for c in cols if "code" in c.lower() or "代码" in c]
            possible_ind = [c for c in cols if "板块" in c or "行业" in c or "industry" in c.lower()]
            if possible_code and possible_ind:
                industry_map = industry_df.set_index(possible_code[0])[possible_ind[0]]
            else:
                industry_map = pd.Series("未知", index=all_codes)
    else:
        industry_map = pd.Series("未知", index=all_codes)

    # ===== Step 3: 估值数据 + 硬过滤 + 基本面初筛 =====
    log.info("Step 3/8: 估值数据 + 风险过滤 + 基本面打分...")
    valuation_df = fetch_valuation_today()
    if valuation_df.empty:
        log.warning("无法获取估值数据，退出")
        return [], {"total": len(all_codes), "after_filter": 0, "after_risk": 0,
                     "final_count": 0, "elapsed": time.time() - t0,
                     "top_score": 0, "threshold_met": False}

    # 风险过滤
    bl = Blacklist(str(get_base_dir() / "blacklist.json"))
    filtered_codes = apply_hard_filters(
        valuation_df.index.tolist(), valuation_df, config, blacklist=bl.codes,
    )
    valuation_df = valuation_df.loc[valuation_df.index.intersection(filtered_codes)]
    log.info(f"  硬过滤后: {len(valuation_df)} 只")

    # 批量获取财务数据（一次调用拿全市场）
    indicators_df, financial_df = fetch_all_bulk_financials()
    fundamental_scores = compute_fundamental_scores(valuation_df, indicators_df, financial_df, industry_map)
    log.info(f"  基本面打分: {len(fundamental_scores)} 只")

    top200 = fundamental_scores.nlargest(200, "fundamental_total").index.tolist()

    # ===== Step 4: 行情 + 技术面 =====
    log.info(f"Step 4/8: 行情数据 + 技术面打分 (前{len(top200)}只)...")
    market_df = fetch_all_daily_hist(top200, start_date="20250101", end_date=target_date.replace("-", ""))
    if market_df.empty:
        # 无行情数据 → NaN，让融合引擎重分配技术面权重
        technical_scores = pd.DataFrame({"technical_total": float("nan")}, index=fundamental_scores.index)
    else:
        technical_scores = compute_technical_scores(market_df)

    # ===== Step 5: 资金面 + 行业面 =====
    log.info("Step 5/8: 资金面 + 行业面打分...")
    all_codes_scored = fundamental_scores.index.tolist()
    capital_scores = compute_capital_scores(all_codes_scored)
    industry_scores = compute_industry_scores(all_codes_scored, industry_map)

    # ===== Step 6: 消息面 + 催化剂 =====
    log.info("Step 6/8: 消息面 + 催化剂打分...")
    news_scores = compute_news_scores(all_codes_scored, code_to_name)
    catalyst_scores = compute_catalyst_scores(all_codes_scored)

    # ===== Step 7: 融合排名 =====
    log.info("Step 7/8: 多维度融合排名...")
    composite = compute_composite_score(
        fundamental_scores, technical_scores, capital_scores, industry_scores,
        news_scores=news_scores, catalyst_scores=catalyst_scores,
        regime_score=market_state.temperature,
        weights=adjusted_weights,
    )

    # 注入最新收盘价（回测和展示用）
    if not market_df.empty and "close" in market_df.columns:
        latest_close = market_df.groupby("code")["close"].last()
        composite["close_price"] = latest_close.reindex(composite.index)
    # 始终返回 Top N 的最高分股票，min_score 只影响置信度标签
    top_stocks = rank_stocks(composite, top_n=top_n, min_score=0.0)
    top_stocks_filtered = rank_stocks(composite, top_n=top_n, min_score=min_score)

    # ===== Step 8: AI 分析 (Top stocks) =====
    log.info("Step 8/8: AI 投资逻辑生成...")
    ai_cfg = config.get("ai", {})
    ai_client = get_ai_client(
        provider=ai_cfg.get("provider", "none"),
        api_key=ai_cfg.get("api_key", ""),
        model=ai_cfg.get("model", ""),
    )

    elapsed = time.time() - t0

    # ===== 输出 =====
    print(f"\n  ── 市场环境 ───────────────────────────────────────")
    print(f"  温度: {market_state.temperature:.0f}/100  {market_state.regime}")
    print(f"  建议仓位: {market_state.suggested_position:.0%}")
    for name, info in market_state.details.items():
        print(f"    {name}: {info.get('close', '-')}  {info.get('trend', '-')}  {info.get('ret_60d', '-')}")

    # 始终显示最高分股票（即使没达到阈值）
    display_stocks = top_stocks_filtered if not top_stocks_filtered.empty else top_stocks
    if display_stocks.empty:
        print_no_results(min_score)
    else:
        if top_stocks_filtered.empty:
            print(f"\n  ⚠ 无股票达到最低分数阈值 ({min_score})，以下为最高分标的:")
        for i, (code, row) in enumerate(display_stocks.iterrows(), 1):
            name = code_to_name.get(code, code)
            ind = str(industry_map.get(code, "未知"))

            # 生成投资逻辑
            score_card = row.to_dict()
            score_card["code"] = code
            score_card["name"] = name
            thesis = ai_client.generate_thesis(score_card) if ai_cfg.get("features", {}).get("thesis_generation") else ""

            risks = ai_client.assess_risk(score_card) if ai_cfg.get("features", {}).get("risk_assessment") else []

            # 推荐周期
            fund = score_card.get("fundamental_total", 50)
            tech = score_card.get("technical_total", 50)
            cycle = determine_cycle(fund, tech)

            print_stock_card(i, code, name, ind, row, thesis=thesis, risks=risks, cycle=cycle)

    # final_count 用达标数（非显示数）
    filtered_count = len(top_stocks_filtered) if not top_stocks_filtered.empty else 0
    print_summary(
        total_stocks=len(all_codes),
        after_filter=len(valuation_df),
        after_risk=len(fundamental_scores),
        final_count=filtered_count,
        elapsed_seconds=elapsed,
    )

    # 统计信息与结果分开返回
    stats = {
        "total": len(all_codes),
        "after_filter": len(valuation_df),
        "after_risk": len(fundamental_scores),
        "final_count": filtered_count,
        "elapsed": elapsed,
        "top_score": float(composite["final_score"].iloc[0]) if len(composite) > 0 else 0,
        "threshold_met": not top_stocks_filtered.empty,
    }
    display = display_stocks if not display_stocks.empty else top_stocks
    results = display.to_dict("records") if not display.empty else []
    return results, stats


def main():
    parser = argparse.ArgumentParser(description="A股智能选股系统 V2.0")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--date", default=None, help="选股日期 YYYY-MM-DD")
    parser.add_argument("--top", type=int, default=None, help="输出前N只")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    parser.add_argument("--ai", default=None, help="AI提供商 (openai/claude/gemini/deepseek/local)")
    parser.add_argument("--cli", action="store_true", help="命令行模式（默认启动GUI）")
    parser.add_argument("--backtest", action="store_true", help="运行回测")
    parser.add_argument("--start", default="2024-01-01", help="回测起始日期")
    parser.add_argument("--end", default="2025-12-31", help="回测结束日期")
    parser.add_argument("--eval-factors", action="store_true", help="运行因子评价")
    parser.add_argument("--optimize", action="store_true", help="权重参数优化")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config = load_config(args.config)
    if args.ai:
        config["ai"]["provider"] = args.ai

    # CLI 模式（--cli 或带了命令行专属参数）
    cli_mode = args.cli or args.backtest or args.eval_factors or args.optimize

    if cli_mode:
        _run_cli_mode(config, args)
    else:
        _run_gui_mode(config)


def _run_cli_mode(config, args):
    """命令行模式."""
    # 回测模式
    if args.backtest:
        from backtest import run_backtest
        log.info(f"回测模式: {args.start} → {args.end}")
        result = run_backtest(config, args.start, args.end,
                              screening_fn=run_screening, top_n=args.top or 2)
        print(result["metrics"].summary())
        if args.verbose and result["trades"]:
            for t in result["trades"]:
                print(f"  {t.code} | {t.entry_date}→{t.exit_date} | "
                      f"{t.pnl_pct:+.1%} | 持有{t.hold_days}天 | {t.reason}")
        _wait_and_exit()

    if args.eval_factors:
        from eval import run_factor_evaluation
        log.info("因子评价模式")
        log.warning("因子评价需在回测后运行，或提供历史因子得分文件")
        _wait_and_exit()

    if args.optimize:
        from backtest.optimizer import grid_search_weights
        log.info("权重优化模式")

        def objective(cfg):
            from backtest import run_backtest as rb
            result = rb(cfg, "2024-01-01", "2024-12-31",
                        screening_fn=run_screening, top_n=2)
            return result["metrics"].sharpe

        df = grid_search_weights(config, objective)
        print("\n最优权重 Top 10:")
        print(df.head(10).to_string(index=False))
        _wait_and_exit()

    results, stats = run_screening(config, date=args.date, top_n=args.top)
    if not results:
        log.info("今日无符合条件的标的")
    _wait_and_exit()


def _gui_excepthook(exc_type, exc_value, tb):
    """全局异常捕获 — 弹窗显示错误."""
    import traceback
    from PyQt6.QtWidgets import QMessageBox
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, tb))
    QMessageBox.critical(None, "程序错误", f"发生未捕获的异常:\n\n{tb_str}")


def _run_gui_mode(config):
    """GUI 模式 — PyQt6 桌面程序."""
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from ui import MainWindow
    except ImportError as e:
        log.error(f"PyQt6 未安装: {e}")
        log.info("请运行: pip install PyQt6")
        log.info("或使用 CLI 模式: python main.py --cli")
        _wait_and_exit()
        return

    app = QApplication(sys.argv)
    app.setApplicationName("A股智能选股系统")

    # 全局异常捕获
    sys.excepthook = _gui_excepthook

    try:
        window = MainWindow(config)
        window.show()
        log.info("GUI 已启动")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        QMessageBox.critical(None, "启动错误", f"GUI 启动失败:\n\n{tb}")
        _wait_and_exit()
        return

    sys.exit(app.exec())


def _wait_and_exit():
    if getattr(sys, 'frozen', False):
        print()
        input("按 Enter 键退出...")
    sys.exit(0)


if __name__ == "__main__":
    main()
