from PyQt6.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QStatusBar, QComboBox
from core_v2.engine import Sd0pEngineV2
import core_v2.strategy.exploits  # 确保 SSRF/XXE/LFI 策略注册
from .views.dashboard_view import DashboardView
from .views.pop_chain_view import PopChainView
from .views.exploit_view import ExploitView
from .views.multi_file_view import MultiFileView
from .views.phar_view import PharView
from .views.advanced_tools_view import AdvancedToolsView

class V2MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sd0p-V3.5")
        self.resize(1200, 800)

        # 初始化 V2 引擎
        self.engine = Sd0pEngineV2()

        # 核心布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标签页系统
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 加载仪表盘（快捷生成）
        self.dashboard = DashboardView(self.engine)
        self.tabs.addTab(self.dashboard, "🚀 快捷生成")

        # 加载 POP 链分析视图
        self.pop_chain_view = PopChainView(self.engine)
        self.tabs.addTab(self.pop_chain_view, "🕸️ POP 链分析")

        # 加载漏洞利用生成视图
        self.exploit_view = ExploitView(self.engine)
        self.tabs.addTab(self.exploit_view, "💣 漏洞利用")

        # 加载多文件分析视图
        self.multi_file_view = MultiFileView(self.engine)
        self.tabs.addTab(self.multi_file_view, "📁 多文件分析")

        # 加载 PHAR 生成工具
        self.phar_view = PharView(self.engine)
        self.tabs.addTab(self.phar_view, "📦 PHAR 生成")

        # 加载高级工具模块
        self.advanced_view = AdvancedToolsView(self.engine)
        self.tabs.addTab(self.advanced_view, "🔧 高级工具")
