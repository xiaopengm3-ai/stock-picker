"""交易模拟器 — 订单、成交、持仓."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Order:
    code: str
    side: str         # "BUY" | "SELL"
    quantity: float
    price: float      # 成交价
    date: str
    reason: str = ""


@dataclass
class Position:
    code: str
    entry_date: str
    entry_price: float
    quantity: float
    peak_price: float = 0.0  # 持仓期间最高价
    sold_quantity: float = 0.0

    @property
    def remaining(self) -> float:
        return self.quantity - self.sold_quantity

    @property
    def is_closed(self) -> bool:
        return self.remaining <= 0


@dataclass
class Trade:
    code: str
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_pct: float
    reason: str
    hold_days: int


class Simulator:
    """回测交易模拟器."""

    def __init__(self, initial_cash: float = 1_000_000, commission: float = 0.00025,
                 stamp_tax: float = 0.001, slippage: float = 0.001):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.commission = commission
        self.stamp_tax = stamp_tax
        self.slippage = slippage
        self.positions: dict[str, Position] = {}
        self.trades: list[Trade] = []
        self.orders: list[Order] = []
        self.equity_history: list[dict] = []

    @property
    def equity(self) -> float:
        position_value = sum(
            p.remaining * p.entry_price for p in self.positions.values() if not p.is_closed
        )
        return self.cash + position_value

    def place_order(self, code: str, side: str, quantity: float, price: float,
                    date: str, reason: str = "") -> Order:
        order = Order(code=code, side=side, quantity=quantity, price=price, date=date, reason=reason)
        self.orders.append(order)
        self._execute(order)
        return order

    def _execute(self, order: Order):
        """执行订单."""
        slippage_mult = (1 + self.slippage) if order.side == "BUY" else (1 - self.slippage)
        exec_price = order.price * slippage_mult
        notional = exec_price * order.quantity
        comm = notional * self.commission

        if order.side == "BUY":
            # 检查资金
            cost = notional + comm
            if cost > self.cash:
                max_qty = self.cash / (exec_price * (1 + self.commission))
                order.quantity = max_qty
                notional = exec_price * order.quantity
                comm = notional * self.commission
                cost = notional + comm

            if order.quantity <= 0:
                return

            self.cash -= cost
            self.positions[order.code] = Position(
                code=order.code,
                entry_date=order.date,
                entry_price=exec_price,
                quantity=order.quantity,
                peak_price=exec_price,
            )

        elif order.side == "SELL":
            if order.code not in self.positions:
                return
            pos = self.positions[order.code]
            qty = min(order.quantity, pos.remaining)
            if qty <= 0:
                return

            notional = exec_price * qty
            comm = notional * self.commission
            stamp = notional * self.stamp_tax

            pnl = (exec_price - pos.entry_price) * qty
            pnl_pct = (exec_price - pos.entry_price) / pos.entry_price if pos.entry_price > 0 else 0

            self.cash += notional - comm - stamp
            pos.sold_quantity += qty

            entry_dt = datetime.strptime(pos.entry_date, "%Y-%m-%d")
            exit_dt = datetime.strptime(order.date, "%Y-%m-%d")
            hold_days = (exit_dt - entry_dt).days

            self.trades.append(Trade(
                code=order.code, entry_date=pos.entry_date, exit_date=order.date,
                entry_price=pos.entry_price, exit_price=exec_price, quantity=qty,
                pnl=pnl, pnl_pct=pnl_pct, reason=order.reason, hold_days=hold_days,
            ))

            if pos.is_closed:
                del self.positions[order.code]

    def update_peak_prices(self, prices: dict[str, float]):
        """更新持仓期间最高价."""
        for code, price in prices.items():
            if code in self.positions:
                self.positions[code].peak_price = max(self.positions[code].peak_price, price)

    def record_equity(self, date: str):
        self.equity_history.append({"date": date, "equity": round(self.equity, 2)})

    def get_open_positions(self) -> list[Position]:
        return [p for p in self.positions.values() if not p.is_closed]
