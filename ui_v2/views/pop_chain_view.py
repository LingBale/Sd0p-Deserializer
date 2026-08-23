from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout
import networkx as nx
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# V3 样式优化: 设置中文字体回退链
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# V3 工具栏中文化: 自定义汉化工具栏类
try:
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
    
    class ChineseNavigationToolbar(NavigationToolbar):
        """汉化版 matplotlib 工具栏"""
        # 覆盖工具项定义，仅修改提示文本（tooltip），保持内部标识不变
        toolitems = [
            ('Home', '复位', 'home', 'home'),
            ('Back', '后退', 'back', 'back'),
            ('Forward', '前进', 'forward', 'forward'),
            (None, None, None, None),
            ('Pan', '平移', 'move', 'pan'),
            ('Zoom', '缩放', 'zoom_to_rect', 'zoom'),
            ('Subplots', '子图配置', 'subplots', 'configure_subplots'),
            (None, None, None, None),
            ('Save', '保存图片', 'filesave', 'save_figure'),
        ]

        def _mouse_event_to_message(self, event):
            """汉化状态栏坐标显示"""
            if event.inaxes:
                return f'X={event.xdata:.4f}  Y={event.ydata:.4f}'
            return ''
except ImportError:
    ChineseNavigationToolbar = None

class PopChainView(QWidget):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 顶部工具栏
        toolbar = QHBoxLayout()
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.clicked.connect(self.clear)
        toolbar.addWidget(self.clear_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 创建 matplotlib Figure 和 Canvas - 深色主题
        self.figure = Figure(figsize=(12, 9), dpi=100, facecolor='#1e1e1e')
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # V3 工具栏中文化: 使用自定义汉化工具栏
        try:
            if ChineseNavigationToolbar:
                self.toolbar = ChineseNavigationToolbar(self.canvas, self)
            else:
                from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
                self.toolbar = NavigationToolbar(self.canvas, self)
            layout.addWidget(self.toolbar)
        except ImportError:
            self.toolbar = None
        
        self.setLayout(layout)

    def update_graph(self, classes):
        """更新 POP 链图谱 - 使用 matplotlib + networkx 力导向布局（深色主题优化版）"""
        from core_v2.chain.analyzer import CallGraphBuilder
        builder = CallGraphBuilder()
        graph_data = builder.build(classes)
        
        if not graph_data['nodes']:
            self.clear()
            return
        
        # 构建 networkx 图
        G = nx.DiGraph()
        for node in graph_data['nodes']:
            G.add_node(node['id'], label=node.get('label', node['id']))
        
        for edge in graph_data['edges']:
            G.add_edge(edge['from'], edge['to'], label=edge.get('label', ''))
        
        # V3 样式优化: 使用更舒展的力导向布局
        try:
            pos = nx.spring_layout(G, k=3, iterations=100, seed=42)
        except Exception:
            pos = nx.circular_layout(G)
        
        # 清空并重新绘制
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#1e1e1e')  # 坐标轴背景色
        
        # V3 样式优化: 定义精致配色方案
        NODE_COLOR = '#2d5a8c'          # 深蓝色节点
        NODE_BORDER_COLOR = '#4a90e2'   # 亮蓝边框
        NODE_TEXT_COLOR = 'white'       # 白色文字
        EDGE_COLOR = '#6c8ebf'          # 灰蓝色边
        EDGE_LABEL_COLOR = '#f0c674'    # 淡黄色边标签
        EDGE_LABEL_BG = '#2d2d2d'       # 深灰背景
        
        # 绘制节点 - 增加阴影效果（通过多层绘制模拟）
        nx.draw_networkx_nodes(
            G, pos, 
            ax=ax, 
            node_color=NODE_COLOR,
            node_size=1200,
            edgecolors=NODE_BORDER_COLOR,
            linewidths=2.5,
            alpha=0.95
        )
        
        # 绘制节点标签 - 加粗白字
        node_labels = {node: data['label'] for node, data in G.nodes(data=True)}
        nx.draw_networkx_labels(
            G, pos, 
            labels=node_labels,
            ax=ax, 
            font_size=11,
            font_weight='bold',
            font_color=NODE_TEXT_COLOR,
            verticalalignment='center',
            horizontalalignment='center'
        )
        
        # 绘制边 - 带弧度的箭头
        nx.draw_networkx_edges(
            G, pos, 
            ax=ax, 
            arrowstyle='-|>', 
            arrowsize=18, 
            edge_color=EDGE_COLOR,
            width=1.5,
            connectionstyle='arc3,rad=0.15',
            alpha=0.8
        )
        
        # 绘制边标签 - 半透明背景
        edge_labels = {(u, v): d['label'] for u, v, d in G.edges(data=True) if d.get('label')}
        if edge_labels:
            nx.draw_networkx_edge_labels(
                G, pos, 
                edge_labels=edge_labels, 
                ax=ax, 
                font_size=9,
                font_color=EDGE_LABEL_COLOR,
                bbox=dict(
                    boxstyle='round,pad=0.4', 
                    facecolor=EDGE_LABEL_BG, 
                    alpha=0.85,
                    edgecolor='none'
                )
            )
        
        # V3 样式优化: 添加中文标题
        ax.set_title('POP 链调用关系图谱', 
                    fontsize=16, 
                    fontweight='bold', 
                    color='white',
                    pad=25)
        
        ax.axis('off')
        
        # 调整布局，避免裁剪
        self.figure.tight_layout()
        
        # 刷新画布
        self.canvas.draw()

    def clear(self):
        """清空调用图 - 深色主题版"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#1e1e1e')
        ax.text(0.5, 0.5, '暂无 POP 链数据\n请上传并分析 PHP 代码以查看图谱', 
                ha='center', va='center', fontsize=13, color='#888888',
                fontweight='bold')
        ax.axis('off')
        self.canvas.draw()
