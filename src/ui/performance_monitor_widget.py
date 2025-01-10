"""
性能监控面板组件
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QFrame, QTabWidget
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from src.utils.performance import PerformanceMonitor, MemoryManager
from collections import deque
import time
import logging

class PerformanceChart(QChartView):
    """性能趋势图表"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.chart = QChart()
        self.setChart(self.chart)
        
        # 设置标题
        self.chart.setTitle(title)
        self.chart.setTitleFont(self.font())
        
        # 创建数据系列
        self.series = QLineSeries()
        self.chart.addSeries(self.series)
        
        # 创建坐标轴
        self.axis_x = QValueAxis()
        self.axis_x.setRange(0, 60)  # 显示60秒的数据
        self.axis_x.setLabelFormat("%d")
        self.axis_x.setTitleText("时间 (秒)")
        
        self.axis_y = QValueAxis()
        self.axis_y.setRange(0, 100)
        self.axis_y.setLabelFormat("%d%")
        self.axis_y.setTitleText("使用率")
        
        self.chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.chart.addAxis(self.axis_y, Qt.AlignLeft)
        self.series.attachAxis(self.axis_x)
        self.series.attachAxis(self.axis_y)
        
        # 初始化数据队列
        self.data_queue = deque(maxlen=60)
        self.start_time = time.time()
        
    def add_data(self, value):
        """添加新数据点"""
        current_time = time.time() - self.start_time
        self.data_queue.append((current_time, value))
        
        # 更新数据系列
        points = [(t, v) for t, v in self.data_queue]
        self.series.clear()
        for t, v in points:
            self.series.append(t, v)
            
        # 调整X轴范围
        if points:
            min_time = max(0, points[-1][0] - 60)
            max_time = points[-1][0]
            self.axis_x.setRange(min_time, max_time)

class PerformanceMonitorWidget(QWidget):
    """性能监控面板组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitor = PerformanceMonitor()
        self.memory_manager = MemoryManager()
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建选项卡
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # 实时监控选项卡
        realtime_tab = QWidget()
        realtime_layout = QVBoxLayout(realtime_tab)
        
        # CPU 使用率
        cpu_layout = QHBoxLayout()
        self.cpu_label = QLabel("CPU:")
        self.cpu_label.setMinimumWidth(100)
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        cpu_layout.addWidget(self.cpu_label)
        cpu_layout.addWidget(self.cpu_progress)
        realtime_layout.addLayout(cpu_layout)
        
        # 内存使用率
        memory_layout = QHBoxLayout()
        self.memory_label = QLabel("内存:")
        self.memory_label.setMinimumWidth(100)
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        memory_layout.addWidget(self.memory_label)
        memory_layout.addWidget(self.memory_progress)
        realtime_layout.addLayout(memory_layout)
        
        # 内存详情
        self.memory_details = QLabel()
        self.memory_details.setStyleSheet("color: #666;")
        realtime_layout.addWidget(self.memory_details)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        
        cleanup_btn = QPushButton("清理内存")
        cleanup_btn.clicked.connect(self.cleanup_memory)
        cleanup_btn.setToolTip("尝试释放未使用的内存")
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.update_stats)
        
        button_layout.addWidget(cleanup_btn)
        button_layout.addWidget(refresh_btn)
        button_layout.addStretch()
        realtime_layout.addLayout(button_layout)
        
        # 添加实时监控选项卡
        tab_widget.addTab(realtime_tab, "实时监控")
        
        # 趋势图选项卡
        trends_tab = QWidget()
        trends_layout = QVBoxLayout(trends_tab)
        
        # CPU趋势图
        self.cpu_chart = PerformanceChart("CPU使用率趋势")
        trends_layout.addWidget(self.cpu_chart)
        
        # 内存趋势图
        self.memory_chart = PerformanceChart("内存使用率趋势")
        trends_layout.addWidget(self.memory_chart)
        
        # 添加趋势图选项卡
        tab_widget.addTab(trends_tab, "趋势图")
        
        # 设置样式
        self.setStyleSheet("""
            QProgressBar {
                text-align: center;
                min-height: 16px;
                max-height: 16px;
                border: none;
                border-radius: 8px;
                background: #f0f0f0;
                margin: 0px 5px;
            }
            QProgressBar::chunk {
                border-radius: 8px;
            }
            QPushButton {
                min-width: 80px;
                padding: 8px;
                border: none;
                border-radius: 4px;
                background: #007AFF;
                color: white;
            }
            QPushButton:hover {
                background: #0066CC;
            }
            QPushButton:pressed {
                background: #005299;
            }
            QTabWidget::pane {
                border: 1px solid #E5E5EA;
                border-radius: 8px;
                background: white;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 4px;
                border: none;
                background: transparent;
            }
            QTabBar::tab:selected {
                color: #007AFF;
                border-bottom: 2px solid #007AFF;
            }
            QTabBar::tab:hover:!selected {
                color: #0066CC;
            }
        """)
        
    def setup_timer(self):
        """设置定时器"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(5000)  # 每5秒更新一次
        
    def update_stats(self):
        """更新统计信息"""
        try:
            # 更新CPU使用率
            cpu_usage = self.monitor.get_cpu_usage()
            self.cpu_progress.setValue(int(cpu_usage))
            self.cpu_label.setText(f"CPU: {cpu_usage:.1f}%")
            self.cpu_chart.add_data(cpu_usage)
            
            # 更新内存使用情况
            memory = self.monitor.get_memory_usage()
            self.memory_progress.setValue(int(memory["percent"]))
            self.memory_label.setText(f"内存: {memory['percent']:.1f}%")
            self.memory_chart.add_data(memory["percent"])
            
            # 更新内存详情
            memory_details = []
            if memory["rss"] > 0:
                memory_details.append(f"物理内存: {memory['rss']:.1f}MB")
            if memory["vms"] > 0:
                memory_details.append(f"虚拟内存: {memory['vms']:.1f}MB")
            if memory["shared"] > 0:
                memory_details.append(f"共享内存: {memory['shared']:.1f}MB")
                
            self.memory_details.setText("  ".join(memory_details))
            
            # 设置进度条颜色
            self._update_progress_colors()
            
        except Exception as e:
            self.memory_details.setText(f"更新失败: {str(e)}")
            logging.error(f"更新性能统计失败: {str(e)}")
            
    def cleanup_memory(self):
        """清理内存"""
        try:
            self.memory_manager.cleanup()
            self.update_stats()
        except Exception as e:
            self.memory_details.setText(f"清理失败: {str(e)}")
            
    def _update_progress_colors(self):
        """更新进度条颜色"""
        def get_color_style(value):
            if value < 60:
                return "background: #34C759;"  # 绿色
            elif value < 80:
                return "background: #FF9500;"  # 橙色
            else:
                return "background: #FF3B30;"  # 红色
                
        cpu_value = self.cpu_progress.value()
        memory_value = self.memory_progress.value()
        
        self.cpu_progress.setStyleSheet(
            f"QProgressBar::chunk {{ {get_color_style(cpu_value)} }}"
        )
        self.memory_progress.setStyleSheet(
            f"QProgressBar::chunk {{ {get_color_style(memory_value)} }}"
        )
        
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        self.timer.start()
        
    def hideEvent(self, event):
        """隐藏事件"""
        super().hideEvent(event)
        self.timer.stop()
        
    def closeEvent(self, event):
        """关闭事件"""
        self.timer.stop()
        super().closeEvent(event) 