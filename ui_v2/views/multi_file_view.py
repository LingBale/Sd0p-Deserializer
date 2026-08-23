from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTreeWidget, QTreeWidgetItem, QHeaderView, QFileDialog, QLabel, QSplitter,
                             QTextEdit, QMessageBox, QMenu)
from PyQt6.QtCore import Qt
import os

class MultiFileView(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.all_classes = []
        self.class_by_file = {}  # 保存文件与类的映射
        self.current_payload = ""  # 当前生成的 Payload
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 顶部工具栏
        toolbar = QHBoxLayout()
        self.upload_btn = QPushButton("📂 上传文件夹")
        self.upload_btn.clicked.connect(self.load_directory)
        
        # V3 功能增强: 新增生成 Payload 按钮
        self.gen_payload_btn = QPushButton("⚡ 生成 Payload")
        self.gen_payload_btn.setEnabled(False)
        self.gen_payload_btn.clicked.connect(self.generate_payload_for_best_class)
        
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.clicked.connect(self.clear)
        
        toolbar.addWidget(self.upload_btn)
        toolbar.addWidget(self.gen_payload_btn)
        toolbar.addWidget(self.clear_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # 主分割视图：左侧文件树，右侧垂直分割（图谱 + Payload）
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：文件与类结构树
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["名称", "类型", "路径"])
        self.file_tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # V3 功能增强: 启用右键菜单
        self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_tree.customContextMenuRequested.connect(self.show_context_menu)
        
        # 右侧：垂直分割器（上半部分图谱，下半部分 Payload 输出）
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 上半部分：复用 PopChainView 展示全局调用图
        from .pop_chain_view import PopChainView
        self.global_graph_view = PopChainView(self.engine)
        
        # 下半部分：Payload 输出区域
        payload_container = QWidget()
        payload_layout = QVBoxLayout(payload_container)
        
        # Payload 显示框
        self.payload_output = QTextEdit()
        self.payload_output.setReadOnly(True)
        self.payload_output.setPlaceholderText("点击'生成 Payload'按钮或右键选择类来生成 Payload")
        
        # V3 功能增强: 复制按钮布局（原始 + Base64）
        btn_layout = QHBoxLayout()
        self.copy_btn = QPushButton("📋 复制 Payload")
        self.copy_btn.clicked.connect(self.copy_payload_to_clipboard)
        self.copy_base64_btn = QPushButton("🔐 复制 Base64")
        self.copy_base64_btn.clicked.connect(self.copy_base64_to_clipboard)
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.copy_base64_btn)
        btn_layout.addStretch()
        
        payload_layout.addWidget(self.payload_output)
        payload_layout.addLayout(btn_layout)
        
        right_splitter.addWidget(self.global_graph_view)
        right_splitter.addWidget(payload_container)
        right_splitter.setStretchFactor(0, 2)  # 图谱占更多空间
        right_splitter.setStretchFactor(1, 1)  # Payload 占较少空间
        
        main_splitter.addWidget(self.file_tree)
        main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)
        
        layout.addWidget(main_splitter)
        self.setLayout(layout)

    def load_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择包含 PHP 文件的文件夹")
        if dir_path:
            from core_v2.parser.multi_file import MultiFileAnalyzer
            analyzer = MultiFileAnalyzer()
            
            # 简单的进度提示
            self.file_tree.clear()
            root_item = QTreeWidgetItem(["正在解析...", "", ""])
            self.file_tree.addTopLevelItem(root_item)
            
            def update_progress(msg):
                root_item.setText(0, msg)
                QApplication.processEvents() # 刷新 UI
            
            from PyQt6.QtWidgets import QApplication
            self.all_classes = analyzer.analyze_directory(dir_path, progress_callback=update_progress)
            
            self.update_file_tree(dir_path, self.all_classes)
            self.global_graph_view.update_graph(self.all_classes)
            
            # V3 功能增强: 启用生成按钮
            if self.all_classes:
                self.gen_payload_btn.setEnabled(True)

    def update_file_tree(self, root_path, classes):
        self.file_tree.clear()
        self.class_by_file = {}  # V3 功能增强: 保存映射
        
        for cls in classes:
            file_path = cls.source_file or "Unknown"
            if file_path not in self.class_by_file:
                self.class_by_file[file_path] = []
            self.class_by_file[file_path].append(cls)

        for file_path, cls_list in self.class_by_file.items():
            rel_path = os.path.relpath(file_path, root_path)
            file_item = QTreeWidgetItem([rel_path, "File", file_path])
            self.file_tree.addTopLevelItem(file_item)
            
            for cls in cls_list:
                cls_item = QTreeWidgetItem([cls.name, "Class", ""])
                # V3 功能增强: 将类对象绑定到节点数据
                cls_item.setData(0, Qt.ItemDataRole.UserRole, cls)
                file_item.addChild(cls_item)
                
                # 显示属性
                prop_item = QTreeWidgetItem(["Properties", "", ""])
                cls_item.addChild(prop_item)
                for name, prop in cls.properties.items():
                    QTreeWidgetItem(prop_item, [name, "Property", prop.visibility])

    def clear(self):
        """清空多文件分析结果"""
        self.file_tree.clear()
        self.all_classes = []
        self.class_by_file = {}
        self.current_payload = ""
        self.payload_output.clear()
        self.gen_payload_btn.setEnabled(False)
        if hasattr(self.global_graph_view, 'figure'):
            self.global_graph_view.clear()
    
    # ==================== V3 功能增强: Payload 生成相关方法 ====================
    
    def _select_best_entry_class(self):
        """V3 功能增强: 选择最可能的入口类（启发式）"""
        # 优先选择包含 __destruct 且属性为 public 的类
        for cls in self.all_classes:
            if '__destruct' in cls.methods:
                has_public_prop = any(p.visibility == 'public' for p in cls.properties.values())
                if has_public_prop:
                    return cls
        
        # 其次选择包含 __destruct 的类
        for cls in self.all_classes:
            if '__destruct' in cls.methods:
                return cls
        
        # 若无，则返回第一个类
        return self.all_classes[0] if self.all_classes else None
    
    def _build_full_code(self):
        """V3 功能增强: 读取所有已解析文件的原始内容并拼接"""
        code_parts = []
        for file_path in self.class_by_file.keys():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code_parts.append(f.read())
            except Exception as e:
                import logging
                logging.warning(f"Failed to read file {file_path}: {e}")
        return '\n'.join(code_parts)
    
    def generate_payload_for_class(self, target_class):
        """V3 功能增强: 为指定类生成 Payload"""
        if not target_class:
            QMessageBox.warning(self, "提示", "未找到目标类")
            return
        
        # 构建完整代码
        full_code = self._build_full_code()
        if not full_code:
            QMessageBox.warning(self, "提示", "无法读取源代码文件")
            return
        
        try:
            # 调用引擎生成 Payload
            payload = self.engine.analyze_and_generate(full_code)
            self.current_payload = payload
            self.payload_output.setText(payload)
            
            # V3 功能增强: 同步到主窗口（若存在）
            main_window = self.window()
            if main_window and hasattr(main_window, 'current_payload'):
                main_window.current_payload = payload
            
            QMessageBox.information(self, "✅ 生成成功", f"已为类 '{target_class.name}' 生成 Payload")
        except Exception as e:
            QMessageBox.critical(self, "❌ 生成失败", f"错误: {str(e)}")
    
    def generate_payload_for_best_class(self):
        """V3 功能增强: 为最佳入口类生成 Payload"""
        best_class = self._select_best_entry_class()
        if best_class:
            self.generate_payload_for_class(best_class)
        else:
            QMessageBox.warning(self, "提示", "未找到可分析的类")
    
    def show_context_menu(self, position):
        """V3 功能增强: 显示右键菜单"""
        item = self.file_tree.itemAt(position)
        if not item:
            return
        
        # 检查是否为类节点
        cls = item.data(0, Qt.ItemDataRole.UserRole)
        if not cls:
            return
        
        # 创建菜单
        menu = QMenu(self)
        gen_action = menu.addAction("⚡ 生成 Payload")
        
        action = menu.exec(self.file_tree.viewport().mapToGlobal(position))
        if action == gen_action:
            self.generate_payload_for_class(cls)
    
    def copy_payload_to_clipboard(self):
        """V3 功能增强: 复制 Payload 到剪贴板（健壮版本）"""
        try:
            payload = self.payload_output.toPlainText().strip()
            if not payload:
                QMessageBox.warning(self, "提示", "没有可复制的 Payload")
                return
            
            from PyQt6.QtGui import QGuiApplication
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(payload)
            QMessageBox.information(self, "✅ 复制成功", "Payload 已复制到剪贴板！")
        except Exception as e:
            QMessageBox.critical(self, "❌ 错误", f"复制失败: {str(e)}")
    
    def copy_base64_to_clipboard(self):
        """V3 功能增强: 复制 Base64 编码的 Payload 到剪贴板"""
        try:
            import base64
            payload = self.payload_output.toPlainText().strip()
            if not payload:
                QMessageBox.warning(self, "提示", "没有可复制的 Payload")
                return
            
            encoded = base64.b64encode(payload.encode('utf-8')).decode('ascii')
            from PyQt6.QtGui import QGuiApplication
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(encoded)
            QMessageBox.information(self, "✅ 复制成功", f"Base64 编码的 Payload 已复制到剪贴板！\n长度: {len(encoded)} 字符")
        except Exception as e:
            QMessageBox.critical(self, "❌ 错误", f"Base64 复制失败: {str(e)}")
