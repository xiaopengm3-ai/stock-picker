"""卖出逻辑引擎 — 时间止盈/技术止损/基本面止损/分级减仓."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

PRIORITY_ORDER = [
    "FUNDAMENTAL_STOP",   # 最高优先级
    "TECH_STOP",
    "TRAILING_STOP",
    "PROFIT_TAKING",
    "TIME_STOP",          # 最低优先级
]


@dataclass
class ExitSignal:
    triggered: bool
    reason: str              # 触发原因码
    priority: str            # PRIORITY_ORDER 中的一项
    sell_ratio: float = 1.0  # 卖出比例 (0.0-1.0)
    detail: dict = field(default_factory=dict)


@dataclass
class Position:
    code: str
    name: str
    entry_date: str
    entry_price: float
    quantity: float
    high_since_entry: float  # 持仓期最高价


class ExitEngine:
    """卖出逻辑引擎 — 每日检查持仓的所有卖出条件."""

    def __init__(self, config: dict):
        self.config = config.get("exit", {})
        self.time_stops = self.config.get("time_stop", {})
        self.tech_stops = self.config.get("tech_stop", {})
        self.fund_stops = self.config.get("fundamental_stop", {})
        self.profit_tiers = self.config.get("profit_taking", {}).get("tiers", [
            {"return": 0.10, "sell_ratio": 0.30},
            {"return": 0.20, "sell_ratio": 0.30},
            {"return": 0.30, "sell_ratio": 1.00},
        ])

    def check_all(self, position: Position, market_data: pd.DataFrame,
                  financial_data: dict | None = None) -> ExitSignal:
        """检查所有卖出条件，返回最高优先级的信号."""
        checks = [
            self._check_fundamental_stop,
            self._check_tech_stop,
            self._check_trailing_stop,
            self._check_profit_taking,
            self._check_time_stop,
        ]
        for check_fn in checks:
            signal = check_fn(position, market_data, financial_data)
            if signal.triggered:
                return signal
        return ExitSignal(triggered=False, reason="HOLD", priority="HOLD")

    def _check_fundamental_stop(self, position, market_data, financial_data) -> ExitSignal:
        """基本面止损：业绩恶化30%以上、审计非标."""
        if financial_data is None:
            return ExitSignal(triggered=False, reason="", priority="FUNDAMENTAL_STOP")
        # Phase 2: 占位，检查 financial_data 中的业绩变动
        earnings_decline = financial_data.get("profit_decline_pct", 0)
        if earnings_decline > self.fund_stops.get("earnings_decline_pct", 30):
            return ExitSignal(
                triggered=True, reason="业绩恶化>30%",
                priority="FUNDAMENTAL_STOP", sell_ratio=1.0,
                detail={"earnings_decline": earnings_decline},
            )
        return ExitSignal(triggered=False, reason="", priority="FUNDAMENTAL_STOP")

    def _check_tech_stop(self, position, market_data, financial_data) -> ExitSignal:
        """技术止损：EMA200跌破、死叉、底背离、放量下跌."""
        if market_data.empty or "close" not in market_data.columns:
            return ExitSignal(triggered=False, reason="", priority="TECH_STOP")

        try:
            close = market_data["close"].dropna()
            if len(close) < 60:
                return ExitSignal(triggered=False, reason="", priority="TECH_STOP")

            ema200 = close.ewm(span=200, adjust=False).mean()

            # 跌破 EMA200
            if self.tech_stops.get("ema200_enabled", True):
                if close.iloc[-1] < ema200.iloc[-1]:
                    return ExitSignal(
                        triggered=True, reason="跌破EMA200",
                        priority="TECH_STOP", sell_ratio=1.0,
                        detail={"close": close.iloc[-1], "ema200": ema200.iloc[-1]},
                    )

            # 放量下跌
            if self.tech_stops.get("panic_sell_enabled", True) and "volume" in market_data.columns:
                vol = market_data["volume"].dropna()
                avg_vol = vol.tail(21).head(20).mean()
                last_ret = close.pct_change().iloc[-1]
                vol_ratio = vol.iloc[-1] / (avg_vol + 1e-10)
                threshold = self.tech_stops.get("panic_sell_pct", 0.03)
                vol_mult = self.tech_stops.get("panic_sell_vol_mult", 2.0)
                if last_ret < -threshold and vol_ratio > vol_mult:
                    return ExitSignal(
                        triggered=True, reason=f"放量下跌({last_ret:.1%})",
                        priority="TECH_STOP", sell_ratio=1.0,
                    )

        except Exception:
            pass

        return ExitSignal(triggered=False, reason="", priority="TECH_STOP")

    def _check_trailing_stop(self, position, market_data, financial_data) -> ExitSignal:
        """移动止盈：从持仓最高点回撤 > 8%."""
        if market_data.empty or "close" not in market_data.columns:
            return ExitSignal(triggered=False, reason="", priority="TRAILING_STOP")

        current_price = market_data["close"].iloc[-1]
        peak = max(position.high_since_entry, current_price)
        drawdown = (peak - current_price) / (peak + 1e-10)
        threshold = self.tech_stops.get("trailing_stop_pct", 0.08)

        if drawdown > threshold:
            return ExitSignal(
                triggered=True, reason=f"移动止盈回撤{drawdown:.1%}",
                priority="TRAILING_STOP", sell_ratio=1.0,
                detail={"peak": peak, "current": current_price, "drawdown": drawdown},
            )
        return ExitSignal(triggered=False, reason="", priority="TRAILING_STOP")

    def _check_profit_taking(self, position, market_data, financial_data) -> ExitSignal:
        """分级盈利止盈."""
        if market_data.empty or "close" not in market_data.columns:
            return ExitSignal(triggered=False, reason="", priority="PROFIT_TAKING")

        current_price = market_data["close"].iloc[-1]
        total_return = (current_price - position.entry_price) / position.entry_price

        for tier in sorted(self.profit_tiers, key=lambda t: t["return"]):
            if total_return >= tier["return"]:
                return ExitSignal(
                    triggered=True,
                    reason=f"分级止盈(≥{tier['return']:.0%})",
                    priority="PROFIT_TAKING",
                    sell_ratio=tier["sell_ratio"],
                    detail={"return": total_return, "tier": tier["return"]},
                )
        return ExitSignal(triggered=False, reason="", priority="PROFIT_TAKING")

    def _check_time_stop(self, position, market_data, financial_data) -> ExitSignal:
        """时间止盈：20日/60日/120日."""
        entry_date = pd.to_datetime(position.entry_date)
        today = datetime.now()
        hold_days = (today - entry_date).days

        current_price = market_data["close"].iloc[-1] if not market_data.empty and "close" in market_data.columns else position.entry_price
        total_return = (current_price - position.entry_price) / position.entry_price

        # 120 日硬性到期
        long_days = self.time_stops.get("long_term_days", 120)
        if hold_days >= long_days:
            return ExitSignal(
                triggered=True, reason=f"持有{hold_days}日到期待平仓",
                priority="TIME_STOP", sell_ratio=1.0,
            )

        # 20 日短线 + 收益率达标
        short_days = self.time_stops.get("short_term_days", 20)
        short_return = self.time_stops.get("short_term_return_min", 0.05)
        if hold_days >= short_days and total_return >= short_return:
            return ExitSignal(
                triggered=True, reason=f"短线{hold_days}日达标(≥{short_return:.0%})",
                priority="TIME_STOP", sell_ratio=1.0,
            )

        # 60 日中线 + 收益率达标
        mid_days = self.time_stops.get("medium_term_days", 60)
        mid_return = self.time_stops.get("medium_term_return_min", 0.05)
        if hold_days >= mid_days and total_return >= mid_return:
            return ExitSignal(
                triggered=True, reason=f"中线{hold_days}日达标(≥{mid_return:.0%})",
                priority="TIME_STOP", sell_ratio=1.0,
            )

        return ExitSignal(triggered=False, reason="", priority="TIME_STOP")


def check_exit_conditions(
    positions: list[Position],
    market_data: dict[str, pd.DataFrame],
    config: dict,
) -> dict[str, ExitSignal]:
    """批量检查所有持仓的卖出条件.

    Args:
        positions: 当前持仓列表
        market_data: {code: DataFrame} 各持仓的行情数据
        config: 全局配置

    Returns:
        {code: ExitSignal} 触发了卖出信号的持仓
    """
    engine = ExitEngine(config)
    signals = {}
    for pos in positions:
        data = market_data.get(pos.code, pd.DataFrame())
        signal = engine.check_all(pos, data)
        if signal.triggered:
            signals[pos.code] = signal
    return signals
