"""选股页 — 参数设置 + 结果展示."""
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QPushButton, QSpinBox, QDateEdit,
    QScrollArea, QFrame, QTextEdit, QGridLayout,
    QProgressBar, QMessageBox,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from .workers import ScreeningWorker


class ScoreCard(QFrame):
    """打分卡组件."""
    def __init__(self, rank: int, data: dict):
        super().__init__()
        self.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # 标题行
        header = QHBoxLayout()
        rank_label = QLabel(f"\U0001f3c6 #{rank}")
        rank_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        rank_label.setStyleSheet("color: #e94560;")

        name_label = QLabel(f"{data.get('name', '--')} ({data.get('code', '--')})")
        name_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))

        score_label = QLabel(f"{data.get('final_score', 0):.1f} 分")
        score_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        score_label.setStyleSheet("color: #00cc66;")

        level_label = QLabel(f"等级: {data.get('rank_level', '-')}")
        level_label.setStyleSheet("color: #ff9900;")

        header.addWidget(rank_label)
        header.addWidget(name_label, 1)
        header.addWidget(level_label)
        header.addWidget(score_label)
        layout.addLayout(header)

        # 评分明细
        dims = [
            ("基本面", "fundamental_total"),
            ("技术面", "technical_total"),
            ("资金面", "capital_flow_total"),
            ("行业面", "industry_total"),
            ("消息面", "news_total"),
            ("催化剂", "catalyst_total"),
            ("市场环境", "market_regime_total"),
        ]
        dim_grid = QGridLayout()
        for i, (dname, dkey) in enumerate(dims):
            val = data.get(dkey, 0)
            col, row = i % 4, i // 4
            lbl = QLabel(f"{dname}: {float(val):.1f}")
            lbl.setStyleSheet("color: #a0a0c0; font-size: 12px;")
            dim_grid.addWidget(lbl, row, col)
        layout.addLayout(dim_grid)


class ScreeningTab(QWidget):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.worker: ScreeningWorker | None = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("智能选股")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #e0e0ff;")
        layout.addWidget(title)

        # 参数区
        param_group = QGroupBox("选股参数")
        param_layout = QHBoxLayout(param_group)
        param_layout.setSpacing(16)

        param_layout.addWidget(QLabel("日期:"))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        param_layout.addWidget(self.date_edit)

        param_layout.addWidget(QLabel("输出数量:"))
        self.top_spin = QSpinBox()
        self.top_spin.setRange(1, 10)
        self.top_spin.setValue(self.config.get("screening", {}).get("top_n", 2))
        param_layout.addWidget(self.top_spin)

        param_layout.addWidget(QLabel("最低分数:"))
        self.min_score_spin = QSpinBox()
        self.min_score_spin.setRange(30, 95)
        self.min_score_spin.setValue(self.config.get("screening", {}).get("min_score", 60))
        param_layout.addWidget(self.min_score_spin)

        self.run_btn = QPushButton("开始选股")
        self.run_btn.setObjectName("primary_btn")
        self.run_btn.clicked.connect(self.run_screening)
        param_layout.addWidget(self.run_btn)

        param_layout.addStretch()
        layout.addWidget(param_group)

        # 进度
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #606080; font-size: 12px;")
        layout.addWidget(self.status_label)

        # 结果区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setSpacing(12)
        self.results_layout.addStretch()
        scroll.setWidget(self.results_widget)
        layout.addWidget(scroll, 1)

    def run_screening(self):
        date = self.date_edit.date().toString("yyyy-MM-dd")
        top_n = self.top_spin.value()

        # 清空旧结果
        for i in reversed(range(self.results_layout.count())):
            w = self.results_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        self.results_layout.addStretch()

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.status_label.setText(f"正在选股 {date}...")
        self.run_btn.setEnabled(False)

        self.worker = ScreeningWorker(self.config, date, top_n)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_finished(self, results):
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)

        if not results:
            self.status_label.setText("未获取到任何数据，请检查网络或数据源")
            return

        # 显示统计
        stats = results[0].get("_stats", {})
        total = stats.get("total", "?")
        after_f = stats.get("after_filter", "?")
        after_r = stats.get("after_risk", "?")
        top_score = stats.get("top_score", 0)
        threshold_met = stats.get("threshold_met", False)

        self.status_label.setText(
            f"扫描: {total}只 → 过滤后{after_f}只 → 入选{after_r}只 | "
            f"最高分: {top_score:.1f} | "
            f"{'✓ 达标' if threshold_met else '⚠ 均未达阈值（显示最高分）'}"
        )

        # 移除 stretch
        last = self.results_layout.itemAt(self.results_layout.count() - 1)
        if last and last.spacerItem():
            self.results_layout.removeItem(last)

        for i, r in enumerate(results, 1):
            # 跳过统计信息
            r_display = {k: v for k, v in r.items() if k != "_stats"}
            if not r_display.get("code"):
                continue
            card = ScoreCard(i, r_display)
            self.results_layout.addWidget(card)

        self.results_layout.addStretch()

    def _on_error(self, msg: str):
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        self.status_label.setText(f"错误: {msg}")
        QMessageBox.critical(self, "选股错误", msg)

    def refresh(self):
        pass
