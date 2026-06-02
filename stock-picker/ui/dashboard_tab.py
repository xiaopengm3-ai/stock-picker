"""仪表盘 — 市场概览 + 快速统计."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QGridLayout, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class StatCard(QFrame):
    """统计卡片."""
    def __init__(self, title: str, value: str, color: str = "#e94560"):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 8px;
                border-left: 4px solid {color};
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        val_label = QLabel(value)
        val_label.setFont(QFont("Microsoft YaHei", 20, QFont.Weight.Bold))
        val_label.setStyleSheet(f"color: {color}; border: none; background: transparent;")
        val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(val_label)

        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", 10))
        title_label.setStyleSheet("color: #a0a0c0; border: none; background: transparent;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)


class DashboardTab(QWidget):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # 标题
        title = QLabel("市场仪表盘")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #e0e0ff;")
        layout.addWidget(title)

        # 市场环境卡片
        status_group = QGroupBox("今日市场环境")
        status_layout = QGridLayout(status_group)
        status_layout.setSpacing(10)

        self.market_temp_card = StatCard("市场温度", "--", "#e94560")
        self.market_regime_card = StatCard("市场状态", "--", "#ff9900")
        self.position_card = StatCard("建议仓位", "--", "#00cc66")
        self.stock_count_card = StatCard("全市场", "--", "#3399ff")

        status_layout.addWidget(self.market_temp_card, 0, 0)
        status_layout.addWidget(self.market_regime_card, 0, 1)
        status_layout.addWidget(self.position_card, 0, 2)
        status_layout.addWidget(self.stock_count_card, 0, 3)

        layout.addWidget(status_group)

        # 指数详情
        index_group = QGroupBox("主要指数")
        self.index_grid = QGridLayout(index_group)
        self.index_grid.setSpacing(8)

        headers = ["指数", "点位", "趋势", "60日涨幅", "vs EMA60", "vs EMA200"]
        for i, h in enumerate(headers):
            lbl = QLabel(h)
            lbl.setStyleSheet("color: #e94560; font-weight: bold; font-size: 12px;")
            self.index_grid.addWidget(lbl, 0, i)

        index_names = ["上证指数", "沪深300", "中证500", "中证1000"]
        self.index_labels = {}
        for row, name in enumerate(index_names, 1):
            self.index_grid.addWidget(QLabel(name), row, 0)
            for col in range(1, 6):
                lbl = QLabel("--")
                lbl.setStyleSheet("color: #a0a0c0;")
                self.index_grid.addWidget(lbl, row, col)
                self.index_labels[(name, col)] = lbl

        layout.addWidget(index_group)

        # 系统信息
        sys_group = QGroupBox("系统信息")
        sys_layout = QGridLayout(sys_group)
        sys_layout.setSpacing(8)
        info = [
            ("因子数量:", "41 个 (F01–F41)"),
            ("数据源:", "akshare + 东方财富"),
            ("AI 状态:", "未启用 (配置中开启)"),
            ("版本:", "V2.0 Phase 3"),
            ("打包:", "PyQt6 + PyInstaller"),
        ]
        for i, (k, v) in enumerate(info):
            sys_layout.addWidget(QLabel(k), i, 0)
            vl = QLabel(v)
            vl.setStyleSheet("color: #a0a0c0;")
            sys_layout.addWidget(vl, i, 1)

        layout.addWidget(sys_group)
        layout.addStretch()

    def refresh(self):
        """刷新仪表盘数据."""
        try:
            from data.index import fetch_all_index_daily
            from environment import detect_market_state

            index_data = fetch_all_index_daily()
            state = detect_market_state(index_data)

            self.market_temp_card.findChildren(QLabel)[0].setText(f"{state.temperature:.0f}/100")
            self.market_regime_card.findChildren(QLabel)[0].setText(state.regime)
            self.position_card.findChildren(QLabel)[0].setText(f"{state.suggested_position:.0%}")

            # 指数详情
            for name, info in state.details.items():
                for col, key in [(1, "close"), (2, "trend"), (3, "ret_60d"),
                                  (4, "above_ema60"), (5, "above_ema200")]:
                    if (name, col) in self.index_labels:
                        val = info.get(key, "--")
                        if isinstance(val, bool):
                            val = "✓ 上方" if val else "✗ 下方"
                        elif isinstance(val, float):
                            val = f"{val:.1f}"
                        self.index_labels[(name, col)].setText(str(val))
        except Exception as e:
            self.market_temp_card.findChildren(QLabel)[0].setText("N/A")
            self.market_regime_card.findChildren(QLabel)[0].setText(str(e)[:20])
