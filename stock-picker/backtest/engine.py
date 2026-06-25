"""回测主引擎 — 逐日循环."""
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from .simulator import Simulator, Position, Trade
from .metrics import compute_metrics, MetricsReport

log = logging.getLogger(__name__)


class BacktestEngine:
    """回测主引擎.

    逐日运行选股逻辑 → 模拟T+1成交 → 跟踪持仓 → 执行卖出规则 → 记录收益.
    """

    def __init__(self, config: dict):
        self.config = config
        self.sim: Simulator | None = None
        self.daily_signals: dict[str, list[str]] = {}
        self.daily_scores: dict[str, pd.DataFrame] = {}

    def run(
        self,
        start_date: str,
        end_date: str,
        screening_fn,  # callable: (config, date, top_n) -> list[dict]
        exit_check_fn=None,  # callable: (positions, prices, config) -> signals
        top_n: int = 2,
        initial_cash: float = 1_000_000,
    ) -> dict:
        """运行回测.

        Args:
            start_date: 起始日期
            end_date: 终止日期
            screening_fn: 选股函数，返回 [{"code": ..., "final_score": ...}, ...]
            exit_check_fn: 卖出检查函数
            top_n: 每日买入数量
            initial_cash: 初始资金

        Returns:
            {metrics: MetricsReport, trades: list[Trade], equity_curve: DataFrame}
        """
        bt_cfg = self.config.get("backtest", {})
        commission = bt_cfg.get("commission_rate", 0.00025)
        stamp = bt_cfg.get("stamp_tax_rate", 0.001)
        slippage = bt_cfg.get("slippage_pct", 0.001)

        self.sim = Simulator(
            initial_cash=initial_cash,
            commission=commission,
            stamp_tax=stamp,
            slippage=slippage,
        )

        self.daily_signals = {}
        dates = pd.date_range(start_date, end_date, freq="B")
        positions_per_day: list[dict] = []

        for i, date in enumerate(dates):
            date_str = date.strftime("%Y-%m-%d")
            log.info(f"回测进度: {date_str} ({i + 1}/{len(dates)})")

            # 1. 检查卖出条件
            if exit_check_fn:
                open_positions = self.sim.get_open_positions()
                # 构建当前价格映射
                prices = {p.code: p.entry_price for p in open_positions}
                signals = exit_check_fn(open_positions, prices, self.config)
                for code, signal in signals.items():
                    if signal.triggered:
                        pos = self.sim.positions.get(code)
                        if pos:
                            sell_qty = pos.remaining * signal.sell_ratio
                            sell_price = prices.get(code, pos.entry_price)
                            self.sim.place_order(code, "SELL", sell_qty, sell_price,
                                                 date_str, reason=signal.reason)

            # 2. 筛选新标的
            try:
                ret = screening_fn(self.config, date=date_str, top_n=top_n)
                results = ret[0] if isinstance(ret, tuple) else ret
            except Exception as e:
                log.warning(f"{date_str} 选股失败: {e}")
                results = []

            self.daily_signals[date_str] = [r["code"] for r in results] if results else []

            # 3. T+1 买入（用当天收盘价模拟）
            if results and len(self.sim.get_open_positions()) < top_n:
                slots = top_n - len(self.sim.get_open_positions())
                cash_per_slot = self.sim.cash / max(slots, 1) * 0.95  # 留5%缓冲

                for r in results[:slots]:
                    code = r["code"]
                    price = r.get("price", 100.0)  # 估价
                    qty = cash_per_slot / (price * (1 + commission))
                    self.sim.place_order(code, "BUY", qty, price, date_str,
                                         reason=f"选股排名#{r.get('rank', '?')}")

            # 4. 记录
            self.sim.record_equity(date_str)
            positions_per_day.append({
                "date": date_str,
                "positions": len(self.sim.get_open_positions()),
                "equity": self.sim.equity,
                "cash": self.sim.cash,
            })

        # 清理未平仓
        if self.sim.get_open_positions():
            last_date = dates[-1].strftime("%Y-%m-%d")
            for pos in self.sim.get_open_positions():
                self.sim.place_order(pos.code, "SELL", pos.remaining, pos.entry_price,
                                     last_date, reason="回测结束平仓")

        # 计算指标
        equity_curve = pd.DataFrame(self.sim.equity_history)
        metrics = compute_metrics(
            trades=self.sim.trades,
            equity_curve=equity_curve,
            initial_cash=initial_cash,
            total_days=len(dates),
        )

        return {
            "metrics": metrics,
            "trades": self.sim.trades,
            "equity_curve": equity_curve,
            "positions_daily": pd.DataFrame(positions_per_day),
        }


def run_backtest(
    config: dict,
    start_date: str,
    end_date: str,
    screening_fn,
    **kwargs,
) -> dict:
    """便捷回测入口."""
    engine = BacktestEngine(config)
    return engine.run(start_date, end_date, screening_fn, **kwargs)
