import shutil
import subprocess
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QSpinBox, QMessageBox)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ 沙箱设置")
        self.resize(400, 200)
        self.init_ui()
        self.load_defaults()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # PHP 路径
        path_layout = QHBoxLayout()
        self.php_path_input = QLineEdit()
        self.detect_btn = QPushButton("🔍 自动检测")
        self.detect_btn.clicked.connect(self.auto_detect_php)
        path_layout.addWidget(QLabel("PHP 解释器路径:"))
        path_layout.addWidget(self.php_path_input)
        path_layout.addWidget(self.detect_btn)
        layout.addLayout(path_layout)

        # 超时设置
        timeout_layout = QHBoxLayout()
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 60)
        self.timeout_spin.setValue(5)
        timeout_layout.addWidget(QLabel("执行超时 (秒):"))
        timeout_layout.addWidget(self.timeout_spin)
        timeout_layout.addStretch()
        layout.addLayout(timeout_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 保存")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)

    def auto_detect_php(self):
        php_path = shutil.which("php")
        if php_path:
            self.php_path_input.setText(php_path)
        else:
            QMessageBox.warning(self, "提示", "未在系统 PATH 中找到 php.exe")

    def load_defaults(self):
        self.php_path_input.setText(shutil.which("php") or "php")
