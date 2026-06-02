"""回测页 — 参数配置 + 绩效报告."""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QPushButton, QSpinBox, QDateEdit,
    QTextEdit, QProgressBar, QMessageBox,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from .workers import BacktestWorker


class BacktestTab(QWidget):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.worker: BacktestWorker | None = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        title = QLabel("历史回测")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #e0e0ff;")
        layout.addWidget(title)

        # 参数区
        param_group = QGroupBox("回测参数")
        param_layout = QHBoxLayout(param_group)
        param_layout.setSpacing(16)

        param_layout.addWidget(QLabel("起始:"))
        self.start_edit = QDateEdit(QDate(2024, 1, 1))
        self.start_edit.setCalendarPopup(True)
        param_layout.addWidget(self.start_edit)

        param_layout.addWidget(QLabel("结束:"))
        self.end_edit = QDateEdit(QDate(2025, 12, 31))
        self.end_edit.setCalendarPopup(True)
        param_layout.addWidget(self.end_edit)

        param_layout.addWidget(QLabel("持仓数:"))
        self.top_spin = QSpinBox()
        self.top_spin.setRange(1, 5)
        self.top_spin.setValue(2)
        param_layout.addWidget(self.top_spin)

        param_layout.addWidget(QLabel("初始资金(万):"))
        self.capital_spin = QSpinBox()
        self.capital_spin.setRange(10, 10000)
        self.capital_spin.setValue(100)
        param_layout.addWidget(self.capital_spin)

        self.run_btn = QPushButton("运行回测")
        self.run_btn.setObjectName("primary_btn")
        self.run_btn.clicked.connect(self.run_backtest)
        param_layout.addWidget(self.run_btn)

        param_layout.addStretch()
        layout.addWidget(param_group)

        # 进度
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 结果区
        result_group = QGroupBox("绩效报告")
        result_layout = QVBoxLayout(result_group)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(300)
        self.result_text.setPlaceholderText("回测结果将显示在这里...")
        result_layout.addWidget(self.result_text)

        layout.addWidget(result_group, 1)

    def run_backtest(self):
        start = self.start_edit.date().toString("yyyy-MM-dd")
        end = self.end_edit.date().toString("yyyy-MM-dd")
        top_n = self.top_spin.value()

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.run_btn.setEnabled(False)
        self.result_text.clear()
        self.result_text.append("回测进行中，请稍候...\n")

        self.worker = BacktestWorker(self.config, start, end, top_n)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_finished(self, result: dict):
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)

        metrics = result.get("metrics")
        trades = result.get("trades", [])

        if metrics:
            txt = metrics.summary()
            txt += f"\n\n--- 最近 10 笔交易 ---\n"
            for t in trades[-10:]:
                txt += f"{t.code} | {t.entry_date}→{t.exit_date} | {t.pnl_pct:+.1%} | 持有{t.hold_days}天 | {t.reason}\n"

            txt += f"\n交易记录已保存到 output/results/"
            self.result_text.setText(txt)
        else:
            self.result_text.setText("回测完成，但未产生交易记录。")

    def _on_error(self, msg: str):
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        self.result_text.append(f"\n错误: {msg}")
        QMessageBox.critical(self, "回测错误", msg)

    def refresh(self):
        pass
