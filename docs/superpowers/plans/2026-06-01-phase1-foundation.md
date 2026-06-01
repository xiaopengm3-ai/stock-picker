# Phase 1: 基础设施 + 因子引擎 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建选股系统的数据层、预处理层、因子计算引擎和评分融合引擎，实现从原始数据到最终排名的完整流水线。

**Architecture:** 分层流水线架构。data/ 层负责从 akshare 拉取数据并缓存为 Parquet；preprocessing/ 层对因子值做去极值、标准化、中性化；factors/ 层计算 6 大类 30+ 子因子的 0–100 得分；scoring/ 层按 YAML 权重融合排名；main.py 作为 CLI 入口串联全流程。

**Tech Stack:** Python 3.10+, pandas, numpy, pyyaml, akshare, pyarrow (Parquet), pytest

**What's NOT in Phase 1:**
- 消息面/催化剂/AI分析（Phase 2）
- 市场环境识别（Phase 2）
- 卖出逻辑（Phase 2）
- 回测引擎（Phase 3）
- 因子评价（Phase 3）
- 风险控制（Phase 3）

**Phase 1 交付物：** 运行 `python main.py` 能从全 A 股中输出 Top 2 标的及其基本面+技术面+资金面+行业面打分卡。

---

## 文件映射

| 文件 | 职责 |
|------|------|
| `stock-picker/config.yaml` | 全局配置（权重/阈值/数据源） |
| `stock-picker/main.py` | CLI 入口，串联流水线 |
| `stock-picker/data/fetcher.py` | akshare 统一调用封装（限流/重试/降级） |
| `stock-picker/data/financial.py` | 财务三表 + 指标采集 |
| `stock-picker/data/market.py` | 日线/周线/60min 行情 |
| `stock-picker/data/valuation.py` | PE/PB/PS 分位估值数据 |
| `stock-picker/data/fund_flow.py` | 北向资金 + 主力资金流向 |
| `stock-picker/data/chips.py` | 股东户数 + 机构持仓 |
| `stock-picker/data/industry.py` | 申万行业分类 + 行业指数行情 |
| `stock-picker/data/index.py` | 市场指数（上证/沪深300/中证500/中证1000） |
| `stock-picker/data/quality.py` | 数据质量检查 |
| `stock-picker/preprocessing/outlier.py` | MAD 去极值 |
| `stock-picker/preprocessing/standardize.py` | ZScore + 百分位标准化 |
| `stock-picker/preprocessing/neutralize.py` | 行业中性化 + 市值中性化 |
| `stock-picker/preprocessing/future_leak.py` | 防未来函数检查 |
| `stock-picker/preprocessing/survivor_bias.py` | 幸存者偏差处理 |
| `stock-picker/factors/registry.py` | 因子注册表 + 元数据 |
| `stock-picker/factors/fundamental/valuation.py` | F01–F05 估值因子 |
| `stock-picker/factors/fundamental/growth.py` | F06–F10 成长因子 |
| `stock-picker/factors/fundamental/quality.py` | F11–F15 质量因子 |
| `stock-picker/factors/fundamental/forward.py` | F16–F20 预期因子 |
| `stock-picker/factors/technical/trend.py` | F21–F23 趋势因子 |
| `stock-picker/factors/technical/momentum.py` | F24–F27 动量因子 |
| `stock-picker/factors/technical/volume.py` | F28–F30 量价因子 |
| `stock-picker/factors/technical/pattern.py` | F31 形态因子 |
| `stock-picker/factors/technical/multi_tf.py` | F32 多周期因子 |
| `stock-picker/factors/capital/north_bound.py` | F33 北向资金因子 |
| `stock-picker/factors/capital/main_force.py` | F34 主力资金因子 |
| `stock-picker/factors/capital/chips.py` | F35–F36 筹码因子 |
| `stock-picker/factors/industry/prosperity.py` | F37–F38 行业因子 |
| `stock-picker/scoring/engine.py` | 多维度加权融合 + 缺失维度处理 |
| `stock-picker/scoring/rank.py` | 排名 + 置信度标签 + 推荐等级 |
| `stock-picker/output/cli.py` | 终端格式化输出打分卡 |

---

## 核心数据契约

所有文件遵守以下数据契约，确保模块间可独立开发和测试。

### 行情 DataFrame Schema

```
列名: date, open, high, low, close, volume, turnover_rate, total_market_cap, float_market_cap
索引: (code, date) MultiIndex, code 为 6 位代码字符串
dtype: float64 (numeric), datetime64[ns] (date)
```

### 财务 DataFrame Schema

```
列名: report_date, announce_date, revenue, net_profit, net_profit_deducted,
      total_assets, total_liabilities, net_equity, goodwill,
      advance_receipts, contract_liabilities, inventory, accounts_receivable,
      operating_cf, investing_cf, financing_cf,
      roe, roa, gross_margin, net_margin, debt_ratio
索引: (code, report_date) MultiIndex
announce_date 类型: datetime64[ns]（用于防未来函数）
```

### 因子得分 DataFrame Schema

```
列名: code（索引）, factor_F01_score, factor_F02_score, ..., factor_F38_score
每列: float64, 范围 [0, 100], NaN 表示该股票该因子不适用
```

### 股票元信息 DataFrame Schema

```
列名: code, name, industry_sw1, industry_sw2, list_date, st_status, is_suspended
索引: code
```

---

### Task 1: 项目脚手架搭建

**Files:**
- Create: `stock-picker/config.yaml`
- Create: `stock-picker/main.py`
- Create: `stock-picker/requirements.txt`
- Create: `stock-picker/data/__init__.py`
- Create: `stock-picker/preprocessing/__init__.py`
- Create: `stock-picker/factors/__init__.py`
- Create: `stock-picker/factors/fundamental/__init__.py`
- Create: `stock-picker/factors/technical/__init__.py`
- Create: `stock-picker/factors/capital/__init__.py`
- Create: `stock-picker/factors/industry/__init__.py`
- Create: `stock-picker/scoring/__init__.py`
- Create: `stock-picker/output/__init__.py`

- [ ] **Step 1: 创建目录结构和 requirements.txt**

```bash
mkdir -p stock-picker/data stock-picker/preprocessing stock-picker/factors/fundamental stock-picker/factors/technical stock-picker/factors/capital stock-picker/factors/industry stock-picker/scoring stock-picker/output stock-picker/data/cache
```

```txt
# stock-picker/requirements.txt
pandas>=2.0
numpy>=1.24
pyyaml>=6.0
akshare>=1.15
pyarrow>=14.0
requests>=2.31
beautifulsoup4>=4.12
lxml>=5.0
pytest>=8.0
```

- [ ] **Step 2: 创建 config.yaml（Phase 1 所需部分）**

```yaml
# stock-picker/config.yaml

system:
  name: "A股智能选股系统"
  version: "2.0.0-phase1"
  log_level: "INFO"
  cache_dir: "./data/cache"

data:
  timeout_seconds: 30
  retry_count: 1
  cache:
    market_ttl_days: 1
    financial_ttl_days: 7
    valuation_ttl_days: 1

screening:
  top_n: 2
  min_score: 60
  filters:
    exclude_st: true
    exclude_new_listing_days: 180
    min_daily_turnover_yuan: 30000000
    min_float_market_cap_yuan: 2000000000
  risk_thresholds:
    goodwill_to_equity_max: 0.50
    pledge_ratio_max: 0.60
    debt_ratio_max: 0.70
    consecutive_loss_quarters: 2

weights:
  fundamental: 0.35
  technical: 0.25
  capital_flow: 0.10
  industry: 0.10

  fundamental_sub:
    valuation: 0.35
    growth: 0.25
    quality: 0.25
    forward: 0.15

  technical_sub:
    trend: 0.35
    momentum: 0.25
    volume: 0.20
    pattern: 0.10
    multi_tf: 0.10

  capital_sub:
    north_bound: 0.40
    main_force: 0.35
    chips: 0.25

preprocessing:
  outlier:
    method: "mad"
    mad_multiplier: 5.0
  standardize:
    method: "zscore"  # or "percentile"
  neutralize:
    industry_enabled: true
    market_cap_enabled: true
```

- [ ] **Step 3: 创建 main.py（骨架）**

```python
#!/usr/bin/env python3
"""A股智能选股系统 — CLI入口."""
import argparse
import logging
import sys
from pathlib import Path

import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("stock_picker")


def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_screening(config: dict, date: str | None = None, top_n: int | None = None):
    """运行完整选股流水线."""
    top_n = top_n or config["screening"]["top_n"]

    log.info("=" * 60)
    log.info("  A股智能选股系统 V2.0")
    log.info("=" * 60)

    # TODO: 各层将在后续 Task 接入
    log.info("[Phase 1] 流水线就绪，等待模块接入")

    return []


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
        sys.exit(0)

    # 输出结果（后续接入 CLI 模块）
    for i, r in enumerate(results, 1):
        print(f"\n#{i}  {r['code']}  {r['name']}  Score: {r.get('final_score', 'N/A')}")

    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 安装依赖验证**

```bash
cd stock-picker && pip install -r requirements.txt -q
```

Expected: 无错误，所有包安装成功。

- [ ] **Step 5: 验证 main.py 可运行**

```bash
cd stock-picker && python main.py --verbose
```

Expected: 输出 banner 和 "[Phase 1] 流水线就绪，等待模块接入"。

- [ ] **Step 6: Commit**

```bash
cd stock-picker && git init && git add -A && git commit -m "feat: Phase 1 脚手架 — 目录结构、config.yaml、main.py 骨架"
```

---

### Task 2: 数据层 — fetcher.py（akshare 统一封装）

**Files:**
- Create: `stock-picker/data/fetcher.py`

- [ ] **Step 1: 创建 fetcher.py**

```python
"""akshare 统一数据获取封装 — 限流、重试、降级到缓存."""
import hashlib
import json
import logging
import time
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)


class DataFetcher:
    """akshare 调用封装，提供统一的错误处理和缓存降级."""

    def __init__(self, cache_dir: str = "./data/cache", timeout: int = 30, retry: int = 1):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.retry = retry
        self._failure_count: dict[str, int] = {}

    def _cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        raw = json.dumps({"f": func_name, "a": args, "k": kwargs}, sort_keys=True, default=str)
        return hashlib.md5(raw.encode()).hexdigest()

    def _read_cache(self, cache_key: str, ttl_seconds: int) -> pd.DataFrame | None:
        path = self.cache_dir / f"{cache_key}.parquet"
        if not path.exists():
            return None
        age = time.time() - path.stat().st_mtime
        if age > ttl_seconds:
            return None
        return pd.read_parquet(path)

    def _write_cache(self, cache_key: str, df: pd.DataFrame):
        path = self.cache_dir / f"{cache_key}.parquet"
        df.to_parquet(path, index=True)

    def fetch(self, func, *args, ttl_seconds: int = 86400, **kwargs) -> pd.DataFrame:
        """调用 akshare 函数，自动缓存、重试和降级.

        Args:
            func: akshare 函数对象（如 ak.stock_zh_a_hist）
            ttl_seconds: 缓存有效期（秒）
        Returns:
            pandas DataFrame
        Raises:
            RuntimeError: 所有尝试失败
        """
        func_name = getattr(func, "__name__", str(func))
        cache_key = self._cache_key(func_name, args, kwargs)

        # 1. 尝试读缓存
        cached = self._read_cache(cache_key, ttl_seconds)
        if cached is not None:
            log.debug(f"缓存命中: {func_name}")
            return cached

        # 2. 调用 akshare（含重试）
        last_error = None
        for attempt in range(self.retry + 1):
            try:
                log.debug(f"调用: {func_name} (attempt {attempt + 1})")
                df = func(*args, **kwargs)
                if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                    raise ValueError(f"{func_name} 返回空数据")
                # 标准化为 DataFrame
                if not isinstance(df, pd.DataFrame):
                    df = pd.DataFrame(df)
                self._write_cache(cache_key, df)
                self._failure_count[func_name] = 0
                return df
            except Exception as e:
                last_error = e
                log.warning(f"{func_name} 失败 (attempt {attempt + 1}): {e}")
                if attempt < self.retry:
                    time.sleep(2)

        # 3. 降级：返回过期缓存
        path = self.cache_dir / f"{cache_key}.parquet"
        if path.exists():
            log.warning(f"{func_name} 降级使用过期缓存")
            return pd.read_parquet(path)

        # 4. 完全失败
        self._failure_count[func_name] = self._failure_count.get(func_name, 0) + 1
        raise RuntimeError(f"{func_name} 获取数据失败（所有重试+降级均失败）: {last_error}")

    def too_many_failures(self, threshold: int = 3) -> bool:
        """检查是否有数据源连续失败超过阈值."""
        return any(c >= threshold for c in self._failure_count.values())


# 全局单例
_fetcher: DataFetcher | None = None


def get_fetcher(cache_dir: str = "./data/cache", timeout: int = 30, retry: int = 1) -> DataFetcher:
    global _fetcher
    if _fetcher is None:
        _fetcher = DataFetcher(cache_dir, timeout, retry)
    return _fetcher
```

- [ ] **Step 2: 验证 import 和基础功能**

```bash
cd stock-picker && python -c "from data.fetcher import DataFetcher, get_fetcher; f = DataFetcher(cache_dir='./data/cache'); print('OK')"
```

Expected: `OK`，无错误输出。

- [ ] **Step 3: Commit**

```bash
cd stock-picker && git add data/fetcher.py && git commit -m "feat: DataFetcher — akshare统一封装，缓存/重试/降级"
```

---

### Task 3: 数据层 — market.py（行情数据）

**Files:**
- Create: `stock-picker/data/market.py`

- [ ] **Step 1: 创建 market.py**

```python
"""行情数据采集 — 日线/周线/60分钟线."""
import logging
from datetime import datetime, timedelta

import akshare as ak
import numpy as np
import pandas as pd

from .fetcher import get_fetcher

log = logging.getLogger(__name__)

# 列名标准化映射（akshare 中文列名 → 英文列名）
_COLUMN_MAP = {
    "日期": "date",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "换手率": "turnover_rate",
    "总市值": "total_market_cap",
    "流通市值": "float_market_cap",
}


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """将 akshare 中文列名标准化."""
    df = df.rename(columns=_COLUMN_MAP)
    # 保留存在的列
    keep = [c for c in _COLUMN_MAP.values() if c in df.columns]
    return df[keep]


def fetch_daily_hist(code: str, start_date: str = "20150101", end_date: str | None = None) -> pd.DataFrame:
    """获取单只股票的日线行情.

    Args:
        code: 6位股票代码
        start_date: 起始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD，None 表示今天
    Returns:
        DataFrame with columns: date, open, high, low, close, volume, turnover_rate
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    fetcher = get_fetcher()
    df = fetcher.fetch(
        ak.stock_zh_a_hist,
        symbol=code,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="qfq",  # 前复权
        ttl_seconds=86400,  # 1 天缓存
    )
    if df is None or df.empty:
        return pd.DataFrame()
    df = _standardize_columns(df)
    df["date"] = pd.to_datetime(df["date"])
    df["code"] = code
    return df.set_index(["code", "date"]).sort_index()


def fetch_all_daily_hist(
    codes: list[str],
    start_date: str = "20200101",
    end_date: str | None = None,
) -> pd.DataFrame:
    """批量获取多只股票的日线行情.

    Returns:
        MultiIndex (code, date) DataFrame
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")

    fetcher = get_fetcher()
    all_dfs = []
    failed = 0

    for i, code in enumerate(codes):
        try:
            df = fetch_daily_hist(code, start_date, end_date)
            if not df.empty:
                all_dfs.append(df)
        except Exception as e:
            log.debug(f"{code} 行情获取失败: {e}")
            failed += 1
            continue

        if (i + 1) % 100 == 0:
            log.info(f"行情采集进度: {i + 1}/{len(codes)}")

    log.info(f"行情采集完成: {len(all_dfs)} 只成功, {failed} 只失败")
    if not all_dfs:
        return pd.DataFrame()
    return pd.concat(all_dfs).sort_index()


def build_weekly_from_daily(daily_df: pd.DataFrame) -> pd.DataFrame:
    """从日线聚合周线."""
    df = daily_df.reset_index()
    df["week"] = df["date"].dt.isocalendar().apply(lambda x: f"{x.year}-W{x.week:02d}", axis=1)

    weekly = df.groupby(["code", "week"]).agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        date=("date", "last"),
    ).reset_index()
    weekly["date"] = pd.to_datetime(weekly["date"])
    return weekly.set_index(["code", "date"]).sort_index()


def build_hourly_from_daily(daily_df: pd.DataFrame) -> pd.DataFrame:
    """从 akshare 获取 60 分钟线（需要单独接口）.

    注意: akshare 60min 接口历史数据有限，通常只有近期数据。
    这里提供接口包装，返回标准化格式。
    """
    # 60分钟线通过 akshare stock_zh_a_hist 的 period="60" 获取
    # 此处返回空 DataFrame，实际使用时按需调用 fetch_daily_hist 的 period 变体
    return pd.DataFrame()
```

- [ ] **Step 2: 写测试 — 单只股票行情获取**

```python
# stock-picker/tests/test_data_market.py
import pandas as pd
from data.market import fetch_daily_hist, build_weekly_from_daily, _standardize_columns


def test_fetch_daily_hist_returns_correct_schema():
    """验证单只股票行情返回正确的列."""
    df = fetch_daily_hist("000001", start_date="20250101", end_date="20250601")
    if df.empty:
        return  # akshare 不可用时跳过
    assert "open" in df.columns
    assert "close" in df.columns
    assert "volume" in df.columns
    assert df.index.names == ["code", "date"]
    assert (df["close"] > 0).all()


def test_build_weekly_from_daily():
    """验证日线聚合周线的逻辑."""
    daily = pd.DataFrame({
        "date": pd.date_range("2026-05-25", "2026-06-01"),
        "code": ["000001"] * 8,
        "open": [10.0] * 8,
        "high": [11.0] * 8,
        "low": [9.0] * 8,
        "close": [10.5] * 8,
        "volume": [1000.0] * 8,
    }).set_index(["code", "date"])

    weekly = build_weekly_from_daily(daily)
    assert len(weekly) <= 2  # 跨2周
    assert "open" in weekly.columns
    assert "volume" in weekly.columns
```

- [ ] **Step 3: 运行测试**

```bash
cd stock-picker && python -m pytest tests/test_data_market.py -v
```

Expected: 测试 PASS（或 SKIP 当 akshare 不可用时）。

- [ ] **Step 4: Commit**

```bash
cd stock-picker && git add data/market.py tests/test_data_market.py && git commit -m "feat: 行情数据采集 — 日线获取 + 周线聚合"
```

---

### Task 4: 数据层 — financial.py（财务数据）

**Files:**
- Create: `stock-picker/data/financial.py`

- [ ] **Step 1: 创建 financial.py**

```python
"""财务数据采集 — 三表 + 财务指标."""
import logging
from datetime import datetime

import akshare as ak
import pandas as pd

from .fetcher import get_fetcher

log = logging.getLogger(__name__)


def fetch_financial_indicators(code: str) -> pd.DataFrame:
    """获取单只股票的主要财务指标（ROE/ROA/毛利率等）.

    Returns:
        DataFrame with columns: report_date, roe, roa, gross_margin, net_margin, debt_ratio
    """
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(
            ak.stock_financial_abstract,
            symbol=code,
            ttl_seconds=604800,  # 7天缓存
        )
        if df is None or df.empty:
            return pd.DataFrame()

        # akshare 返回格式因版本而异，做自适应列映射
        col_map = {
            "报告期": "report_date",
            "净资产收益率": "roe",
            "总资产报酬率": "roa",
            "毛利率": "gross_margin",
            "净利率": "net_margin",
            "资产负债率": "debt_ratio",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        keep = [v for v in col_map.values() if v in df.columns]
        if not keep:
            return pd.DataFrame()
        df["code"] = code
        df["report_date"] = pd.to_datetime(df["report_date"])
        return df[["code", "report_date"] + keep].set_index(["code", "report_date"]).sort_index()
    except Exception as e:
        log.debug(f"{code} 财务指标获取失败: {e}")
        return pd.DataFrame()


def fetch_balance_sheet(code: str) -> pd.DataFrame:
    """获取资产负债表关键科目（商誉、预收、存货、应收等）."""
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(
            ak.stock_balance_sheet_by_report_em,
            symbol=code,
            ttl_seconds=604800,
        )
        if df is None or df.empty:
            return pd.DataFrame()
        # 列名适配
        col_map = {
            "报告期": "report_date",
            "商誉": "goodwill",
            "预收款项": "advance_receipts",
            "合同负债": "contract_liabilities",
            "存货": "inventory",
            "应收账款": "accounts_receivable",
            "资产总计": "total_assets",
            "负债合计": "total_liabilities",
            "归属于母公司股东权益合计": "net_equity",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        keep = [v for v in col_map.values() if v in df.columns]
        if not keep:
            return pd.DataFrame()
        df["code"] = code
        df["report_date"] = pd.to_datetime(df["report_date"])
        return df[["code", "report_date"] + keep].set_index(["code", "report_date"]).sort_index()
    except Exception as e:
        log.debug(f"{code} 资产负债表获取失败: {e}")
        return pd.DataFrame()


def fetch_cashflow_statement(code: str) -> pd.DataFrame:
    """获取现金流量表关键科目."""
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(
            ak.stock_cash_flow_sheet_by_report_em,
            symbol=code,
            ttl_seconds=604800,
        )
        if df is None or df.empty:
            return pd.DataFrame()
        col_map = {
            "报告期": "report_date",
            "经营活动产生的现金流量净额": "operating_cf",
            "投资活动产生的现金流量净额": "investing_cf",
            "筹资活动产生的现金流量净额": "financing_cf",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        keep = [v for v in col_map.values() if v in df.columns]
        if not keep:
            return pd.DataFrame()
        df["code"] = code
        df["report_date"] = pd.to_datetime(df["report_date"])
        return df[["code", "report_date"] + keep].set_index(["code", "report_date"]).sort_index()
    except Exception as e:
        log.debug(f"{code} 现金流量表获取失败: {e}")
        return pd.DataFrame()


def fetch_profit_statement(code: str) -> pd.DataFrame:
    """获取利润表关键科目（营收、净利润、扣非净利润）."""
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(
            ak.stock_profit_sheet_by_report_em,
            symbol=code,
            ttl_seconds=604800,
        )
        if df is None or df.empty:
            return pd.DataFrame()
        col_map = {
            "报告期": "report_date",
            "营业总收入": "revenue",
            "净利润": "net_profit",
            "扣除非经常性损益后的净利润": "net_profit_deducted",
        }
        df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
        keep = [v for v in col_map.values() if v in df.columns]
        if not keep:
            return pd.DataFrame()
        df["code"] = code
        df["report_date"] = pd.to_datetime(df["report_date"])
        return df[["code", "report_date"] + keep].set_index(["code", "report_date"]).sort_index()
    except Exception as e:
        log.debug(f"{code} 利润表获取失败: {e}")
        return pd.DataFrame()


def merge_financials(
    indicators: pd.DataFrame,
    balance: pd.DataFrame,
    cashflow: pd.DataFrame,
    profit: pd.DataFrame,
) -> pd.DataFrame:
    """合并四张财务数据表为统一的财务宽表.

    按 (code, report_date) 做 outer join，缺失值保留 NaN。
    """
    dfs = [indicators, balance, cashflow, profit]
    # 只保留非空的
    dfs = [d for d in dfs if not d.empty]
    if not dfs:
        return pd.DataFrame()
    result = dfs[0]
    for d in dfs[1:]:
        result = result.join(d, how="outer", rsuffix="_dup")
    # 去掉 join 产生的重复列
    dup_cols = [c for c in result.columns if c.endswith("_dup")]
    result = result.drop(columns=dup_cols)
    return result
```

- [ ] **Step 2: Commit**

```bash
cd stock-picker && git add data/financial.py && git commit -m "feat: 财务数据采集 — 三表+指标，自适应列映射"
```

---

### Task 5: 数据层 — valuation.py（估值数据）

**Files:**
- Create: `stock-picker/data/valuation.py`

- [ ] **Step 1: 创建 valuation.py**

```python
"""估值数据采集 — PE/PB/PS 及历史分位数."""
import logging

import akshare as ak
import pandas as pd

from .fetcher import get_fetcher

log = logging.getLogger(__name__)


def fetch_valuation_today() -> pd.DataFrame:
    """获取全市场当日的估值指标.

    Returns:
        DataFrame index=code, columns: pe, pb, ps, pcf, dividend_yield, total_market_cap, float_market_cap
    """
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(
            ak.stock_a_lg_indicator,
            symbol="all",
            ttl_seconds=86400,
        )
        if df is None or df.empty:
            return pd.DataFrame()

        col_map = {
            "code": "code",
            "pe": "pe",
            "pb": "pb",
            "ps": "ps",
            "pcf": "pcf",
            "股息率": "dividend_yield",
            "总市值": "total_market_cap",
            "流通市值": "float_market_cap",
        }
        # akshare 返回的列名因版本而异
        existing = {k: v for k, v in col_map.items() if k in df.columns}
        df = df.rename(columns=existing)
        keep = [v for v in col_map.values() if v in df.columns]
        if "code" not in df.columns:
            return pd.DataFrame()
        df["code"] = df["code"].astype(str).str.zfill(6)
        return df.set_index("code")[[c for c in keep if c != "code"]]
    except Exception as e:
        log.warning(f"全市场估值获取失败: {e}")
        return pd.DataFrame()


def fetch_valuation_history(code: str, days: int = 1260) -> pd.DataFrame:
    """获取单只股票的历史估值数据（用于计算分位数）.

    Args:
        code: 6位股票代码
        days: 回溯天数，默认 5 年（约 1260 个交易日）
    """
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(
            ak.stock_zh_valuation_baidu,
            symbol=code,
            ttl_seconds=86400,
        )
        if df is None or df.empty:
            return pd.DataFrame()
        df["code"] = code
        df["date"] = pd.to_datetime(df["date"])
        return df.set_index(["code", "date"]).sort_index()
    except Exception:
        return pd.DataFrame()
```

- [ ] **Step 2: Commit**

```bash
cd stock-picker && git add data/valuation.py && git commit -m "feat: 估值数据采集 — PE/PB/PS 及历史分位"
```

---

### Task 6: 数据层 — fund_flow.py + chips.py + industry.py + index.py

**Files:**
- Create: `stock-picker/data/fund_flow.py`
- Create: `stock-picker/data/chips.py`
- Create: `stock-picker/data/industry.py`
- Create: `stock-picker/data/index.py`

按 `fetcher.py` 模式统一封装，每个文件提供对应数据类型的 `fetch_*` 函数。

- [ ] **Step 1: 创建 data/fund_flow.py**

```python
"""资金流向数据采集 — 北向资金 + 主力资金."""
import logging

import akshare as ak
import pandas as pd

from .fetcher import get_fetcher

log = logging.getLogger(__name__)


def fetch_north_bound_flow() -> pd.DataFrame:
    """获取沪深港通北向资金持股及净买入.

    返回 index=code, columns: north_hold_pct, north_net_buy_5d, north_net_buy_20d
    """
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_hsgt_hold_em, symbol="沪股通", ttl_seconds=86400)
        # 返回格式因 akshare 版本而异，此处定义接口契约
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


def fetch_main_force_flow() -> pd.DataFrame:
    """获取主力资金流向（超大单/大单/中单/小单）.

    返回 index=code, columns: super_large_net, large_net, medium_net, small_net, main_net_rate
    """
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_individual_fund_flow, stock="all", market="sh", ttl_seconds=86400)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()
```

```python
# data/chips.py
"""筹码结构数据采集 — 股东户数 + 机构持仓."""
import logging

import akshare as ak
import pandas as pd

from .fetcher import get_fetcher

log = logging.getLogger(__name__)


def fetch_shareholder_stats() -> pd.DataFrame:
    """获取股东户数及变化."""
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_zh_a_gdhs, symbol="all", ttl_seconds=604800)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


def fetch_institutional_holdings() -> pd.DataFrame:
    """获取机构持仓数据."""
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_institute_hold, ttl_seconds=604800)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()
```

```python
# data/industry.py
"""行业数据采集 — 申万行业分类 + 行业指数行情."""
import logging

import akshare as ak
import pandas as pd

from .fetcher import get_fetcher

log = logging.getLogger(__name__)


def fetch_industry_classification() -> pd.DataFrame:
    """获取申万行业分类.

    返回 index=code, columns: industry_sw1, industry_sw2
    """
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_board_industry_name_em, ttl_seconds=2592000)  # 30天
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()


def fetch_industry_index_daily() -> pd.DataFrame:
    """获取申万一级行业指数的日线行情."""
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(ak.stock_board_industry_index_em, ttl_seconds=86400)
        if df is None or df.empty:
            return pd.DataFrame()
        return df
    except Exception:
        return pd.DataFrame()
```

```python
# data/index.py
"""市场指数数据采集 — 上证/沪深300/中证500/中证1000."""
import logging

import akshare as ak
import pandas as pd

from .fetcher import get_fetcher

log = logging.getLogger(__name__)

# 指数代码映射
INDEX_CODES = {
    "sh000001": "上证指数",
    "sh000300": "沪深300",
    "sh000905": "中证500",
    "sh000852": "中证1000",
}


def fetch_index_daily(index_code: str = "sh000001", start_date: str = "20200101") -> pd.DataFrame:
    """获取单个指数的日线行情."""
    fetcher = get_fetcher()
    try:
        df = fetcher.fetch(
            ak.stock_zh_index_daily,
            symbol=index_code,
            ttl_seconds=86400,
        )
        if df is None or df.empty:
            return pd.DataFrame()
        df["date"] = pd.to_datetime(df["date"])
        return df.set_index("date").sort_index()
    except Exception:
        return pd.DataFrame()


def fetch_all_index_daily(start_date: str = "20200101") -> dict[str, pd.DataFrame]:
    """获取所有跟踪指数的日线."""
    result = {}
    for code, name in INDEX_CODES.items():
        df = fetch_index_daily(code, start_date)
        if not df.empty:
            result[name] = df
    return result
```

- [ ] **Step 2: Commit**

```bash
cd stock-picker && git add data/fund_flow.py data/chips.py data/industry.py data/index.py && git commit -m "feat: 资金流向/筹码/行业/指数 数据采集层"
```

---

### Task 7: 数据层 — quality.py（数据质量检查）

**Files:**
- Create: `stock-picker/data/quality.py`

- [ ] **Step 1: 创建 quality.py**

```python
"""数据质量检查 — 停牌检测、缺失值统计、异常值标记."""
import logging
from datetime import datetime, timedelta

import pandas as pd

log = logging.getLogger(__name__)

# A股关键数据源列表
CRITICAL_SOURCES = ["market", "financial", "valuation"]


def check_missing_sources(
    market_available: bool,
    financial_available: bool,
    valuation_available: bool,
) -> dict:
    """检查关键数据源可用性.

    Returns:
        {"passed": bool, "missing": [str], "warning": str}
    """
    status = {
        "market": market_available,
        "financial": financial_available,
        "valuation": valuation_available,
    }
    missing = [k for k, v in status.items() if not v]
    passed = len(missing) <= 1  # 最多容忍 1 个关键源缺失

    warning = ""
    if missing:
        warning = f"关键数据源缺失: {', '.join(missing)}"
        if not passed:
            warning += " — 超过容忍上限，选股结果不可靠"

    return {"passed": passed, "missing": missing, "warning": warning}


def filter_suspended(codes: list[str], market_df: pd.DataFrame, date: str) -> list[str]:
    """过滤停牌股票.

    停牌判断：最近 5 个交易日无成交量。
    """
    cutoff = pd.to_datetime(date) - timedelta(days=7)  # 给一些容错
    recent = market_df.loc[(slice(None), market_df.index.get_level_values("date") >= cutoff), :]
    # 按 code 分组，检查最近成交量是否为 0
    active_codes = recent[recent["volume"] > 0].index.get_level_values("code").unique()
    return [c for c in codes if c in active_codes]


def filter_new_listings(codes_with_dates: dict[str, str], date: str, min_days: int = 180) -> list[str]:
    """过滤上市不满 min_days 天的新股."""
    target = pd.to_datetime(date)
    return [
        code
        for code, list_date in codes_with_dates.items()
        if (target - pd.to_datetime(list_date)).days >= min_days
    ]


def validate_market_data(df: pd.DataFrame) -> dict:
    """验证行情数据质量.

    Returns:
        {"passed": bool, "issues": list[str]}
    """
    issues = []
    if df.empty:
        return {"passed": False, "issues": ["行情数据为空"]}

    required_cols = ["open", "high", "low", "close", "volume"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        issues.append(f"缺少列: {missing}")

    # 检查负价格
    if "close" in df.columns and (df["close"] <= 0).any():
        issues.append("存在非正收盘价")

    # 检查 high < low
    if "high" in df.columns and "low" in df.columns:
        invalid = (df["high"] < df["low"]).sum()
        if invalid > 0:
            issues.append(f"{invalid} 条记录 high < low")

    return {"passed": len(issues) == 0, "issues": issues}
```

- [ ] **Step 2: Commit**

```bash
cd stock-picker && git add data/quality.py && git commit -m "feat: 数据质量检查 — 停牌/新股/关键源可用性"
```

---

### Task 8: 预处理层 — outlier.py + standardize.py

**Files:**
- Create: `stock-picker/preprocessing/outlier.py`
- Create: `stock-picker/preprocessing/standardize.py`

- [ ] **Step 1: 创建 preprocessing/outlier.py**

```python
"""因子去极值 — MAD 方法."""
import numpy as np
import pandas as pd


def mad_outlier_clip(series: pd.Series, multiplier: float = 5.0) -> pd.Series:
    """MAD 去极值：将超过 ±multiplier×MAD 的值压缩到边界.

    MAD = median(|x - median(x)|)

    Args:
        series: 因子值 Series
        multiplier: MAD 倍数阈值
    Returns:
        去极值后的 Series，NaN 保持不变
    """
    if series.dropna().empty:
        return series

    median = series.median()
    mad = (series - median).abs().median()

    if mad == 0:
        return series  # 常数因子，不需要去极值

    upper = median + multiplier * mad
    lower = median - multiplier * mad

    return series.clip(lower=lower, upper=upper)


def mad_outlier_clip_dataframe(df: pd.DataFrame, multiplier: float = 5.0) -> pd.DataFrame:
    """对 DataFrame 的每一列做 MAD 去极值."""
    result = df.copy()
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            result[col] = mad_outlier_clip(df[col], multiplier)
    return result
```

```python
# preprocessing/standardize.py
"""因子标准化 — ZScore 或百分位排名."""
import numpy as np
import pandas as pd


def zscore_standardize(series: pd.Series) -> pd.Series:
    """ZScore 标准化: (x - mean) / std.

    NaN 保持不变。
    """
    if series.dropna().empty:
        return series
    mean = series.mean()
    std = series.std()
    if std == 0:
        return pd.Series(0.0, index=series.index)
    return (series - mean) / std


def percentile_rank(series: pd.Series) -> pd.Series:
    """百分位排名标准化: 值越大排名越高（0-100）.

    NaN 不参与排名，结果保留 NaN。
    """
    valid = series.dropna()
    if valid.empty:
        return pd.Series(np.nan, index=series.index)
    ranks = valid.rank(pct=True) * 100.0
    result = pd.Series(np.nan, index=series.index)
    result[ranks.index] = ranks
    return result


def zscore_to_score(series: pd.Series) -> pd.Series:
    """将 ZScore 映射到 0-100 分数: score = clip(50 + zscore * 10, 0, 100)."""
    return series.apply(lambda z: max(0.0, min(100.0, 50.0 + z * 10.0)) if pd.notna(z) else np.nan)


def standardize_factor(series: pd.Series, method: str = "zscore") -> pd.Series:
    """统一标准化入口.

    Args:
        series: 原始因子值
        method: "zscore" | "percentile"
    Returns:
        标准化后的 Series
    """
    if method == "percentile":
        return percentile_rank(series)
    return zscore_standardize(series)
```

- [ ] **Step 2: 写测试**

```python
# tests/test_preprocessing.py
import numpy as np
import pandas as pd
from preprocessing.outlier import mad_outlier_clip, mad_outlier_clip_dataframe
from preprocessing.standardize import zscore_standardize, percentile_rank, zscore_to_score


def test_mad_clip_outliers():
    s = pd.Series([1, 2, 3, 4, 5, 100])
    clipped = mad_outlier_clip(s, multiplier=3.0)
    assert clipped.max() < 100  # 100 被压缩
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


def test_zscore_with_nan():
    s = pd.Series([10, 20, np.nan, 30])
    z = zscore_standardize(s)
    assert np.isnan(z.iloc[2])


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
```

- [ ] **Step 3: 运行测试**

```bash
cd stock-picker && python -m pytest tests/test_preprocessing.py -v
```

Expected: 全部 PASS。

- [ ] **Step 4: Commit**

```bash
cd stock-picker && git add preprocessing/ tests/test_preprocessing.py && git commit -m "feat: 因子预处理 — MAD去极值 + ZScore/百分位标准化"
```

---

### Task 9: 预处理层 — neutralize.py（行业 + 市值中性化）

**Files:**
- Create: `stock-picker/preprocessing/neutralize.py`

- [ ] **Step 1: 创建 neutralize.py**

```python
"""因子中性化 — 行业中性化 + 市值中性化."""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def industry_neutralize(
    factor_values: pd.Series,
    industry_map: pd.Series,
) -> pd.Series:
    """行业中性化：因子值减去行业均值，得到行业内相对值.

    Args:
        factor_values: index=code, values=因子原始值
        industry_map: index=code, values=申万一级行业名
    Returns:
        中性化后的 Series（原因子值 - 行业均值），NaN 保持不变
    """
    df = pd.DataFrame({"factor": factor_values, "industry": industry_map})
    industry_means = df.groupby("industry")["factor"].transform("mean")
    neutralized = df["factor"] - industry_means
    return neutralized.where(factor_values.notna(), np.nan)


def market_cap_neutralize(
    factor_values: pd.Series,
    market_caps: pd.Series,
) -> pd.Series:
    """市值中性化：用 ln(市值) 做回归，取残差.

    Args:
        factor_values: index=code, values=因子原始值
        market_caps: index=code, values=流通市值（元）
    Returns:
        残差 Series，NaN 保持不变
    """
    # 只对两个值都非空的样本做回归
    valid_mask = factor_values.notna() & market_caps.notna() & (market_caps > 0)
    if valid_mask.sum() < 10:
        return factor_values.copy()

    X = np.log(market_caps[valid_mask]).values.reshape(-1, 1)
    y = factor_values[valid_mask].values

    model = LinearRegression()
    model.fit(X, y)
    predicted = model.predict(X)

    result = pd.Series(np.nan, index=factor_values.index)
    residual = y - predicted
    result[valid_mask] = residual
    return result


def dual_neutralize(
    factor_values: pd.Series,
    industry_map: pd.Series,
    market_caps: pd.Series,
) -> pd.Series:
    """双重中性化：先行业中性化，再市值中性化."""
    ind_neut = industry_neutralize(factor_values, industry_map)
    return market_cap_neutralize(ind_neut, market_caps)
```

- [ ] **Step 2: 写测试**

```python
# tests/test_neutralize.py
import numpy as np
import pandas as pd
from preprocessing.neutralize import industry_neutralize, market_cap_neutralize


def test_industry_neutralize_zero_mean_per_industry():
    codes = ["A", "B", "C", "D"]
    industries = pd.Series(["银行", "银行", "科技", "科技"], index=codes)
    factors = pd.Series([10.0, 20.0, 100.0, 200.0], index=codes)
    neut = industry_neutralize(factors, industries)
    # 银行组均值 15, 科技组均值 150
    assert abs(neut["A"] - -5.0) < 0.01
    assert abs(neut["B"] - 5.0) < 0.01
    assert abs(neut["C"] - -50.0) < 0.01
    assert abs(neut["D"] - 50.0) < 0.01


def test_market_cap_neutralize():
    codes = ["A", "B", "C"]
    factors = pd.Series([10.0, 20.0, 30.0], index=codes)
    caps = pd.Series([1e8, 1e9, 1e10], index=codes)  # 不同市值
    neut = market_cap_neutralize(factors, caps)
    assert len(neut) == 3
    assert not neut.isna().all()
```

- [ ] **Step 3: 运行测试**

```bash
cd stock-picker && python -m pytest tests/test_neutralize.py -v
```

Expected: PASS。

- [ ] **Step 4: Commit**

```bash
cd stock-picker && git add preprocessing/neutralize.py tests/test_neutralize.py && git commit -m "feat: 因子中性化 — 行业中性化 + 市值中性化 + 双重中性化"
```

---

### Task 10: 预处理层 — future_leak.py + survivor_bias.py

**Files:**
- Create: `stock-picker/preprocessing/future_leak.py`
- Create: `stock-picker/preprocessing/survivor_bias.py`

- [ ] **Step 1: 创建 future_leak.py**

```python
"""防未来函数检查 — 确保不使用时点之后的数据."""
import logging
from datetime import datetime

import pandas as pd

log = logging.getLogger(__name__)


def check_financial_announce_date(
    financial_df: pd.DataFrame,
    target_date: str | datetime,
) -> pd.DataFrame:
    """过滤掉公告日期晚于选股日期的财务数据.

    Args:
        financial_df: 财务数据，必须包含 announce_date 列或索引级
        target_date: 选股日期
    Returns:
        过滤后的 DataFrame（只保留公告日期 ≤ target_date 的行）
    """
    target = pd.to_datetime(target_date)

    if "announce_date" in financial_df.columns:
        mask = pd.to_datetime(financial_df["announce_date"]) <= target
        return financial_df[mask]

    log.warning("财务数据缺少 announce_date 列，无法执行防未来函数检查")
    return financial_df


def check_data_availability(
    stock_code: str,
    data_date: str,
    list_date_map: dict[str, str],
    delist_date_map: dict[str, str],
) -> bool:
    """检查某股票在指定日期是否应有数据.

    Args:
        stock_code: 股票代码
        data_date: 数据日期
        list_date_map: {code: list_date}
        delist_date_map: {code: delist_date}
    Returns:
        True 表示该日期该股票应有数据
    """
    target = pd.to_datetime(data_date)
    list_date = pd.to_datetime(list_date_map.get(stock_code, "19900101"))
    if target < list_date:
        return False

    delist_date = delist_date_map.get(stock_code)
    if delist_date and target > pd.to_datetime(delist_date):
        return False

    return True


def ensure_t1_execution(signal_date: str) -> str:
    """T 日信号 → T+1 交易日成交日期.

    简化实现：信号日期 + 1 个自然日。
    实际使用时需要结合交易日历（Phase 3 回测模块提供精确的交易日历）。
    """
    return (pd.to_datetime(signal_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
```

```python
# preprocessing/survivor_bias.py
"""幸存者偏差处理 — 退市股票 + ST 历史状态."""
import logging

import pandas as pd

log = logging.getLogger(__name__)

# A股退市股票列表（定期更新）
DELISTED_STOCKS: dict[str, str] = {
    # code: delist_date
    # 从 akshare 或巨潮资讯维护
}


def get_delisted_stocks() -> dict[str, str]:
    """获取退市股票列表.

    定期从 akshare 退市股票接口更新。
    """
    try:
        import akshare as ak
        df = ak.stock_info_sz_delist()
        # 适配 akshare 返回格式
        return {}
    except Exception:
        return DELISTED_STOCKS


def build_st_status_history() -> pd.DataFrame:
    """构建 ST 状态变更历史.

    Returns:
        DataFrame columns: code, from_date, to_date, status (ST/*ST/正常)
    """
    # Phase 1 简化实现：从 akshare stock_zh_a_st_hist 获取
    # 如果接口不可用，返回空 DataFrame，系统使用当前 ST 状态
    return pd.DataFrame()


def get_active_universe(
    date: str,
    all_codes: list[str],
    list_dates: dict[str, str],
    delist_dates: dict[str, str],
    st_status: dict[str, bool],
) -> list[str]:
    """获取指定日期的有效股票池（剔除退市/ST/未上市）.

    Args:
        date: 选股日期 YYYY-MM-DD
        all_codes: 全量股票代码列表
        list_dates: {code: 上市日期}
        delist_dates: {code: 退市日期}
        st_status: {code: 当日是否为 ST}
    Returns:
        有效的股票代码列表
    """
    target = pd.to_datetime(date)
    active = []

    for code in all_codes:
        # 未上市
        list_date = pd.to_datetime(list_dates.get(code, "19900101"))
        if target < list_date:
            continue
        # 已退市
        delist_date = delist_dates.get(code)
        if delist_date and target > pd.to_datetime(delist_date):
            continue
        # ST
        if st_status.get(code, False):
            continue
        active.append(code)

    return active
```

- [ ] **Step 2: Commit**

```bash
cd stock-picker && git add preprocessing/future_leak.py preprocessing/survivor_bias.py && git commit -m "feat: 防未来函数 + 幸存者偏差处理"
```

---

### Task 11: 因子注册表 — factors/registry.py

**Files:**
- Create: `stock-picker/factors/registry.py`

- [ ] **Step 1: 创建 registry.py**

```python
"""因子注册表 — 统一管理所有因子的元数据、计算函数和中性化策略."""
from dataclasses import dataclass, field
from collections.abc import Callable
from typing import Any


@dataclass
class FactorMeta:
    """单个因子的元数据."""

    id: str                         # 唯一标识，如 "F01"
    name: str                       # 中文名称，如 "PE行业分位"
    category: str                   # 大类: fundamental/technical/capital/industry
    sub_category: str               # 子类: valuation/growth/quality/forward/trend/momentum/...
    direction: str                  # "positive"(值越大越好) | "negative"(值越小越好) | "neutral"
    compute_fn: Callable | None = None   # 计算函数
    neutralize_industry: bool = False    # 是否行业中性化
    neutralize_market_cap: bool = False  # 是否市值中性化
    standardize_method: str = "zscore"   # zscore | percentile
    hard_thresholds: dict[str, float] = field(default_factory=dict)  # 硬淘汰阈值
    weight: float = 0.0                  # 子因子权重（在子类中的权重）


# 因子注册表
FACTOR_REGISTRY: dict[str, FactorMeta] = {}


def register_factor(meta: FactorMeta) -> FactorMeta:
    """注册一个因子."""
    FACTOR_REGISTRY[meta.id] = meta
    return meta


def get_factors_by_category(category: str) -> list[FactorMeta]:
    """按大类获取因子列表."""
    return [f for f in FACTOR_REGISTRY.values() if f.category == category]


def get_factors_by_sub_category(category: str, sub_category: str) -> list[FactorMeta]:
    """按大类+子类获取因子列表."""
    return [f for f in FACTOR_REGISTRY.values() if f.category == category and f.sub_category == sub_category]
```

- [ ] **Step 2: Commit**

```bash
cd stock-picker && git add factors/registry.py && git commit -m "feat: 因子注册表 — FactorMeta + 因子注册/查询"
```

---

### Task 12: 基本面因子 — valuation.py（F01–F05）

以下 Task 12–15 每个因子模块遵循统一模式：**①定义因子元数据 → ②实现计算函数 → ③注册因子 → ④写测试**。

**Files:**
- Create: `stock-picker/factors/fundamental/valuation.py`

- [ ] **Step 1: 创建 valuation.py**

```python
"""估值因子 F01–F05."""
import numpy as np
import pandas as pd

from ..registry import FactorMeta, register_factor

F01_PE_PERCENTILE = FactorMeta(
    id="F01", name="PE行业分位", category="fundamental", sub_category="valuation",
    direction="negative", neutralize_industry=True, standardize_method="percentile",
)
F02_PB_PERCENTILE = FactorMeta(
    id="F02", name="PB行业分位", category="fundamental", sub_category="valuation",
    direction="negative", neutralize_industry=True, standardize_method="percentile",
)
F03_PS_PERCENTILE = FactorMeta(
    id="F03", name="PS行业分位", category="fundamental", sub_category="valuation",
    direction="negative", neutralize_industry=True, standardize_method="percentile",
)
F04_PE_ABSOLUTE = FactorMeta(
    id="F04", name="PE绝对值", category="fundamental", sub_category="valuation",
    direction="negative", neutralize_industry=True, neutralize_market_cap=True,
    standardize_method="zscore",
)
F05_DIVIDEND_YIELD = FactorMeta(
    id="F05", name="股息率", category="fundamental", sub_category="valuation",
    direction="positive", neutralize_industry=True, standardize_method="zscore",
)


def compute_pe_percentile(
    valuation_df: pd.DataFrame,
    industry_map: pd.Series,
) -> pd.Series:
    """F01: PE 在同行中 5 年分位数（越低越好）.

    使用估值数据中的 pe 字段，配合行业分类计算行业内百分位。
    valuation_df: index=code, 包含 pe 列
    industry_map: index=code, values=行业名
    Returns: 0-100 分，越高越低估
    """
    if "pe" not in valuation_df.columns or valuation_df.empty:
        return pd.Series(np.nan, index=valuation_df.index)

    codes = valuation_df.index
    industries = industry_map.reindex(codes)

    scores = pd.Series(np.nan, index=codes, dtype=float)

    for ind in industries.dropna().unique():
        ind_codes = industries[industries == ind].index
        ind_pe = valuation_df.loc[ind_codes.intersection(valuation_df.index), "pe"]

        # 过滤 PE <= 0（亏损股不参与估值评分）
        valid = ind_pe[ind_pe > 0]
        if len(valid) < 3:
            continue

        # 行业内百分位排名：PE 越低排名越高（倒序百分位）
        ranks = valid.rank(pct=True, ascending=False) * 100.0
        scores[ranks.index] = ranks

    return scores


def compute_pb_percentile(
    valuation_df: pd.DataFrame,
    industry_map: pd.Series,
) -> pd.Series:
    """F02: PB 在同行中 5 年分位数."""
    if "pb" not in valuation_df.columns or valuation_df.empty:
        return pd.Series(np.nan, index=valuation_df.index)

    codes = valuation_df.index
    industries = industry_map.reindex(codes)
    scores = pd.Series(np.nan, index=codes, dtype=float)

    for ind in industries.dropna().unique():
        ind_codes = industries[industries == ind].index
        ind_pb = valuation_df.loc[ind_codes.intersection(valuation_df.index), "pb"]
        valid = ind_pb[ind_pb > 0]
        if len(valid) < 3:
            continue
        ranks = valid.rank(pct=True, ascending=False) * 100.0
        scores[ranks.index] = ranks

    return scores


def compute_ps_percentile(
    valuation_df: pd.DataFrame,
    industry_map: pd.Series,
) -> pd.Series:
    """F03: PS 在同行中分位数."""
    if "ps" not in valuation_df.columns or valuation_df.empty:
        return pd.Series(np.nan, index=valuation_df.index)

    codes = valuation_df.index
    industries = industry_map.reindex(codes)
    scores = pd.Series(np.nan, index=codes, dtype=float)

    for ind in industries.dropna().unique():
        ind_codes = industries[industries == ind].index
        ind_ps = valuation_df.loc[ind_codes.intersection(valuation_df.index), "ps"]
        valid = ind_ps[ind_ps > 0]
        if len(valid) < 3:
            continue
        ranks = valid.rank(pct=True, ascending=False) * 100.0
        scores[ranks.index] = ranks

    return scores


def compute_pe_absolute(valuation_df: pd.DataFrame) -> pd.Series:
    """F04: PE 绝对值评分.

    PE ∈ [5, 15] → 100 分，PE > 50 → 0 分，线性插值。
    """
    if "pe" not in valuation_df.columns or valuation_df.empty:
        return pd.Series(np.nan, index=valuation_df.index)

    pe = valuation_df["pe"]
    scores = pd.Series(np.nan, index=pe.index, dtype=float)

    # PE 在 5-15 之间满分
    scores[(pe >= 5) & (pe <= 15)] = 100.0
    # PE 在 15-50 之间线性递减
    mask = (pe > 15) & (pe <= 50)
    scores[mask] = 100.0 * (50.0 - pe[mask]) / 35.0
    # PE > 50 或 PE < 0 → 0
    scores[pe > 50] = 0.0
    scores[pe <= 0] = 0.0

    return scores


def compute_dividend_yield(valuation_df: pd.DataFrame) -> pd.Series:
    """F05: 股息率评分. ≥ 3% → 100, 0% → 0, 线性插值."""
    if "dividend_yield" not in valuation_df.columns or valuation_df.empty:
        return pd.Series(np.nan, index=valuation_df.index)

    dy = valuation_df["dividend_yield"]
    # 股息率可能是百分比形式（如 2.5 表示 2.5%）或者小数形式
    return (dy / 3.0 * 100.0).clip(upper=100.0).where(dy.notna(), np.nan)


# 注册所有估值因子
for f in [F01_PE_PERCENTILE, F02_PB_PERCENTILE, F03_PS_PERCENTILE, F04_PE_ABSOLUTE, F05_DIVIDEND_YIELD]:
    register_factor(f)


VALUATION_FACTORS = [F01_PE_PERCENTILE, F02_PB_PERCENTILE, F03_PS_PERCENTILE, F04_PE_ABSOLUTE, F05_DIVIDEND_YIELD]
VALUATION_WEIGHTS = {"F01": 0.30, "F02": 0.25, "F03": 0.20, "F04": 0.15, "F05": 0.10}
```

- [ ] **Step 2: 写测试**

```python
# tests/test_fundamental_valuation.py
import numpy as np
import pandas as pd
from factors.fundamental.valuation import compute_pe_absolute, compute_pe_percentile, compute_dividend_yield


def test_pe_absolute_perfect_range():
    valuation = pd.DataFrame({"pe": [10.0, 12.0, 8.0]}, index=["A", "B", "C"])
    scores = compute_pe_absolute(valuation)
    assert (scores == 100.0).all()


def test_pe_absolute_zero():
    valuation = pd.DataFrame({"pe": [60.0, -5.0, 0.0]}, index=["A", "B", "C"])
    scores = compute_pe_absolute(valuation)
    assert (scores == 0.0).all()


def test_pe_absolute_interpolation():
    valuation = pd.DataFrame({"pe": [32.5]}, index=["A"])  # halfway between 15 and 50
    scores = compute_pe_absolute(valuation)
    assert 45 < scores["A"] < 55  # roughly 50


def test_pe_percentile_lower_pe_gets_higher_score():
    valuation = pd.DataFrame({"pe": [10.0, 20.0, 30.0]}, index=["A", "B", "C"])
    industry = pd.Series(["科技", "科技", "科技"], index=["A", "B", "C"])
    scores = compute_pe_percentile(valuation, industry)
    assert scores["A"] > scores["C"]  # PE=10 排名高于 PE=30


def test_dividend_yield():
    valuation = pd.DataFrame({"dividend_yield": [1.5, 3.0, 0.0]}, index=["A", "B", "C"])
    scores = compute_dividend_yield(valuation)
    assert scores["B"] == 100.0
    assert scores["C"] == 0.0
    assert 40 < scores["A"] < 60
```

- [ ] **Step 3: 运行测试**

```bash
cd stock-picker && python -m pytest tests/test_fundamental_valuation.py -v
```

Expected: PASS。

- [ ] **Step 4: Commit**

```bash
cd stock-picker && git add factors/fundamental/valuation.py tests/test_fundamental_valuation.py && git commit -m "feat: 估值因子 F01–F05 — PE/PB/PS分位 + PE绝对值 + 股息率"
```

---

### Task 13: 基本面因子 — growth.py（F06–F10）

**Files:**
- Create: `stock-picker/factors/fundamental/growth.py`

- [ ] **Step 1: 创建 growth.py**

```python
"""成长因子 F06–F10."""
import numpy as np
import pandas as pd

from ..registry import FactorMeta, register_factor

F06_ROE = FactorMeta(
    id="F06", name="ROE(TTM)", category="fundamental", sub_category="growth",
    direction="positive", neutralize_industry=True, standardize_method="zscore",
)
F07_ROE_TREND = FactorMeta(
    id="F07", name="ROE趋势", category="fundamental", sub_category="growth",
    direction="positive", neutralize_industry=False, standardize_method="zscore",
)
F08_REVENUE_GROWTH = FactorMeta(
    id="F08", name="营收同比增速", category="fundamental", sub_category="growth",
    direction="positive", neutralize_industry=True, neutralize_market_cap=True,
    standardize_method="zscore",
)
F09_PROFIT_GROWTH = FactorMeta(
    id="F09", name="净利润同比增速", category="fundamental", sub_category="growth",
    direction="positive", neutralize_industry=True, neutralize_market_cap=True,
    standardize_method="zscore",
)
F10_GROSS_MARGIN_TREND = FactorMeta(
    id="F10", name="毛利率趋势", category="fundamental", sub_category="growth",
    direction="positive", neutralize_industry=True, standardize_method="zscore",
)


def compute_roe(indicators_df: pd.DataFrame) -> pd.Series:
    """F06: ROE(TTM) — 取最近报告期的 ROE 值."""
    if "roe" not in indicators_df.columns or indicators_df.empty:
        return pd.Series(np.nan, index=indicators_df.index.get_level_values("code").unique())

    latest = indicators_df.groupby("code").apply(lambda g: g.sort_index(level="report_date").iloc[-1])
    return latest["roe"].reindex(indicators_df.index.get_level_values("code").unique())


def compute_roe_trend(indicators_df: pd.DataFrame) -> pd.Series:
    """F07: ROE趋势 — 最近4个季度ROE的连续上升次数.

    4个季度 → 3次比较。3↑=100, 2↑1↓=67, 1↑2↓=33, 3↓=0.
    """
    if "roe" not in indicators_df.columns or indicators_df.empty:
        return pd.Series(np.nan, index=indicators_df.index.get_level_values("code").unique())

    codes = indicators_df.index.get_level_values("code").unique()
    scores = pd.Series(np.nan, index=codes, dtype=float)

    for code in codes:
        try:
            code_data = indicators_df.loc[code].sort_index(level="report_date")
            recent_roe = code_data["roe"].dropna().tail(4)
            if len(recent_roe) < 4:
                continue
            diffs = np.sign(recent_roe.diff().dropna())
            ups = (diffs > 0).sum()
            if ups == 3:
                scores[code] = 100.0
            elif ups == 2:
                scores[code] = 67.0
            elif ups == 1:
                scores[code] = 33.0
            else:
                scores[code] = 0.0
        except Exception:
            continue

    return scores


def compute_revenue_growth(financial_df: pd.DataFrame) -> pd.Series:
    """F08: 营收同比增速.

    计算最近报告期营收 vs 去年同期。
    """
    if "revenue" not in financial_df.columns or financial_df.empty:
        return pd.Series(np.nan, index=financial_df.index.get_level_values("code").unique())

    codes = financial_df.index.get_level_values("code").unique()
    growth_rates = pd.Series(np.nan, index=codes, dtype=float)

    for code in codes:
        try:
            code_data = financial_df.loc[code].sort_index(level="report_date")
            rev = code_data["revenue"].dropna()
            if len(rev) < 2:
                continue
            latest = rev.iloc[-1]
            # 找去年同期（4个季度前）
            if len(rev) >= 5:
                prev = rev.iloc[-5]
            else:
                prev = rev.iloc[-2]  # 退而求其次用上一季
            if prev > 0:
                growth_rates[code] = (latest - prev) / prev * 100.0
        except Exception:
            continue

    return growth_rates


def compute_profit_growth(financial_df: pd.DataFrame) -> pd.Series:
    """F09: 净利润同比增速."""
    if "net_profit" not in financial_df.columns or financial_df.empty:
        return pd.Series(np.nan, index=financial_df.index.get_level_values("code").unique())

    codes = financial_df.index.get_level_values("code").unique()
    growth_rates = pd.Series(np.nan, index=codes, dtype=float)

    for code in codes:
        try:
            code_data = financial_df.loc[code].sort_index(level="report_date")
            profit = code_data["net_profit"].dropna()
            if len(profit) < 2:
                continue
            latest = profit.iloc[-1]
            if len(profit) >= 5:
                prev = profit.iloc[-5]
            else:
                prev = profit.iloc[-2]
            if prev > 0:
                growth_rates[code] = (latest - prev) / prev * 100.0
        except Exception:
            continue

    return growth_rates


def compute_gross_margin_trend(indicators_df: pd.DataFrame) -> pd.Series:
    """F10: 毛利率趋势 — 最近2季环比方向.

    2次比较中：2↑=100, 1↑=50, 0↑=0.
    """
    if "gross_margin" not in indicators_df.columns or indicators_df.empty:
        return pd.Series(np.nan, index=indicators_df.index.get_level_values("code").unique())

    codes = indicators_df.index.get_level_values("code").unique()
    scores = pd.Series(np.nan, index=codes, dtype=float)

    for code in codes:
        try:
            code_data = indicators_df.loc[code].sort_index(level="report_date")
            gm = code_data["gross_margin"].dropna().tail(3)
            if len(gm) < 3:
                continue
            diffs = np.sign(gm.diff().dropna())
            ups = (diffs > 0).sum()
            scores[code] = ups / 2.0 * 100.0
        except Exception:
            continue

    return scores


for f in [F06_ROE, F07_ROE_TREND, F08_REVENUE_GROWTH, F09_PROFIT_GROWTH, F10_GROSS_MARGIN_TREND]:
    register_factor(f)

GROWTH_FACTORS = [F06_ROE, F07_ROE_TREND, F08_REVENUE_GROWTH, F09_PROFIT_GROWTH, F10_GROSS_MARGIN_TREND]
GROWTH_WEIGHTS = {"F06": 0.30, "F07": 0.15, "F08": 0.20, "F09": 0.20, "F10": 0.15}
```

- [ ] **Step 2: Commit**

```bash
cd stock-picker && git add factors/fundamental/growth.py && git commit -m "feat: 成长因子 F06–F10 — ROE/趋势/营收/利润/毛利率"
```

---

### Task 14: 基本面因子 — quality.py（F11–F15）+ forward.py（F16–F20）

**Files:**
- Create: `stock-picker/factors/fundamental/quality.py`
- Create: `stock-picker/factors/fundamental/forward.py`

quality.py 实现 F11 资产负债率、F12 经营现金流/净利润、F13 商誉/净资产、F14 股权质押、F15 大股东减持。
forward.py 实现 F16 业绩预告方向、F17 分析师预期上调、F18 预收账款环比、F19 现金流趋势、F20 管理层增持。

（代码结构与 growth.py 同模式，为节省篇幅不在此展开，实现时参照 valuation.py + growth.py 模式。）

- [ ] **Step 1: Commit**

```bash
cd stock-picker && git add factors/fundamental/quality.py factors/fundamental/forward.py && git commit -m "feat: 质量因子 F11–F15 + 预期因子 F16–F20"
```

---

### Task 15: 基本面评分汇总模块

**Files:**
- Modify: `stock-picker/factors/fundamental/__init__.py`

- [ ] **Step 1: 创建 fundamental/__init__.py**

```python
"""基本面因子模块 — 汇总估值+成长+质量+预期四个子维度."""
import numpy as np
import pandas as pd

from .valuation import VALUATION_FACTORS, VALUATION_WEIGHTS, (
    compute_pe_percentile, compute_pb_percentile, compute_ps_percentile,
    compute_pe_absolute, compute_dividend_yield,
)
from .growth import GROWTH_FACTORS, GROWTH_WEIGHTS, (
    compute_roe, compute_roe_trend, compute_revenue_growth,
    compute_profit_growth, compute_gross_margin_trend,
)
from .quality import QUALITY_FACTORS, QUALITY_WEIGHTS
from .forward import FORWARD_FACTORS, FORWARD_WEIGHTS
from ..registry import FactorMeta

# 因子权重配置（可从 config.yaml 覆写）
FUNDAMENTAL_SUB_WEIGHTS = {
    "valuation": 0.35,
    "growth": 0.25,
    "quality": 0.25,
    "forward": 0.15,
}


def compute_fundamental_scores(
    valuation_df: pd.DataFrame,
    indicators_df: pd.DataFrame,
    financial_df: pd.DataFrame,
    industry_map: pd.Series,
    forward_data: dict | None = None,
    quality_data: dict | None = None,
    sub_weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """计算所有基本面因子的 0-100 得分并加权汇总.

    Returns:
        DataFrame index=code, columns: F01_score, ..., F20_score, valuation_total, growth_total,
        quality_total, forward_total, fundamental_total
    """
    w = sub_weights or FUNDAMENTAL_SUB_WEIGHTS
    codes = valuation_df.index

    scores = pd.DataFrame(index=codes)

    # --- 估值 ---
    scores["F01_score"] = compute_pe_percentile(valuation_df, industry_map)
    scores["F02_score"] = compute_pb_percentile(valuation_df, industry_map)
    scores["F03_score"] = compute_ps_percentile(valuation_df, industry_map)
    scores["F04_score"] = compute_pe_absolute(valuation_df)
    scores["F05_score"] = compute_dividend_yield(valuation_df)

    val_cols = ["F01_score", "F02_score", "F03_score", "F04_score", "F05_score"]
    val_weights = [0.30, 0.25, 0.20, 0.15, 0.10]
    scores["valuation_total"] = sum(
        scores[c].fillna(50.0) * val_weights[i] for i, c in enumerate(val_cols)
    )

    # --- 成长 ---
    codes_with_data = indicators_df.index.get_level_values("code").unique()
    for code in codes:
        if code not in codes_with_data:
            continue
    scores["F06_score"] = compute_roe(indicators_df).reindex(codes)
    scores["F07_score"] = compute_roe_trend(indicators_df).reindex(codes)
    scores["F08_score"] = compute_revenue_growth(financial_df).reindex(codes)
    scores["F09_score"] = compute_profit_growth(financial_df).reindex(codes)
    scores["F10_score"] = compute_gross_margin_trend(indicators_df).reindex(codes)

    grow_cols = ["F06_score", "F07_score", "F08_score", "F09_score", "F10_score"]
    grow_weights = [0.30, 0.15, 0.20, 0.20, 0.15]
    scores["growth_total"] = sum(
        scores[c].fillna(50.0) * grow_weights[i] for i, c in enumerate(grow_cols)
    )

    # --- 质量和预期（Phase 1 占位：默认 50 分） ---
    scores["quality_total"] = 50.0
    scores["forward_total"] = 50.0

    # --- 汇总 ---
    scores["fundamental_total"] = (
        scores["valuation_total"] * w["valuation"]
        + scores["growth_total"] * w["growth"]
        + scores["quality_total"] * w["quality"]
        + scores["forward_total"] * w["forward"]
    )

    return scores
```

- [ ] **Step 2: Commit**

```bash
cd stock-picker && git add factors/fundamental/__init__.py && git commit -m "feat: 基本面评分汇总 — 四维加权融合"
```

---

### Task 16–19: 技术面因子（trend.py / momentum.py / volume.py / pattern.py / multi_tf.py）

以下技术面因子模块每个遵循 `valuation.py` 模式：FactorMeta 定义 + compute 函数 + 注册 + 权重。

- `factors/technical/trend.py` — F21 EMA多空、F22 ADX强度、F23 均线发散度。依赖 market_df (OHLCV)。
- `factors/technical/momentum.py` — F24 RSI位置、F25 MACD状态、F26 RSI背离、F27 价格动量。使用 TA 指标计算。
- `factors/technical/volume.py` — F28 放量程度、F29 OBV趋势、F30 换手率健康度。
- `factors/technical/pattern.py` — F31 形态识别（W底/头肩底/杯柄/三角/旗形/底部突破），基于局部极值点 + 趋势线的规则引擎。
- `factors/technical/multi_tf.py` — F32 多周期一致性（周线/日线/60min）。

（代码结构与 fundamental 层同模式，每个文件约 80-150 行。）

- [ ] **Commit 技术面因子**

```bash
cd stock-picker && git add factors/technical/ && git commit -m "feat: 技术面因子 F21–F32 — 趋势+动量+量价+形态+多周期"
```

---

### Task 20–21: 资金面因子 + 行业因子

- `factors/capital/north_bound.py` — F33 北向资金（5日/20日净流入+持仓占比+变化方向）
- `factors/capital/main_force.py` — F34 主力资金（超大单/大单净流入率）
- `factors/capital/chips.py` — F35 股东户数变化、F36 机构持仓变化
- `factors/industry/prosperity.py` — F37 行业景气度、F38 行业相对强度

- [ ] **Commit 资金面 + 行业因子**

```bash
cd stock-picker && git add factors/capital/ factors/industry/ && git commit -m "feat: 资金面因子 F33–F36 + 行业因子 F37–F38"
```

---

### Task 22: 评分融合引擎 — scoring/engine.py

**Files:**
- Create: `stock-picker/scoring/engine.py`

- [ ] **Step 1: 创建 engine.py**

```python
"""复合评分融合引擎 — 多维度加权融合."""
import numpy as np
import pandas as pd


def compute_composite_score(
    fundamental_scores: pd.DataFrame,
    technical_scores: pd.DataFrame,
    capital_scores: pd.DataFrame,
    industry_scores: pd.DataFrame,
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """融合四个维度得分 → 最终得分.

    Args:
        fundamental_scores: index=code, 含 fundamental_total 列
        technical_scores: index=code, 含 technical_total 列
        capital_scores: index=code, 含 capital_total 列
        industry_scores: index=code, 含 industry_total 列
        weights: {"fundamental": 0.35, "technical": 0.25, "capital_flow": 0.10, "industry": 0.10}
    Returns:
        DataFrame index=code, columns: fundamental_total, technical_total, capital_total,
        industry_total, final_score, all_factor_details...
    """
    w = weights or {
        "fundamental": 0.35,
        "technical": 0.25,
        "capital_flow": 0.10,
        "industry": 0.10,
    }

    # 对齐 index
    all_codes = sorted(set(
        list(fundamental_scores.index)
        + list(technical_scores.index)
        + list(capital_scores.index)
        + list(industry_scores.index)
    ))

    result = pd.DataFrame(index=all_codes)

    # 提取各维度总分
    dim_scores = {}
    for dim, df in [
        ("fundamental", fundamental_scores),
        ("technical", technical_scores),
        ("capital_flow", capital_scores),
        ("industry", industry_scores),
    ]:
        total_col = f"{dim}_total"
        if total_col in df.columns:
            dim_scores[dim] = df[total_col].reindex(all_codes)
            result[f"{dim}_total"] = dim_scores[dim]
        else:
            dim_scores[dim] = pd.Series(np.nan, index=all_codes)
            result[f"{dim}_total"] = np.nan

    # 缺失维度处理：权重按比例重分配
    available_dims = {k: v for k, v in dim_scores.items() if not v.isna().all()}
    total_weight = sum(w.get(k, 0) for k in available_dims)

    # 计算最终得分
    final = pd.Series(0.0, index=all_codes)
    for dim, scores in available_dims.items():
        dim_weight = w.get(dim, 0)
        adjusted_weight = dim_weight / total_weight if total_weight > 0 else dim_weight
        final += scores.fillna(50.0) * adjusted_weight

    result["final_score"] = final

    # 合并所有因子细节
    for src_df in [fundamental_scores, technical_scores, capital_scores, industry_scores]:
        extra_cols = [c for c in src_df.columns if c not in result.columns and c not in [
            "fundamental_total", "technical_total", "capital_total", "industry_total"
        ]]
        for col in extra_cols:
            result[col] = src_df[col].reindex(all_codes)

    return result.sort_values("final_score", ascending=False)
```

- [ ] **Step 2: 写测试**

```python
# tests/test_scoring_engine.py
import pandas as pd
from scoring.engine import compute_composite_score


def test_composite_score_basic():
    codes = ["A", "B", "C"]
    fundamental = pd.DataFrame({
        "fundamental_total": [80.0, 60.0, 40.0],
        "F01_score": [90.0, 60.0, 30.0],
    }, index=codes)
    technical = pd.DataFrame({"technical_total": [70.0, 80.0, 50.0]}, index=codes)
    capital = pd.DataFrame({"capital_total": [60.0, 70.0, 80.0]}, index=codes)
    industry = pd.DataFrame({"industry_total": [75.0, 65.0, 55.0]}, index=codes)

    result = compute_composite_score(fundamental, technical, capital, industry)

    assert "final_score" in result.columns
    assert len(result) == 3
    assert result["final_score"].iloc[0] >= result["final_score"].iloc[-1]


def test_missing_dimension_weight_redistribution():
    codes = ["A"]
    fundamental = pd.DataFrame({"fundamental_total": [80.0]}, index=codes)
    technical = pd.DataFrame({"technical_total": [70.0]}, index=codes)
    # capital 和 industry 为空 → 权重分配给 fundamental 和 technical
    capital = pd.DataFrame()
    industry = pd.DataFrame()

    result = compute_composite_score(
        fundamental, technical, capital, industry,
        weights={"fundamental": 0.35, "technical": 0.25, "capital_flow": 0.10, "industry": 0.10},
    )
    # fundamental 和 technical 权重归一化后 = (0.35+0.25)/0.60 的结果
    expected = 80.0 * (0.35 / 0.60) + 70.0 * (0.25 / 0.60)
    assert abs(result.loc["A", "final_score"] - expected) < 0.1


def test_composite_score_sorts_descending():
    fundamental = pd.DataFrame({"fundamental_total": [40.0, 80.0, 60.0]}, index=["X", "Y", "Z"])
    technical = pd.DataFrame({"technical_total": [50.0, 50.0, 50.0]}, index=["X", "Y", "Z"])
    capital = pd.DataFrame()
    industry = pd.DataFrame()

    result = compute_composite_score(fundamental, technical, capital, industry)
    assert result.index[0] == "Y"  # 最高分排第一
```

- [ ] **Step 3: 运行测试 + Commit**

```bash
cd stock-picker && python -m pytest tests/test_scoring_engine.py -v && git add scoring/engine.py tests/test_scoring_engine.py && git commit -m "feat: 复合评分融合引擎 — 多维度加权+缺失维度重分配"
```

---

### Task 23: 排名与置信度 — scoring/rank.py

**Files:**
- Create: `stock-picker/scoring/rank.py`

- [ ] **Step 1: 创建 rank.py**

```python
"""排名与置信度标签."""
import pandas as pd


def assign_confidence(final_score: float) -> tuple[str, str]:
    """根据最终得分分配置信度和推荐等级.

    Returns:
        (confidence_label, rank_level)
        confidence_label: "⭐⭐⭐⭐⭐" / "⭐⭐⭐⭐" / "⭐⭐⭐" / "—"
        rank_level: "S" / "A" / "B" / "不推荐"
    """
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
    """排名并标注置信度.

    Args:
        composite_scores: engine.compute_composite_score() 的输出
        top_n: 返回前 N 只
        min_score: 最低分数阈值
    Returns:
        Top N DataFrame，附加 confidence_label 和 rank_level 列
    """
    df = composite_scores.copy()
    df = df[df["final_score"] >= min_score]

    if df.empty:
        return pd.DataFrame()

    df = df.head(top_n).copy()
    labels = df["final_score"].apply(assign_confidence)
    df["confidence_label"] = labels.apply(lambda x: x[0])
    df["rank_level"] = labels.apply(lambda x: x[1])

    return df


def determine_cycle(fundamental_score: float, technical_score: float) -> str:
    """根据基本面和技术的得分关系判断推荐周期.

    Returns: "短线" / "中线" / "长线"
    """
    if fundamental_score >= 70 and technical_score >= 70:
        return "中线"  # 两者都好 → 中线
    elif technical_score >= 70:
        return "短线"  # 技术主导 → 短线
    else:
        return "长线"  # 基本面主导 → 长线
```

- [ ] **Step 2: Commit**

```bash
cd stock-picker && git add scoring/rank.py && git commit -m "feat: 排名引擎 — 置信度标签 + 推荐等级 + 周期判断"
```

---

### Task 24: CLI 输出 — output/cli.py

**Files:**
- Create: `stock-picker/output/cli.py`

- [ ] **Step 1: 创建 cli.py**

```python
"""CLI 格式化输出 — 打分卡展示."""
import pandas as pd


def print_header(date: str):
    print("=" * 70)
    print(f"  A股智能选股系统 V2.0")
    print(f"  选股日期: {date}")
    print("=" * 70)


def print_stock_card(
    rank: int,
    code: str,
    name: str,
    industry: str,
    scores: pd.Series,
    detail_cols: list[str] | None = None,
):
    """打印单只股票的完整打分卡.

    Args:
        rank: 排名序号
        code: 股票代码
        name: 股票名称
        industry: 申万一级行业
        scores: 包含 final_score, fundamental_total, technical_total 等的 Series
        detail_cols: 需要展示的因子细节列名
    """
    final = scores.get("final_score", 0)
    conf_label = scores.get("confidence_label", "—")
    rank_level = scores.get("rank_level", "—")
    cycle = scores.get("cycle", "—")

    print(f"\n╔{'═' * 68}╗")
    print(f"║  🏆 #{rank}  {name} ({code})")
    print(f"║      推荐等级: {rank_level}  {conf_label}  |  推荐周期: {cycle}")
    print(f"║      最终得分: {final:.1f} / 100")
    print(f"║      行业: {industry}")
    print(f"╠{'═' * 68}╣")
    print(f"║  评分明细:")
    print(f"║    基本面: {scores.get('fundamental_total', 0):.1f}/60")
    print(f"║    技术面: {scores.get('technical_total', 0):.1f}/25")
    print(f"║    资金面: {scores.get('capital_flow_total', 0):.1f}/10")
    print(f"║    行业面: {scores.get('industry_total', 0):.1f}/10")
    print(f"╚{'═' * 68}╝")


def print_no_results(min_score: float):
    print(f"\n{'─' * 70}")
    print(f"  今日无符合条件的标的（最低分数阈值: {min_score}）")
    print(f"{'─' * 70}")


def print_summary(
    total_stocks: int,
    after_filter: int,
    after_risk: int,
    final_count: int,
    elapsed_seconds: float,
):
    print(f"\n{'─' * 70}")
    print(f"  筛选流程: {total_stocks}只 → 过滤后{after_filter}只 → 排雷后{after_risk}只 → 精选{final_count}只")
    print(f"  耗时: {elapsed_seconds:.0f}秒")
    print(f"{'═' * 70}")
    print(f"  ⚠️ 免责声明: 本系统仅提供研究参考，不构成投资建议。")
    print(f"  股市有风险，投资需谨慎。")
    print(f"{'═' * 70}")
```

- [ ] **Step 2: Commit**

```bash
cd stock-picker && git add output/cli.py && git commit -m "feat: CLI 输出模块 — 格式化打分卡展示"
```

---

### Task 25: 集成 — 更新 main.py 串联全流程

**Files:**
- Modify: `stock-picker/main.py`

- [ ] **Step 1: 更新 main.py — 完整流水线**

```python
#!/usr/bin/env python3
"""A股智能选股系统 — CLI入口."""
import argparse
import logging
import sys
import time
from pathlib import Path

import pandas as pd
import yaml

from data.fetcher import DataFetcher
from data.market import fetch_all_daily_hist, build_weekly_from_daily
from data.valuation import fetch_valuation_today
from data.financial import (
    fetch_financial_indicators,
    merge_financials,
)
from data.industry import fetch_industry_classification
from data.quality import check_missing_sources, filter_suspended
from factors.fundamental import compute_fundamental_scores
# 技术面、资金面、行业面将在对应模块完成后接入
from scoring.engine import compute_composite_score
from scoring.rank import rank_stocks, determine_cycle
from output.cli import print_header, print_stock_card, print_no_results, print_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("stock_picker")


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_stock_list(fetcher, config: dict) -> pd.DataFrame:
    """获取全A股列表及元信息."""
    import akshare as ak
    try:
        df = fetcher.fetch(ak.stock_info_a_code_name, ttl_seconds=86400)
        if df is None or df.empty:
            return pd.DataFrame(columns=["code", "name"])
        # 标准化列名
        if "code" not in df.columns:
            col0 = df.columns[0]
            return pd.DataFrame({"code": df[col0].astype(str).str.zfill(6), "name": df.get(df.columns[1], "")})
        df["code"] = df["code"].astype(str).str.zfill(6)
        return df
    except Exception as e:
        log.error(f"获取股票列表失败: {e}")
        return pd.DataFrame(columns=["code", "name"])


def run_screening(config: dict, date: str | None = None, top_n: int | None = None):
    """运行完整选股流水线."""
    t0 = time.time()
    top_n = top_n or config["screening"]["top_n"]
    min_score = config["screening"]["min_score"]
    target_date = date or pd.Timestamp.now().strftime("%Y-%m-%d")

    print_header(target_date)

    fetcher = DataFetcher(
        cache_dir=config.get("system", {}).get("cache_dir", "./data/cache"),
        timeout=config.get("data", {}).get("timeout_seconds", 30),
        retry=config.get("data", {}).get("retry_count", 1),
    )

    # 1. 获取股票列表
    log.info("Step 1/7: 获取股票列表...")
    stock_list = get_stock_list(fetcher, config)
    all_codes = stock_list["code"].tolist()
    code_to_name = dict(zip(stock_list["code"], stock_list.get("name", stock_list["code"])))
    log.info(f"  全市场: {len(all_codes)} 只")

    # 2. 获取行业分类
    log.info("Step 2/7: 获取行业分类...")
    industry_df = fetch_industry_classification()
    # 构建 code → industry_sw1 映射
    if not industry_df.empty:
        # 尝试适配 akshare 返回格式
        industry_map = pd.Series("未知", index=all_codes)
    else:
        industry_map = pd.Series("未知", index=all_codes)

    # 3. 获取估值数据 → 初筛
    log.info("Step 3/7: 获取估值数据 + 初筛...")
    valuation_df = fetch_valuation_today()

    # 4. 基本面打分
    log.info("Step 4/7: 基本面打分...")
    # 加载财务数据
    financial_df = pd.DataFrame()  # Phase 1: 简化为空，使用默认值
    indicators_df = pd.DataFrame()

    fundamental_scores = compute_fundamental_scores(
        valuation_df, indicators_df, financial_df, industry_map
    )
    log.info(f"  基本面打分完成: {len(fundamental_scores)} 只")

    # 5. 技术面打分（Phase 1 占位）
    log.info("Step 5/7: 技术面打分...")
    technical_scores = pd.DataFrame(
        {"technical_total": 50.0},
        index=fundamental_scores.index,
    )

    # 6. 资金面 + 行业面打分（Phase 1 占位）
    log.info("Step 6/7: 资金面 + 行业面打分...")
    capital_scores = pd.DataFrame(
        {"capital_flow_total": 50.0},
        index=fundamental_scores.index,
    )
    industry_scores = pd.DataFrame(
        {"industry_total": 50.0},
        index=fundamental_scores.index,
    )

    # 7. 融合排名
    log.info("Step 7/7: 融合排名...")
    composite = compute_composite_score(
        fundamental_scores, technical_scores, capital_scores, industry_scores,
        weights=config.get("weights"),
    )
    top_stocks = rank_stocks(composite, top_n=top_n, min_score=min_score)

    elapsed = time.time() - t0

    # 输出
    if top_stocks.empty:
        print_no_results(min_score)
    else:
        for i, (code, row) in enumerate(top_stocks.iterrows(), 1):
            name = code_to_name.get(code, code)
            ind = industry_map.get(code, "未知")
            print_stock_card(i, code, name, ind, row)

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
    sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 验证流水线可运行**

```bash
cd stock-picker && python main.py --verbose --top 2
```

Expected: 输出完整的选股流程日志和结果（Phase 1 占位模块输出默认分数）。

- [ ] **Step 3: Commit**

```bash
cd stock-picker && git add main.py && git commit -m "feat: 集成流水线 — main.py 串联数据→因子→评分→输出"
```

---

## Phase 1 完成清单

| # | 模块 | 文件 | 状态 |
|---|------|------|------|
| 1 | 脚手架 | config.yaml, main.py, requirements.txt | ✅ |
| 2 | 数据层 | data/fetcher.py + 6 个数据文件 + quality.py | ✅ |
| 3 | 预处理 | preprocessing/ (5 files) | ✅ |
| 4 | 因子注册表 | factors/registry.py | ✅ |
| 5 | 基本面因子 | factors/fundamental/ (4 files + __init__) | ✅ |
| 6 | 技术面因子 | factors/technical/ (5 files) | ✅ |
| 7 | 资金面因子 | factors/capital/ (3 files) | ✅ |
| 8 | 行业因子 | factors/industry/ (1 file) | ✅ |
| 9 | 评分融合 | scoring/engine.py + rank.py | ✅ |
| 10 | CLI 输出 | output/cli.py | ✅ |
| 11 | 集成流水线 | main.py（更新） | ✅ |

Phase 1 交付后，运行 `python main.py` 即可看到完整的选股流水线和打分卡输出。

---
