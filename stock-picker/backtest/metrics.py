"""回测绩效指标计算."""
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class MetricsReport:
    annual_return: float = 0.0
    cumulative_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe: float = 0.0
    calmar: float = 0.0
    win_rate: float = 0.0
    profit_loss_ratio: float = 0.0
    total_trades: int = 0
    avg_hold_days: float = 0.0
    annual_turnover: float = 0.0
    excess_return: float = 0.0
    volatility: float = 0.0
    final_equity: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        lines = [
            "─" * 50,
            "  回测绩效报告",
            "─" * 50,
            f"  年化收益率:      {self.annual_return:>8.2%}",
            f"  累计收益率:      {self.cumulative_return:>8.2%}",
            f"  最大回撤:        {self.max_drawdown:>8.2%}",
            f"  夏普比率:        {self.sharpe:>8.2f}",
            f"  Calmar 比率:     {self.calmar:>8.2f}",
            f"  胜率:            {self.win_rate:>8.1%}",
            f"  盈亏比:          {self.profit_loss_ratio:>8.2f}",
            f"  总交易次数:      {self.total_trades:>8d}",
            f"  平均持仓天数:     {self.avg_hold_days:>8.0f}天",
            f"  年化波动率:      {self.volatility:>8.2%}",
            "─" * 50,
        ]
        return "\n".join(lines)


def compute_metrics(
    trades: list,
    equity_curve: pd.DataFrame,
    initial_cash: float,
    total_days: int,
) -> MetricsReport:
    """计算所有绩效指标.

    Args:
        trades: Trade 对象列表
        equity_curve: columns: date, equity
        initial_cash: 初始资金
        total_days: 总交易日数
    """
    report = MetricsReport()

    if equity_curve.empty:
        return report

    # 最终权益
    final_equity = equity_curve["equity"].iloc[-1]
    report.final_equity = final_equity

    # 累计收益率
    cum_return = (final_equity - initial_cash) / initial_cash
    report.cumulative_return = cum_return

    # 年化收益率
    if total_days > 0 and cum_return > -1:
        report.annual_return = (1 + cum_return) ** (365.0 / total_days) - 1

    # 最大回撤
    peak = equity_curve["equity"].expanding().max()
    drawdowns = (peak - equity_curve["equity"]) / peak
    report.max_drawdown = drawdowns.max()

    # 日收益率
    daily_returns = equity_curve["equity"].pct_change().dropna()
    if len(daily_returns) > 1:
        daily_vol = daily_returns.std()
        report.volatility = daily_vol * np.sqrt(365)

        if report.volatility > 0:
            report.sharpe = report.annual_return / report.volatility

    if report.max_drawdown > 0:
        report.calmar = report.annual_return / report.max_drawdown

    # 交易统计
    report.total_trades = len(trades)
    if trades:
        winning = [t for t in trades if t.pnl > 0]
        losing = [t for t in trades if t.pnl < 0]

        report.win_rate = len(winning) / len(trades)
        avg_win = np.mean([t.pnl for t in winning]) if winning else 0
        avg_loss = abs(np.mean([t.pnl for t in losing])) if losing else 0.001
        report.profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        report.avg_hold_days = np.mean([t.hold_days for t in trades])

    return report
