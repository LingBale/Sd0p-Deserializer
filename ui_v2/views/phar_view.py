from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTextEdit, QLabel, QFileDialog, QMessageBox, QLineEdit)
from core_v2.phar.generator import PharGenerator
import os

class PharView(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Payload 输入
        layout.addWidget(QLabel("序列化 Payload:"))
        self.payload_input = QTextEdit()
        self.payload_input.setPlaceholderText("在此粘贴 O:... 格式的 Payload...")
        layout.addWidget(self.payload_input)

        # 配置选项
        config_layout = QHBoxLayout()
        self.stub_input = QLineEdit("<?php __HALT_COMPILER(); ?>")
        self.stub_input.setPlaceholderText("PHP Stub (可选)")
        config_layout.addWidget(QLabel("Stub:"))
        config_layout.addWidget(self.stub_input, 1)
        layout.addLayout(config_layout)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.save_path_input = QLineEdit("output.phar")
        btn_layout.addWidget(QLabel("保存路径:"))
        btn_layout.addWidget(self.save_path_input, 1)
        
        self.browse_btn = QPushButton("📂 浏览")
        self.browse_btn.clicked.connect(self.browse_save_path)
        btn_layout.addWidget(self.browse_btn)
        
        self.gen_btn = QPushButton("⚡ 生成 PHAR")
        self.gen_btn.clicked.connect(self.generate_phar)
        btn_layout.addWidget(self.gen_btn)
        
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.clicked.connect(self.clear)
        btn_layout.addWidget(self.clear_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)

    def browse_save_path(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "保存 PHAR 文件", "", "PHAR Files (*.phar)")
        if file_path:
            self.save_path_input.setText(file_path)

    def generate_phar(self):
        payload = self.payload_input.toPlainText().strip()
        if not payload:
            QMessageBox.warning(self, "提示", "请输入 Payload")
            return
        
        try:
            generator = PharGenerator()
            generator.set_payload(payload)
            generator.set_stub(self.stub_input.text())
            
            output_path = self.save_path_input.text() or "output.phar"
            generator.generate(output_path)
            
            QMessageBox.information(self, "成功", f"PHAR 文件已生成:\n{os.path.abspath(output_path)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成失败: {str(e)}")

    def clear(self):
        """清空 PHAR 生成配置"""
        self.payload_input.clear()
        self.save_path_input.setText("output.phar")
