#!/usr/bin/env python3
"""A股智能选股系统 — CLI入口."""
import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from data.fetcher import DataFetcher
from data.valuation import fetch_valuation_today
from data.industry import fetch_industry_classification
from data.quality import check_missing_sources
from data.market import fetch_all_daily_hist

from factors.fundamental import compute_fundamental_scores
from factors.technical import compute_technical_scores
from factors.capital import compute_capital_scores
from factors.industry import compute_industry_scores

from scoring.engine import compute_composite_score
from scoring.rank import rank_stocks
from output.cli import print_header, print_stock_card, print_no_results, print_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("stock_picker")


def get_base_dir() -> Path:
    """获取程序根目录（兼容 PyInstaller 打包）."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def load_config(path: str = "config.yaml") -> dict:
    # 如果传了完整路径就用它，否则在 exe 同目录找
    if not os.path.isabs(path):
        path = str(get_base_dir() / path)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_stock_list(fetcher: DataFetcher) -> pd.DataFrame:
    """获取全A股列表."""
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

    # 1. 获取股票列表
    log.info("Step 1/6: 获取股票列表...")
    stock_list = get_stock_list(fetcher)
    all_codes = stock_list["code"].tolist()
    code_to_name = dict(zip(stock_list["code"], stock_list.get("name", stock_list["code"])))
    log.info(f"  全市场: {len(all_codes)} 只")

    # 2. 获取行业分类
    log.info("Step 2/6: 获取行业分类...")
    industry_df = fetch_industry_classification()
    if not industry_df.empty:
        # 尝试从 akshare 返回格式中提取 code → industry 映射
        if "code" in industry_df.columns and "板块名称" in industry_df.columns:
            industry_map = industry_df.set_index("code")["板块名称"]
        else:
            # 尝试其他列名
            cols = industry_df.columns.tolist()
            possible_code = [c for c in cols if "code" in c.lower() or "代码" in c]
            possible_ind = [c for c in cols if "板块" in c or "行业" in c or "industry" in c.lower()]
            if possible_code and possible_ind:
                industry_map = industry_df.set_index(possible_code[0])[possible_ind[0]]
            else:
                industry_map = pd.Series("未知", index=all_codes)
    else:
        industry_map = pd.Series("未知", index=all_codes)

    # 3. 获取估值数据
    log.info("Step 3/6: 获取估值数据...")
    valuation_df = fetch_valuation_today()
    log.info(f"  估值数据: {len(valuation_df)} 只")

    if valuation_df.empty:
        log.warning("无法获取估值数据，退出")
        return []

    # 4. 获取行情数据（仅用于技术面计算的股票，此处先取 Top 200 估值最低的）
    log.info("Step 4/6: 基本面初筛...")
    # 先做基本面打分，取前200只做技术面精细计算
    financial_df = pd.DataFrame()
    indicators_df = pd.DataFrame()

    fundamental_scores = compute_fundamental_scores(
        valuation_df, indicators_df, financial_df, industry_map,
    )
    log.info(f"  基本面打分: {len(fundamental_scores)} 只")
    top200 = fundamental_scores.nlargest(200, "fundamental_total").index.tolist()

    # 5. 获取行情数据 + 技术面
    log.info(f"Step 5/6: 技术面+资金面+行业面打分 (前 {len(top200)} 只)...")
    market_df = fetch_all_daily_hist(
        top200, start_date="20250101", end_date=target_date.replace("-", ""),
    )
    if market_df.empty:
        log.warning("无法获取行情数据，技术面使用默认值")
        technical_scores = pd.DataFrame(
            {"technical_total": 50.0}, index=fundamental_scores.index,
        )
    else:
        technical_scores = compute_technical_scores(market_df)

    # 6. 资金面 + 行业面
    all_codes_scored = fundamental_scores.index.tolist()
    capital_scores = compute_capital_scores(all_codes_scored)
    industry_scores = compute_industry_scores(all_codes_scored, industry_map)

    # 7. 融合排名
    log.info("Step 6/6: 融合排名...")
    composite = compute_composite_score(
        fundamental_scores, technical_scores, capital_scores, industry_scores,
        weights={
            "fundamental": config["weights"]["fundamental"],
            "technical": config["weights"]["technical"],
            "capital_flow": config["weights"]["capital_flow"],
            "industry": config["weights"]["industry"],
        },
    )
    top_stocks = rank_stocks(composite, top_n=top_n, min_score=min_score)

    elapsed = time.time() - t0

    # 输出
    if top_stocks.empty:
        print_no_results(min_score)
    else:
        for i, (code, row) in enumerate(top_stocks.iterrows(), 1):
            name = code_to_name.get(code, code)
            ind = industry_map.get(code, "未知") if isinstance(industry_map, pd.Series) else "未知"
            if isinstance(ind, pd.Series):
                ind = ind.iloc[0] if len(ind) > 0 else "未知"
            print_stock_card(i, code, name, str(ind), row)

    print_summary(
        total_stocks=len(all_codes),
        after_filter=len(valuation_df),
        after_risk=len(fundamental_scores),
        final_count=len(top_stocks),
        elapsed_seconds=elapsed,
    )

    return top_stocks.to_dict("records") if not top_stocks.empty else []


def main():
    parser = argparse.ArgumentParser(description="A股智能选股系统")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--date", default=None, help="选股日期 YYYY-MM-DD")
    parser.add_argument("--top", type=int, default=None, help="输出前N只")
    parser.add_argument("--verbose", action="store_true", help="详细输出")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config = load_config(args.config)
    results = run_screening(config, date=args.date, top_n=args.top)

    if not results:
        log.info("今日无符合条件的标的")

    # 双击运行时保持窗口不关闭
    if getattr(sys, 'frozen', False):
        print()
        input("按 Enter 键退出...")
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
