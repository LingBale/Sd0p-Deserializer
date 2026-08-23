from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTextEdit, QLabel, QMessageBox)
from PyQt6.QtCore import Qt
from core_v2.http.client import HttpClient

class HTTPPreviewDialog(QDialog):
    def __init__(self, raw_request, parent=None):
        super().__init__(parent)
        self.setWindowTitle("👁️ HTTP 请求预览与编辑")
        self.resize(600, 500)
        self.raw_request = raw_request
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("原始 HTTP 请求报文 (可编辑):"))
        self.editor = QTextEdit()
        self.editor.setText(self.raw_request)
        self.editor.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        layout.addWidget(self.editor)

        # 按钮区域
        btn_layout = QHBoxLayout()
        self.copy_btn = QPushButton("📋 复制报文")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        
        self.send_btn = QPushButton("🚀 发送此请求")
        self.send_btn.clicked.connect(self.send_edited_request)
        
        cancel_btn = QPushButton("❌ 关闭")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.send_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)

    def copy_to_clipboard(self):
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.editor.toPlainText())
        QMessageBox.information(self, "提示", "已复制到剪贴板！")

    def send_edited_request(self):
        """解析编辑后的报文并发送，并在对话框内显示响应"""
        text = self.editor.toPlainText()
        lines = text.split('\n')
        if not lines:
            return

        # 简单解析第一行获取方法和路径
        first_line = lines[0]
        parts = first_line.split()
        if len(parts) < 2:
            QMessageBox.warning(self, "错误", "请求行格式不正确")
            return
            
        method = parts[0]
        path = parts[1]
        
        # 尝试从 Host 头获取域名
        host = ""
        for line in lines[1:]:
            if line.lower().startswith("host:"):
                host = line.split(":", 1)[1].strip()
                break
        
        if not host:
            QMessageBox.warning(self, "错误", "未找到 Host 头部，无法确定目标服务器")
            return

        url = f"http://{host}{path}"
        
        # 提取 Body (空行之后)
        body = ""
        in_body = False
        for line in lines:
            if in_body:
                body += line + "\n"
            elif line == "":
                in_body = True
        
        client = HttpClient()
        result = client.send(url, method, body.strip(), "data") 
        
        if result['success']:
            resp_text = f"HTTP/1.1 {result['status']} OK\n"
            for k, v in result['headers'].items():
                resp_text += f"{k}: {v}\n"
            resp_text += f"\n{result['body']}"
            
            # 在对话框下方增加响应显示区域（如果不存在则创建）
            if not hasattr(self, 'resp_view'):
                resp_group = QLabel("📥 服务器响应:")
                self.layout().insertWidget(1, resp_group)
                self.resp_view = QTextEdit()
                self.resp_view.setReadOnly(True)
                self.resp_view.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
                self.layout().insertWidget(2, self.resp_view)
            
            self.resp_view.setText(resp_text)
        else:
            QMessageBox.critical(self, "❌ 发送失败", result.get('error', 'Unknown error'))
