"""主窗口 — 侧边栏导航 + 内容区."""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QButtonGroup,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from .styles import DARK_THEME
from .dashboard_tab import DashboardTab
from .screening_tab import ScreeningTab
from .backtest_tab import BacktestTab
from .factor_tab import FactorTab
from .settings_tab import SettingsTab

NAV_ITEMS = [
    ("\U0001f4ca  仪表盘", "dashboard"),
    ("\U0001f50d  选股", "screening"),
    ("\U0001f4c8  回测", "backtest"),
    ("\U0001f4ca  因子分析", "factor"),
    ("⚙️  设置", "settings"),
]


class MainWindow(QMainWindow):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.setWindowTitle("A股智能选股系统 V2.0")
        self.resize(1200, 780)
        self.setMinimumSize(960, 640)
        self.setStyleSheet(DARK_THEME)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 侧边栏 ──
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        logo = QLabel("StockPicker")
        logo.setObjectName("logo_label")
        sidebar_layout.addWidget(logo)

        version = QLabel("V2.0 · Phase 3")
        version.setObjectName("version_label")
        sidebar_layout.addWidget(version)

        self.nav_buttons = []
        self.btn_group = QButtonGroup()
        self.btn_group.setExclusive(True)

        for text, key in NAV_ITEMS:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.nav_buttons.append(btn)
            self.btn_group.addButton(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        footer = QLabel("xiaopengm3-ai")
        footer.setObjectName("version_label")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(footer)
        sidebar_layout.addSpacing(10)

        layout.addWidget(sidebar)

        # ── 内容区 ──
        self.stack = QStackedWidget()
        self.stack.setObjectName("content_area")

        self.dashboard_tab = DashboardTab(config)
        self.screening_tab = ScreeningTab(config)
        self.backtest_tab = BacktestTab(config)
        self.factor_tab = FactorTab(config)
        self.settings_tab = SettingsTab(config)

        self.stack.addWidget(self.dashboard_tab)
        self.stack.addWidget(self.screening_tab)
        self.stack.addWidget(self.backtest_tab)
        self.stack.addWidget(self.factor_tab)
        self.stack.addWidget(self.settings_tab)

        layout.addWidget(self.stack, 1)

        # 连接导航
        for i, (_, key) in enumerate(NAV_ITEMS):
            self.nav_buttons[i].clicked.connect(lambda checked, idx=i: self._switch_tab(idx))

        # 默认选中仪表盘
        self.nav_buttons[0].setChecked(True)
        self._switch_tab(0)

    def _switch_tab(self, index: int):
        self.stack.setCurrentIndex(index)
        if index == 0:
            self.dashboard_tab.refresh()
        elif index == 1:
            self.screening_tab.refresh()
        elif index == 2:
            self.backtest_tab.refresh()
        elif index == 3:
            self.factor_tab.refresh()
        elif index == 4:
            self.settings_tab.refresh()
