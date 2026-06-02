"""设置页 — YAML 配置编辑器."""
import yaml
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QPushButton, QTextEdit, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class SettingsTab(QWidget):
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.config_path = Path("config.yaml")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("系统设置")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #e0e0ff;")
        header.addWidget(title)
        header.addStretch()

        self.reload_btn = QPushButton("重新加载")
        self.reload_btn.clicked.connect(self._reload)
        header.addWidget(self.reload_btn)

        self.save_btn = QPushButton("保存配置")
        self.save_btn.setObjectName("primary_btn")
        self.save_btn.clicked.connect(self._save)
        header.addWidget(self.save_btn)

        layout.addLayout(header)

        # 配置编辑器
        editor_group = QGroupBox("config.yaml")
        editor_layout = QVBoxLayout(editor_group)

        self.editor = QTextEdit()
        self.editor.setMinimumHeight(400)
        self.editor.setTabStopDistance(20)
        editor_layout.addWidget(self.editor)

        layout.addWidget(editor_group, 1)

        # 快捷操作
        quick_group = QGroupBox("快捷操作")
        quick_layout = QHBoxLayout(quick_group)
        quick_layout.setSpacing(12)

        labels = [
            ("PE上限", "pe_max", "50"),
            ("商誉上限%", "goodwill_max", "50"),
            ("质押上限%", "pledge_max", "60"),
            ("黑名单管理", "blacklist", ""),
        ]
        self.quick_inputs = {}
        for lname, key, default in labels:
            quick_layout.addWidget(QLabel(lname))
            from PyQt6.QtWidgets import QLineEdit
            inp = QLineEdit()
            inp.setMaximumWidth(80)
            inp.setText(default)
            inp.setPlaceholderText(default)
            quick_layout.addWidget(inp)
            self.quick_inputs[key] = inp

        quick_layout.addStretch()
        layout.addWidget(quick_group)

        # 帮助提示
        help_text = QLabel(
            "提示: 修改配置后点「保存配置」生效。\n"
            "权重总和应为 1.00 (100%)。支持热加载，保存后下次选股自动使用新配置。"
        )
        help_text.setStyleSheet("color: #606080; font-size: 11px; padding: 8px;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

    def refresh(self):
        self._reload()

    def _reload(self):
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.editor.setPlainText(content)
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config.update(yaml.safe_load(f))
        except Exception as e:
            QMessageBox.warning(self, "加载失败", str(e))

    def _save(self):
        try:
            content = self.editor.toPlainText()
            new_config = yaml.safe_load(content)
            # 写入文件
            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(content)
            # 更新内存中的配置
            self.config.clear()
            self.config.update(new_config)
            QMessageBox.information(self, "成功", "配置已保存，即时生效。")
        except yaml.YAMLError as e:
            QMessageBox.critical(self, "YAML 语法错误", str(e))
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))
