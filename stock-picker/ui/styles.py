"""全局 QSS 样式 — 暗色专业主题."""
DARK_THEME = """
/* ===== 全局 ===== */
QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ===== 主窗口 ===== */
QMainWindow {
    background-color: #1a1a2e;
}

/* ===== 侧边栏 ===== */
#sidebar {
    background-color: #16213e;
    border-right: 1px solid #0f3460;
    min-width: 180px;
    max-width: 180px;
}

#sidebar QPushButton {
    background-color: transparent;
    color: #a0a0c0;
    border: none;
    text-align: left;
    padding: 12px 20px;
    font-size: 14px;
    border-radius: 0px;
}

#sidebar QPushButton:hover {
    background-color: #1a1a40;
    color: #ffffff;
}

#sidebar QPushButton:checked {
    background-color: #0f3460;
    color: #e94560;
    border-left: 3px solid #e94560;
}

#logo_label {
    color: #e94560;
    font-size: 18px;
    font-weight: bold;
    padding: 20px 16px 10px 16px;
}

#version_label {
    color: #606080;
    font-size: 11px;
    padding: 0px 16px 16px 16px;
}

/* ===== 内容区 ===== */
#content_area {
    background-color: #1a1a2e;
}

/* ===== 分组框 ===== */
QGroupBox {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 8px;
    margin-top: 12px;
    padding: 16px;
    font-size: 14px;
    font-weight: bold;
    color: #e0e0ff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: #e94560;
}

/* ===== 按钮 ===== */
QPushButton {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 1px solid #1a5080;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 13px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #1a5080;
    border-color: #2a70a0;
}

QPushButton:pressed {
    background-color: #0a2540;
}

QPushButton:disabled {
    background-color: #2a2a3e;
    color: #606070;
}

/* 主要操作按钮 */
#primary_btn {
    background-color: #e94560;
    border-color: #e94560;
    color: #ffffff;
    font-weight: bold;
    font-size: 14px;
    padding: 10px 30px;
}

#primary_btn:hover {
    background-color: #ff6b80;
}

/* ===== 表格 ===== */
QTableWidget, QTableView {
    background-color: #16213e;
    alternate-background-color: #1a2540;
    border: 1px solid #0f3460;
    border-radius: 6px;
    gridline-color: #1f3060;
    selection-background-color: #0f3460;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #0f3460;
    color: #e0e0ff;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #e94560;
    font-weight: bold;
    font-size: 12px;
}

/* ===== 文本输入 ===== */
QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit {
    background-color: #0d1b33;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 13px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #e94560;
}

/* ===== 标签页 ===== */
QTabWidget::pane {
    background-color: #1a1a2e;
    border: 1px solid #0f3460;
    border-radius: 6px;
}

QTabBar::tab {
    background-color: #16213e;
    color: #a0a0c0;
    padding: 10px 24px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 13px;
}

QTabBar::tab:selected {
    color: #e94560;
    border-bottom: 2px solid #e94560;
}

QTabBar::tab:hover {
    color: #ffffff;
}

/* ===== 滚动条 ===== */
QScrollBar:vertical {
    background-color: #1a1a2e;
    width: 8px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #0f3460;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #1a5080;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ===== 进度条 ===== */
QProgressBar {
    background-color: #0d1b33;
    border: 1px solid #0f3460;
    border-radius: 4px;
    text-align: center;
    color: #e0e0e0;
    font-size: 11px;
}

QProgressBar::chunk {
    background-color: #e94560;
    border-radius: 3px;
}

/* ===== 下拉框 ===== */
QComboBox {
    background-color: #0d1b33;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    border-radius: 4px;
    padding: 6px 10px;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #16213e;
    selection-background-color: #0f3460;
}

/* ===== 文本编辑器 ===== */
QPlainTextEdit, QTextEdit {
    background-color: #0d1b33;
    color: #a0ffa0;
    border: 1px solid #0f3460;
    border-radius: 4px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
}

/* ===== 复选框 ===== */
QCheckBox {
    color: #e0e0e0;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #0f3460;
    background-color: #0d1b33;
}

QCheckBox::indicator:checked {
    background-color: #e94560;
    border-color: #e94560;
}

/* ===== 工具提示 ===== */
QToolTip {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    padding: 6px;
    border-radius: 4px;
}
"""
