from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTextEdit, QFileDialog, QLabel, QSplitter, 
                             QTreeWidget, QTreeWidgetItem, QHeaderView, QMessageBox, QComboBox, QGroupBox, QLineEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QTextCharFormat, QColor, QFont
import re
import os

from core_v2.sandbox.local import LocalSandbox
from core_v2.serializer.obfuscator import PayloadObfuscator
from core_v2.ai.assistant import AIAnalyzer
from core_v2.http.client import HttpClient
from core_v2.utils.escape_detector import ExternalEscapeDetector

class SandboxWorker(QThread):
    """后台沙箱测试线程"""
    finished = pyqtSignal(dict)

    def __init__(self, payload):
        super().__init__()
        self.payload = payload

    def run(self):
        sandbox = LocalSandbox()
        result = sandbox.execute(self.payload)
        self.finished.emit(result)

class AnalysisWorker(QThread):
    """后台分析线程，避免界面卡顿"""
    finished = pyqtSignal(object, object, list) # class_info, features, all_classes
    error = pyqtSignal(str)

    def __init__(self, engine, code):
        super().__init__()
        self.engine = engine
        self.code = code

    def run(self):
        try:
            classes = self.engine.parser.parse(self.code)
            if not classes:
                self.error.emit("No classes found in the provided code.")
                return
            
            target_class = classes[0]
            features = self.engine.extractor.extract_from_code(target_class, self.code)
            self.finished.emit(target_class, features, classes)  # 返回完整类列表
        except Exception as e:
            self.error.emit(str(e))

class DashboardView(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.current_code = ""
        self.original_payload = "" # 存储原始生成的 Payload
        self.current_payload = "" # 存储当前显示的完整 Payload (含 \0)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 顶部工具栏
        toolbar = QHBoxLayout()
        self.upload_btn = QPushButton("📂 上传 PHP 文件")
        self.upload_btn.clicked.connect(self.load_file)
        
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(["Standard", "Callback RCE", "String Escape"])
        self.strategy_combo.setCurrentText("Standard")
        
        self.generate_btn = QPushButton("⚡ 生成 Payload")
        self.generate_btn.setEnabled(False)
        self.generate_btn.clicked.connect(self.start_analysis)
        
        toolbar.addWidget(self.upload_btn)
        toolbar.addWidget(self.strategy_combo)
        toolbar.addWidget(self.generate_btn)
        
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.clicked.connect(self.clear)
        toolbar.addWidget(self.clear_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # 主分割视图：左侧代码/结构，右侧结果
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：代码预览与结构树
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.code_view = QTextEdit()
        self.code_view.setPlaceholderText("在此粘贴 PHP 代码或上传文件...")
        self.code_view.textChanged.connect(self.on_code_changed)
        self.highlight_php_syntax()
        
        self.structure_tree = QTreeWidget()
        self.structure_tree.setHeaderLabels(["名称", "类型", "详情"])
        self.structure_tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.structure_tree.setEditTriggers(QTreeWidget.EditTrigger.DoubleClicked)
        self.structure_tree.itemChanged.connect(self.on_property_changed)
        
        left_layout.addWidget(QLabel("代码预览:"))
        left_layout.addWidget(self.code_view, 1)
        left_layout.addWidget(QLabel("类结构:"))
        left_layout.addWidget(self.structure_tree, 1)
        
        # 右侧：Payload 输出与 AI 建议
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.payload_view = QTextEdit()
        self.payload_view.setReadOnly(True)
        self.payload_view.setStyleSheet("font-family: Consolas, monospace; font-size: 12px;")
        
        right_layout.addWidget(QLabel("生成的 Payload:"))
        right_layout.addWidget(self.payload_view)
        
        # 沙箱测试按钮
        self.sandbox_btn = QPushButton("🧪 沙箱测试")
        self.sandbox_btn.clicked.connect(self.start_sandbox_test)
        right_layout.addWidget(self.sandbox_btn)
        
        # 混淆工具栏
        obf_toolbar = QHBoxLayout()
        self.obf_combo = QComboBox()
        self.obf_combo.addItems(["原始 Payload", "Base64 混淆", "Gzip+Base64", "ROT13"])
        self.obf_combo.currentIndexChanged.connect(self.on_obfuscate_method_changed)
        
        self.copy_btn = QPushButton("📋 复制 (明文)")
        self.copy_btn.setToolTip("注意：包含特殊字符时可能截断")
        self.copy_btn.clicked.connect(self.copy_current_payload)
        
        self.copy_b64_btn = QPushButton("🔐 复制 Base64")
        self.copy_b64_btn.setToolTip("推荐：将 Payload 编码后复制，避免截断")
        self.copy_b64_btn.clicked.connect(self.copy_base64_payload)
        
        self.export_btn = QPushButton("💾 导出为文件")
        self.export_btn.setToolTip("最可靠：保存为 .txt 文件")
        self.export_btn.clicked.connect(self.export_payload_to_file)
        self.test_obf_btn = QPushButton("🧪 测试混淆结果")
        self.test_obf_btn.clicked.connect(self.test_obfuscated_payload)
        
        # P2-5: 序列化模式切换控件
        self.serialize_mode_combo = QComboBox()
        self.serialize_mode_combo.addItems(["传统对象格式（默认）", "数组格式（PHP 7.4+ __serialize）"])
        self.serialize_mode_combo.setToolTip("针对使用 __serialize/__unserialize 钩子的类，切换到数组格式可避免可见性前缀问题")
        
        obf_toolbar.addWidget(QLabel("混淆方式:"))
        obf_toolbar.addWidget(self.obf_combo)
        obf_toolbar.addWidget(self.copy_btn)
        obf_toolbar.addWidget(self.copy_b64_btn)
        obf_toolbar.addWidget(self.export_btn)
        obf_toolbar.addWidget(self.test_obf_btn)
        obf_toolbar.addSpacing(20)  # 添加间距
        obf_toolbar.addWidget(QLabel("序列化模式:"))
        obf_toolbar.addWidget(self.serialize_mode_combo)
        right_layout.addLayout(obf_toolbar)
        
        # AI 建议面板
        ai_group = QGroupBox("🤖 AI 安全审计建议")
        ai_layout = QVBoxLayout()
        self.ai_result_view = QTextEdit()
        self.ai_result_view.setReadOnly(True)
        self.ai_result_view.setMaximumHeight(150)
        ai_layout.addWidget(self.ai_result_view)
        ai_group.setLayout(ai_layout)
        right_layout.addWidget(ai_group)
        
        # HTTP 发包面板
        http_group = QGroupBox("📡 HTTP 发送测试")
        http_layout = QVBoxLayout()
        
        url_layout = QHBoxLayout()
        self.http_method_combo = QComboBox()
        self.http_method_combo.addItems(["GET", "POST"])
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("http://target.com/vuln.php")
        url_layout.addWidget(self.http_method_combo)
        url_layout.addWidget(self.url_input)
        
        param_layout = QHBoxLayout()
        self.param_name_input = QLineEdit("data")
        self.param_name_input.setFixedWidth(80)
        self.preview_btn = QPushButton("👁️ 预览请求")
        self.preview_btn.clicked.connect(self.preview_http_request)
        self.send_btn = QPushButton("🚀 发送请求")
        self.send_btn.clicked.connect(self.send_http_request)
        param_layout.addWidget(QLabel("参数名:"))
        param_layout.addWidget(self.param_name_input)
        param_layout.addWidget(self.preview_btn)
        param_layout.addWidget(self.send_btn)
        param_layout.addStretch()
        
        http_layout.addLayout(url_layout)
        http_layout.addLayout(param_layout)
        http_group.setLayout(http_layout)
        right_layout.addWidget(http_group)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        self.setLayout(layout)

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择 PHP 文件", "", "PHP 文件 (*.php)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.current_code = f.read()
                self.code_view.setText(self.current_code)
                self.generate_btn.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"读取文件失败: {str(e)}")

    def on_code_changed(self):
        self.current_code = self.code_view.toPlainText()
        self.generate_btn.setEnabled(len(self.current_code) > 0)

    def start_analysis(self):
        if not self.current_code:
            return
        
        self.status_bar = self.window().statusBar() if hasattr(self.window(), 'statusBar') else None
        if self.status_bar:
            self.status_bar.showMessage("正在分析...")
        
        self.worker = AnalysisWorker(self.engine, self.current_code)
        self.worker.finished.connect(self.on_analysis_finished)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.start()

    def on_analysis_finished(self, class_info, features, all_classes):
        if self.status_bar:
            self.status_bar.showMessage("分析完成")
        
        # 更新结构树
        self.update_structure_tree(class_info)
        
        # 运行 AI 审计
        self.run_ai_audit(class_info, features)
        
        # 运行外部逃逸检测
        self.check_external_escape(self.current_code)
        
        # P3-1: 运行 PHAR 场景检测
        self.check_phar_context(features)
        
        # P2-6: 运行能力边界检测
        self.check_capability_boundary(features)
        
        # V3 Bug修复: 更新 POP 链分析图谱
        main_window = self.window()
        if main_window and hasattr(main_window, 'pop_chain_view'):
            try:
                main_window.pop_chain_view.update_graph(all_classes)
            except Exception as e:
                import logging
                logging.warning(f"Failed to update POP chain graph: {e}")
        
        # V3 UI集成: 直接调用引擎的 analyze_and_generate 方法，该方法已包含 V3 路由分支
        payload = self.engine.analyze_and_generate(self.current_code)
        self.original_payload = payload
        
        # V3 UI集成: 检测是否为实验性 Payload
        is_experimental = 'C:' in payload and ('Fiber' in payload or 'SplFixedArray' in payload)
        if is_experimental:
            self.payload_view.setPlaceholderText("⚠️ 实验性 Payload - 请验证目标环境 PHP 版本")
        else:
            self.payload_view.setPlaceholderText("")
        
        # 检查当前是否选择了混淆方式，如果是则自动应用
        current_obf_index = self.obf_combo.currentIndex()
        if current_obf_index > 0:
            self.on_obfuscate_method_changed(current_obf_index)
        else:
            self.current_payload = str(payload)
            self.payload_view.setText(self.current_payload)

    def on_analysis_error(self, msg):
        if self.status_bar:
            self.status_bar.showMessage("发生错误")
        QMessageBox.critical(self, "分析错误", msg)

    def update_structure_tree(self, class_info):
        self.structure_tree.clear()
        root = QTreeWidgetItem([class_info.name, "类", ""])
        self.structure_tree.addTopLevelItem(root)
        
        # Properties
        prop_root = QTreeWidgetItem(["属性列表", "", ""])
        root.addChild(prop_root)
        for name, prop in class_info.properties.items():
            val = str(prop.default_value) if prop.default_value is not None else "None"
            QTreeWidgetItem(prop_root, [name, "属性", f"{prop.visibility} = {val}"])
        
        # Methods
        method_root = QTreeWidgetItem(["方法列表", "", ""])
        root.addChild(method_root)
        for name, method in class_info.methods.items():
            QTreeWidgetItem(method_root, [name, "方法", f"{len(method.params)} 个参数"])
        
        root.setExpanded(True)

    def start_sandbox_test(self):
        """启动沙箱测试"""
        payload = self.payload_view.toPlainText()
        if not payload:
            QMessageBox.warning(self, "提示", "请先生成 Payload")
            return
        
        if self.status_bar:
            self.status_bar.showMessage("正在沙箱中执行...")
        
        self.sandbox_worker = SandboxWorker(payload)
        self.sandbox_worker.finished.connect(self.on_sandbox_finished)
        self.sandbox_worker.start()

    def on_sandbox_finished(self, result):
        """处理沙箱测试结果"""
        if self.status_bar:
            self.status_bar.showMessage("测试完成")
        
        title = "✅ 执行成功" if result['success'] else "❌ 执行失败"
        msg = f"输出:\n{result['output']}" if result['output'] else f"错误:\n{result['error']}"
        QMessageBox.information(self, title, msg)

    def get_obfuscated_payload(self):
        """获取当前选择的混淆 Payload"""
        original = self.payload_view.toPlainText()
        method_map = {
            "原始 Payload": "none",
            "Base64 混淆": "base64",
            "Gzip+Base64": "gzip_base64",
            "ROT13": "rot13"
        }
        method = method_map.get(self.obf_combo.currentText(), "none")
        return PayloadObfuscator.obfuscate(original, method)

    def copy_current_payload(self):
        """复制当前显示的 Payload (增加异常捕获)"""
        try:
            from PyQt6.QtGui import QGuiApplication
            if not self.current_payload:
                QMessageBox.warning(self, "提示", "没有可复制的 Payload")
                return
            
            # 确保是字符串类型
            payload_str = str(self.current_payload)
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(payload_str)
            QMessageBox.information(self, "成功", f"已复制 {len(payload_str)} 个字符到剪贴板！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"复制失败: {str(e)}")

    def copy_base64_payload(self):
        """将 Payload 进行 Base64 编码后复制到剪贴板"""
        try:
            import base64
            from PyQt6.QtGui import QGuiApplication
            if not self.current_payload:
                QMessageBox.warning(self, "提示", "没有可复制的 Payload")
                return
            
            payload_str = str(self.current_payload)
            encoded = base64.b64encode(payload_str.encode('utf-8')).decode('ascii')
            
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(encoded)
            
            msg = f"已复制 Base64 编码的 Payload ({len(encoded)} 字符)。\n使用时请用 base64_decode() 解码后再反序列化。"
            QMessageBox.information(self, "成功", msg)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"Base64 复制失败: {str(e)}")

    def export_payload_to_file(self):
        """将 Payload 导出为 .txt 文件，避免剪贴板截断问题"""
        if not self.current_payload:
            QMessageBox.warning(self, "提示", "没有可导出的 Payload")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "保存 Payload", "payload.txt", "Text Files (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.current_payload)
                QMessageBox.information(self, "成功", f"Payload 已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

    def test_obfuscated_payload(self):
        """测试混淆后的 Payload"""
        payload = self.get_obfuscated_payload()
        if not payload:
            return
        
        if self.status_bar:
            self.status_bar.showMessage("正在测试混淆结果...")
        
        self.sandbox_worker = SandboxWorker(payload)
        self.sandbox_worker.finished.connect(self.on_sandbox_finished)
        self.sandbox_worker.start()

    def run_ai_audit(self, class_info, features):
        """执行 AI 安全审计并展示结果"""
        analyzer = AIAnalyzer()
        risks = analyzer.analyze(class_info, features)
        
        if not risks:
            self.ai_result_view.setText("✅ 未发现明显安全风险。")
            return
            
        html = ""
        for risk in risks:
            color = {"严重": "#FF0000", "高危": "#FF4500", "中危": "#FFA500", "低危": "#808080"}.get(risk['level'], "#000")
            html += f'<div style="margin-bottom: 8px; border-left: 3px solid {color}; padding-left: 8px;">'
            html += f'<b style="color: {color}">[{risk["level"]}] {risk["title"]}</b><br>'
            html += f'<span style="font-size: 11px; color: #666;">{risk["desc"]}</span>'
            html += '</div>'
        self.ai_result_view.setHtml(html)

    def check_external_escape(self, code):
        """检测外部字符串替换并给出警告"""
        detections = ExternalEscapeDetector.detect(code)
        if not detections:
            return
            
        warning_html = "<hr><b style='color: #FF4500'>⚠️ 检测到外部过滤逻辑：</b><br>"
        for d in detections:
            delta_str = f"长度变化: {'+' if d['delta'] > 0 else ''}{d['delta']}"
            warning_html += f"<div style='font-size: 11px; margin-top: 4px;'>"
            warning_html += f"函数: {d['context']} <br>"
            warning_html += f"{delta_str}。普通 Payload 可能失效，建议构造逃逸利用串。"
            warning_html += f"</div>"
        
        current_html = self.ai_result_view.toHtml()
        self.ai_result_view.setHtml(current_html + warning_html)
    
    def check_phar_context(self, features):
        """P3-1: 检测 PHAR 反序列化场景并给出提示"""
        if 'phar_context' not in features.tags:
            return
        
        warning_html = "<hr><div style='background-color: #FFFACD; border-left: 4px solid #FFD700; padding: 8px; margin-top: 8px;'>"
        warning_html += "<b style='color: #B8860B'>⚠️ 检测到 PHAR 反序列化场景</b><br>"
        warning_html += "<span style='font-size: 11px; color: #666;'>"
        warning_html += "当前生成的 Payload 可能无法直接利用，建议前往「📦 PHAR 生成」标签页构造恶意归档文件。"
        warning_html += "</span></div>"
        
        current_html = self.ai_result_view.toHtml()
        self.ai_result_view.setHtml(current_html + warning_html)
    
    def check_capability_boundary(self, features):
        """P2-6: 检测能力边界并给出诚实提示"""
        warnings = []
        
        if 'spl_object_storage' in features.tags:
            warnings.append({
                'title': '检测到 SplObjectStorage 类',
                'desc': '可能涉及引用计数或内存破坏漏洞 (UAF)。当前版本无法自动生成有效利用链，建议手动分析对象引用关系。',
                'color': '#FF4500'  # OrangeRed
            })
        
        if 'incomplete_class' in features.tags:
            warnings.append({
                'title': '检测到 __PHP_Incomplete_Class 相关逻辑',
                'desc': '此类绕过通常需构造特殊序列化串，当前版本生成的标准对象可能无效，请手动构造。',
                'color': '#FF4500'
            })
        
        if 'wide_char_escape' in features.tags:
            warnings.append({
                'title': '检测到多字节编码函数',
                'desc': '可能存在宽字符逃逸（如 %bf 绕过 addslashes）。当前版本未实现编码层攻击自动生成，请手动测试宽字符注入。',
                'color': '#FF4500'
            })
        
        if 'datetime_traversal' in features.tags:
            warnings.append({
                'title': '检测到 DateTime 类利用',
                'desc': '若目标为路径遍历或命令注入，当前 Payload 已填充基本命令，但可能需要根据实际触发函数调整参数。',
                'color': '#FFA500'  # Orange
            })
        
        if 'spl_fixed_array' in features.tags:
            warnings.append({
                'title': '检测到 SplFixedArray 类',
                'desc': 'PHP 7.0-7.4 存在整数溢出漏洞，可尝试手动修改序列化长度字段为极大值（如 0x7fffffff）。',
                'color': '#FF4500'
            })
        
        if 'superglobal_pollution' in features.tags:
            warnings.append({
                'title': '检测到超全局变量赋值',
                'desc': '可能通过污染 $_SERVER[\'PHP_VALUE\'] 等实现配置劫持，当前版本无法自动编排多阶段利用，建议手动构造前置污染链。',
                'color': '#FF4500'
            })
        
        if not warnings:
            return
        
        warning_html = "<hr>"
        for w in warnings:
            warning_html += f"<div style='background-color: #FFF0F0; border-left: 4px solid {w['color']}; padding: 8px; margin-top: 8px;'>"
            warning_html += f"<b style='color: {w['color']}'>⚠️ {w['title']}</b><br>"
            warning_html += f"<span style='font-size: 11px; color: #666;'>{w['desc']}</span>"
            warning_html += "</div>"
        
        current_html = self.ai_result_view.toHtml()
        self.ai_result_view.setHtml(current_html + warning_html)
        
        # V3 UI集成: 当检测到 fiber 或 spl_fixed_array 标签时，添加实验性生成按钮
        if 'fiber' in features.tags or 'spl_fixed_array' in features.tags:
            # 移除旧按钮（如果存在）
            if hasattr(self, '_v3_exp_btn') and self._v3_exp_btn:
                self._v3_exp_btn.deleteLater()
            
            # 创建新按钮
            from PyQt6.QtWidgets import QPushButton
            self._v3_exp_btn = QPushButton("🧪 尝试 V3 实验性生成")
            self._v3_exp_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFA500;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    margin-top: 8px;
                }
                QPushButton:hover {
                    background-color: #FF8C00;
                }
            """)
            self._v3_exp_btn.clicked.connect(self.generate_v3_experimental)
            
            # 将按钮添加到 AI 审计区域的布局中
            # 查找 ai_group 的布局
            if hasattr(self, 'ai_group') and self.ai_group:
                layout = self.ai_group.layout()
                if layout:
                    layout.addWidget(self._v3_exp_btn)

    def generate_v3_experimental(self):
        """V3 UI集成: 强制调用 V3 策略生成实验性 Payload"""
        if not self.current_code:
            QMessageBox.warning(self, "提示", "请先加载 PHP 代码")
            return
        
        # 直接调用引擎，引擎内部已包含 V3 路由
        payload = self.engine.analyze_and_generate(self.current_code)
        
        # 标注为实验性
        self.payload_view.setPlaceholderText("⚠️ 实验性 Payload - 请验证目标环境 PHP 版本")
        self.original_payload = payload
        self.current_payload = str(payload)
        self.payload_view.setText(self.current_payload)
        
        # 在 AI 审计区域显示提示
        exp_html = "<hr><div style='background-color: #FFFACD; border-left: 4px solid #FFA500; padding: 8px; margin-top: 8px;'>"
        exp_html += "<b style='color: #FF8C00'>🧪 V3 实验性 Payload 已生成</b><br>"
        exp_html += "<span style='font-size: 11px; color: #666;'>"
        exp_html += "此 Payload 使用了高级利用技术（如 Fiber 协程或 SplFixedArray 溢出）。"
        exp_html += "请确保目标环境支持相应的 PHP 版本和特性。"
        exp_html += "</span></div>"
        current_html = self.ai_result_view.toHtml()
        self.ai_result_view.setHtml(current_html + exp_html)

    def send_http_request(self):
        """发送 HTTP 请求并展示结果"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "提示", "请输入目标 URL")
            return
        
        # V3 Bug修复: 直接从输出框获取原始 Payload，确保无污染
        raw_payload = self.payload_view.toPlainText()
        
        # 如果用户选择了混淆方式（非“原始”），则发送原始未混淆 Payload
        if self.obf_combo.currentIndex() != 0:
            # 若用户选择了混淆方式，但希望发送原始 Payload，使用 self.original_payload
            if self.original_payload:
                raw_payload = self.original_payload
            else:
                # 如果原始 Payload 丢失，则使用输出框内容（可能已混淆）
                pass
        
        # V3 Bug补充修复: 如果 payload 以 "data=" 开头，则去除前缀
        if raw_payload.startswith('data='):
            raw_payload = raw_payload[5:]
        
        method = self.http_method_combo.currentText()
        param_name = self.param_name_input.text().strip()
        
        client = HttpClient()
        # 关键修复：确保 payload 参数为普通字符串，且不是预览注释
        result = client.send(url, method, str(raw_payload), param_name)
        
        if result.get('success'):
            resp_text = f"Status: {result['status']}\n\nHeaders:\n{result['headers']}\n\nBody:\n{result['body']}"
            QMessageBox.information(self, "✅ 请求成功", resp_text)
        else:
            QMessageBox.critical(self, "❌ 请求失败", result.get('error', 'Unknown error'))

    def preview_http_request(self):
        """预览原始 HTTP 请求报文"""
        url = self.url_input.text()
        if not url:
            QMessageBox.warning(self, "提示", "请先输入目标 URL")
            return
            
        payload = self.payload_view.toPlainText()
        method = self.http_method_combo.currentText()
        param_name = self.param_name_input.text()
        
        raw_request = HttpClient.build_raw_request(url, method, payload, param_name)
        
        from ui_v2.widgets.http_preview_dialog import HTTPPreviewDialog
        dialog = HTTPPreviewDialog(raw_request, self)
        dialog.exec()

    def clear(self):
        """清空当前视图的所有内容"""
        self.code_view.clear()
        self.structure_tree.clear()
        self.payload_view.clear()
        self.ai_result_view.clear()
        self.url_input.clear()
        self.param_name_input.setText("data")
        self.current_code = ""
        self.original_payload = ""
        self.current_payload = ""
        self.generate_btn.setEnabled(False)

    def on_obfuscate_method_changed(self, index):
        """根据选择的混淆方式更新 Payload 显示"""
        if not self.original_payload:
            return
            
        method_map = {
            0: None, # 原始
            1: "base64",
            2: "gzip_base64",
            3: "rot13"
        }
        
        method = method_map.get(index)
        if method is None:
            self.current_payload = str(self.original_payload)
            self.payload_view.setText(self.current_payload)
        else:
            obfuscator = PayloadObfuscator()
            obfuscated = obfuscator.obfuscate(str(self.original_payload), method)
            self.current_payload = str(obfuscated)
            self.payload_view.setText(self.current_payload)

    def on_property_changed(self, item, column):
        """处理属性值修改并重新生成 Payload"""
        if column == 2 and item.parent() and item.parent().text(0) == "属性列表":
            # 简化：目前仅更新 UI，实际 Payload 生成需要重新运行引擎逻辑
            # 在实际生产中，这里应触发局部重算
            self.start_analysis()

    def highlight_php_syntax(self):
        """基础 PHP 语法高亮"""
        text = self.code_view.toPlainText()
        cursor = self.code_view.textCursor()
        
        # 简单的正则匹配关键字
        keywords = ['class', 'function', 'public', 'private', 'protected', 'if', 'else', 'return']
        for kw in keywords:
            pattern = re.compile(r'\b' + kw + r'\b')
            for match in pattern.finditer(text):
                fmt = QTextCharFormat()
                fmt.setForeground(QColor("#569CD6")) # VSCode Blue
                cursor.setPosition(match.start())
                cursor.setPosition(match.end(), QTextCursor.MoveMode.KeepAnchor)
                cursor.mergeCharFormat(fmt)
