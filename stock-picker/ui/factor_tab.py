"""因子分析页 — IC 表格 + 因子列表."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor


class FactorTab(QWidget):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("因子评价")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #e0e0ff;")
        header.addWidget(title)
        header.addStretch()

        self.refresh_btn = QPushButton("刷新因子列表")
        self.refresh_btn.clicked.connect(self.load_factors)
        header.addWidget(self.refresh_btn)

        layout.addLayout(header)

        # 因子列表
        factor_group = QGroupBox("41 因子注册表 (F01–F41)")
        factor_layout = QVBoxLayout(factor_group)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "名称", "大类", "子类", "方向"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)

        factor_layout.addWidget(self.table)
        layout.addWidget(factor_group, 1)

        # IC 分析占位
        ic_group = QGroupBox("因子 IC 分析（需先运行回测积累数据）")
        ic_layout = QVBoxLayout(ic_group)
        info = QLabel("运行回测后，可分析各因子的 IC/ICIR/分层收益，自动降权低效因子。\n"
                       "CLI 方式: python main.py --eval-factors")
        info.setStyleSheet("color: #606080; font-size: 12px; padding: 12px;")
        info.setWordWrap(True)
        ic_layout.addWidget(info)
        layout.addWidget(ic_group)

    def load_factors(self):
        try:
            from factors.registry import FACTOR_REGISTRY
            factors = sorted(FACTOR_REGISTRY.values(), key=lambda f: f.id)
            self.table.setRowCount(len(factors))

            cat_colors = {
                "fundamental": "#3399ff",
                "technical": "#ff9900",
                "capital": "#00cc66",
                "industry": "#9966ff",
                "news": "#ff6699",
                "catalyst": "#00cccc",
            }
            dir_map = {"positive": "↑ 正向", "negative": "↓ 负向", "neutral": "— 中性"}

            for i, f in enumerate(factors):
                id_item = QTableWidgetItem(f.id)
                id_item.setForeground(QColor("#e94560"))
                self.table.setItem(i, 0, id_item)
                self.table.setItem(i, 1, QTableWidgetItem(f.name))

                cat_item = QTableWidgetItem(f.category)
                if f.category in cat_colors:
                    cat_item.setForeground(QColor(cat_colors[f.category]))
                self.table.setItem(i, 2, cat_item)

                self.table.setItem(i, 3, QTableWidgetItem(f.sub_category))
                self.table.setItem(i, 4, QTableWidgetItem(dir_map.get(f.direction, f.direction)))

            self.table.setRowCount(len(factors))
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载因子列表失败: {e}")

    def refresh(self):
        self.load_factors()
