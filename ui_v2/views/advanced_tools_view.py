from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTextEdit, QLabel, QComboBox, QTabWidget, QMessageBox, QLineEdit, 
                             QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from core_v2.utils.session_converter import SessionConverter
from core_v2.utils.string_escape import StringEscapeCalculator
from core_v2.composer.analyzer import ComposerAnalyzer
import re
import json

class AdvancedToolsView(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        # 1. Session 转换工具
        session_tab = QWidget()
        s_layout = QVBoxLayout()
        self.session_input = QTextEdit()
        self.session_input.setPlaceholderText("输入 PHP Session 字符串...")
        self.session_combo = QComboBox()
        self.session_combo.addItems(["php -> php_serialize", "php_serialize -> php", "to php_binary"])
        convert_btn = QPushButton("🔄 执行转换")
        convert_btn.clicked.connect(self.convert_session)
        self.session_output = QTextEdit()
        self.session_output.setReadOnly(True)
        
        s_layout.addWidget(QLabel("输入:"))
        s_layout.addWidget(self.session_input)
        s_layout.addWidget(self.session_combo)
        s_layout.addWidget(convert_btn)
        s_layout.addWidget(QLabel("输出:"))
        s_layout.addWidget(self.session_output)
        session_tab.setLayout(s_layout)
        
        # 2. 序列化格式化工具
        fmt_tab = QWidget()
        f_layout = QVBoxLayout()
        self.fmt_input = QTextEdit()
        self.fmt_input.setPlaceholderText("输入 O:... 序列化字符串...")
        fmt_btn = QPushButton("✨ 美化 / 验证")
        fmt_btn.clicked.connect(self.format_serialized)
        self.fmt_output = QTextEdit()
        self.fmt_output.setReadOnly(True)
        
        f_layout.addWidget(QLabel("输入:"))
        f_layout.addWidget(self.fmt_input)
        f_layout.addWidget(fmt_btn)
        f_layout.addWidget(QLabel("结果:"))
        f_layout.addWidget(self.fmt_output)
        fmt_tab.setLayout(f_layout)
        
        self.tabs.addTab(session_tab, "Session 转换")
        self.tabs.addTab(fmt_tab, "序列化格式化")
        
        # 3. 正则测试器
        regex_tab = QWidget()
        r_layout = QVBoxLayout()
        self.regex_input = QLineEdit()
        self.regex_input.setPlaceholderText("输入正则表达式 (如: /pattern/)")
        self.test_text = QTextEdit()
        self.test_text.setPlaceholderText("输入测试文本...")
        test_btn = QPushButton("🔍 测试匹配")
        test_btn.clicked.connect(self.test_regex)
        self.regex_result = QTextEdit()
        self.regex_result.setReadOnly(True)
        
        r_layout.addWidget(QLabel("正则表达式:"))
        r_layout.addWidget(self.regex_input)
        r_layout.addWidget(QLabel("测试文本:"))
        r_layout.addWidget(self.test_text)
        r_layout.addWidget(test_btn)
        r_layout.addWidget(QLabel("结果:"))
        r_layout.addWidget(self.regex_result)
        regex_tab.setLayout(r_layout)
        
        # 4. __wakeup 版本检测
        ver_tab = QWidget()
        v_layout = QVBoxLayout()
        self.ver_input = QLineEdit()
        self.ver_input.setPlaceholderText("例如: 7.4.20")
        check_btn = QPushButton("🛡️ 检查 CVE-2016-7124")
        check_btn.clicked.connect(self.check_wakeup_version)
        self.ver_result = QLabel("")
        
        v_layout.addWidget(QLabel("PHP 版本号:"))
        v_layout.addWidget(self.ver_input)
        v_layout.addWidget(check_btn)
        v_layout.addWidget(self.ver_result)
        ver_tab.setLayout(v_layout)
        
        # 5. 逃逸长度计算器
        esc_tab = QWidget()
        e_layout = QVBoxLayout()
        self.esc_input = QTextEdit()
        self.esc_combo = QComboBox()
        self.esc_combo.addItems(["addslashes", "mysql_real_escape_string"])
        calc_btn = QPushButton("📏 计算长度变化")
        calc_btn.clicked.connect(self.calculate_escape)
        self.esc_output = QTextEdit()
        self.esc_output.setReadOnly(True)
        
        e_layout.addWidget(QLabel("原始字符串:"))
        e_layout.addWidget(self.esc_input)
        e_layout.addWidget(self.esc_combo)
        e_layout.addWidget(calc_btn)
        e_layout.addWidget(QLabel("结果:"))
        e_layout.addWidget(self.esc_output)
        esc_tab.setLayout(e_layout)
        
        self.tabs.addTab(regex_tab, "正则测试")
        self.tabs.addTab(ver_tab, "__wakeup 检测")
        self.tabs.addTab(esc_tab, "逃逸计算器")
        
        # 6. Composer 依赖分析
        comp_tab = QWidget()
        c_layout = QVBoxLayout()
        self.comp_dir_input = QLineEdit()
        browse_btn = QPushButton("📂 选择项目目录")
        browse_btn.clicked.connect(self.browse_composer_dir)
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("项目目录:"))
        dir_layout.addWidget(self.comp_dir_input)
        dir_layout.addWidget(browse_btn)
        
        self.comp_table = QTableWidget()
        self.comp_table.setColumnCount(3)
        self.comp_table.setHorizontalHeaderLabels(["包名", "版本", "类型"])
        self.comp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        analyze_btn = QPushButton("🔍 开始分析")
        analyze_btn.clicked.connect(self.start_composer_analysis)
        
        c_layout.addLayout(dir_layout)
        c_layout.addWidget(analyze_btn)
        c_layout.addWidget(self.comp_table)
        comp_tab.setLayout(c_layout)
        self.tabs.addTab(comp_tab, "Composer 分析")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def convert_session(self):
        input_str = self.session_input.toPlainText().strip()
        method = self.session_combo.currentText()
        
        if not input_str:
            return
            
        try:
            if "php -> php_serialize" in method:
                res = SessionConverter.php_to_serialize(input_str)
            elif "php_serialize -> php" in method:
                res = SessionConverter.serialize_to_php(input_str)
            else:
                res = SessionConverter.to_binary(input_str)
            self.session_output.setText(res)
        except Exception as e:
            QMessageBox.critical(self, "错误", str(e))

    def format_serialized(self):
        input_str = self.fmt_input.toPlainText().strip()
        # 简化：目前仅做简单的换行处理，后续可接入 advanced/serialization_formatter.py
        self.fmt_output.setText(input_str.replace(";", ";\n").replace("{", "{\n  ").replace("}", "\n}"))

    def test_regex(self):
        """测试正则表达式匹配
        
        支持 PHP/JavaScript 风格的 /pattern/flags 格式
        自动去除分隔符并提取标志（i, s, m）
        """
        raw_pattern = self.regex_input.text().strip()
        text = self.test_text.toPlainText()
        
        if not raw_pattern:
            self.regex_result.setText("请输入正则表达式")
            return
        
        if not text:
            self.regex_result.setText("请输入测试文本")
            return

        # 预处理：支持 /pattern/flags 格式
        pattern = raw_pattern
        flags = 0
        
        # 检测是否使用 / 作为分隔符
        if raw_pattern.startswith('/') and raw_pattern.rfind('/') > 0:
            last_slash = raw_pattern.rfind('/')
            pattern = raw_pattern[1:last_slash]
            flag_str = raw_pattern[last_slash + 1:]
            
            # 提取标志
            if 'i' in flag_str:
                flags |= re.IGNORECASE
            if 's' in flag_str:
                flags |= re.DOTALL
            if 'm' in flag_str:
                flags |= re.MULTILINE
        
        try:
            matches = re.findall(pattern, text, flags=flags)
            
            if not matches:
                res_str = f"❌ 未找到匹配项\n\n正则表达式: {pattern}\n标志: {self._format_flags(flags)}"
            else:
                res_str = f"✅ 找到 {len(matches)} 个匹配:\n\n正则表达式: {pattern}\n标志: {self._format_flags(flags)}\n\n匹配结果:\n"
                for i, m in enumerate(matches, 1):
                    if isinstance(m, tuple):
                        # 如果有捕获组，显示为元组
                        res_str += f"{i}. {m}\n"
                    else:
                        res_str += f"{i}. {m}\n"
            
            self.regex_result.setText(res_str)
        except Exception as e:
            self.regex_result.setText(f"❌ 正则错误: {type(e).__name__}: {str(e)}\n\n请检查正则表达式语法")
    
    def _format_flags(self, flags):
        """格式化正则标志为可读字符串"""
        flag_list = []
        if flags & re.IGNORECASE:
            flag_list.append('i (忽略大小写)')
        if flags & re.DOTALL:
            flag_list.append('s (点号匹配换行)')
        if flags & re.MULTILINE:
            flag_list.append('m (多行模式)')
        
        return ', '.join(flag_list) if flag_list else '无'

    def check_wakeup_version(self):
        ver_str = self.ver_input.text()
        if not ver_str:
            return
        try:
            parts = list(map(int, ver_str.split('.')))
            # CVE-2016-7124: PHP 5 < 5.6.25 or PHP 7 < 7.0.10
            is_vuln = False
            if parts[0] == 5 and parts[1] < 6:
                is_vuln = True
            elif parts[0] == 5 and parts[1] == 6 and parts[2] < 25:
                is_vuln = True
            elif parts[0] == 7 and parts[1] == 0 and parts[2] < 10:
                is_vuln = True
            
            msg = "⚠️ 受影响 (存在 __wakeup 绕过漏洞)" if is_vuln else "✅ 不受影响"
            color = "red" if is_vuln else "green"
            self.ver_result.setText(f"<b style='color:{color}'>{msg}</b>")
        except:
            self.ver_result.setText("版本号格式错误")

    def calculate_escape(self):
        original = self.esc_input.toPlainText()
        method = self.esc_combo.currentText()
        result = StringEscapeCalculator.calculate(original, method)
        
        output = f"原始长度: {result['original_len']}\n"
        output += f"逃逸后长度: {result['escaped_len']}\n"
        output += f"长度增加: +{result['diff']}\n\n"
        output += f"逃逸结果:\n{result['escaped_str']}"
        self.esc_output.setText(output)

    def browse_composer_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择包含 composer.json 的目录")
        if dir_path:
            self.comp_dir_input.setText(dir_path)

    def start_composer_analysis(self):
        dir_path = self.comp_dir_input.text()
        if not dir_path:
            QMessageBox.warning(self, "提示", "请先选择项目目录")
            return
        
        analyzer = ComposerAnalyzer()
        try:
            deps = analyzer.analyze(dir_path)
            self.comp_table.setRowCount(len(deps))
            for i, dep in enumerate(deps):
                self.comp_table.setItem(i, 0, QTableWidgetItem(dep['name']))
                self.comp_table.setItem(i, 1, QTableWidgetItem(dep['version']))
                self.comp_table.setItem(i, 2, QTableWidgetItem(dep['type']))
            QMessageBox.information(self, "成功", f"共找到 {len(deps)} 个依赖项")
        except Exception as e:
            QMessageBox.critical(self, "分析失败", str(e))
