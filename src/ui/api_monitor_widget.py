"""
API监控界面组件
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTabWidget, QTableWidget, QTableWidgetItem,
    QFrame, QPushButton
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor, QFont
from datetime import datetime
from src.utils.api_monitor import APIMonitor

class APIMonitorWidget(QWidget):
    """API监控界面组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_monitor = APIMonitor()
        self.init_ui()
        self.setup_timer()
        
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("API使用监控")
        title.setFont(QFont("SF Pro Display", 18, QFont.Bold))
        title.setStyleSheet("color: #1D1D1F;")
        layout.addWidget(title)
        
        # 总计信息卡片
        total_info = QWidget()
        total_info.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 15px;
            }
            QLabel {
                color: #1D1D1F;
                font-size: 14px;
            }
        """)
        total_layout = QHBoxLayout(total_info)
        total_layout.setContentsMargins(20, 15, 20, 15)
        
        self.total_calls = QLabel()
        self.total_tokens = QLabel()
        self.total_cost = QLabel()
        
        for label in [self.total_calls, self.total_tokens, self.total_cost]:
            label.setFont(QFont("SF Pro Text", 14))
        
        total_layout.addWidget(self.total_calls)
        total_layout.addWidget(self.total_tokens)
        total_layout.addWidget(self.total_cost)
        
        layout.addWidget(total_info)
        
        # 选项卡
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: white;
                border-radius: 15px;
            }
            QTabBar::tab {
                background-color: transparent;
                padding: 10px 20px;
                margin-right: 5px;
                border: none;
                font-size: 14px;
                color: #1D1D1F;
            }
            QTabBar::tab:selected {
                color: #007AFF;
                border-bottom: 2px solid #007AFF;
            }
            QTabBar::tab:hover:!selected {
                color: #0066CC;
            }
        """)
        
        # 每日统计
        daily_tab = QWidget()
        daily_layout = QVBoxLayout(daily_tab)
        daily_layout.setContentsMargins(15, 15, 15, 15)
        self.daily_table = QTableWidget()
        self.setup_table(self.daily_table)
        daily_layout.addWidget(self.daily_table)
        
        # 每月统计
        monthly_tab = QWidget()
        monthly_layout = QVBoxLayout(monthly_tab)
        monthly_layout.setContentsMargins(15, 15, 15, 15)
        self.monthly_table = QTableWidget()
        self.setup_table(self.monthly_table)
        monthly_layout.addWidget(self.monthly_table)
        
        tab_widget.addTab(daily_tab, "每日统计")
        tab_widget.addTab(monthly_tab, "每月统计")
        
        layout.addWidget(tab_widget)
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setFont(QFont("SF Pro Text", 14))
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #0066CC;
            }
            QPushButton:pressed {
                background-color: #005299;
            }
        """)
        refresh_btn.clicked.connect(self.update_stats)
        layout.addWidget(refresh_btn)
        
    def setup_table(self, table):
        """设置表格样式"""
        table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: none;
                border-radius: 10px;
                gridline-color: #E5E5EA;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #E5E5EA;
            }
            QTableWidget::item:selected {
                background-color: #E5F3FF;
                color: #007AFF;
            }
            QHeaderView::section {
                background-color: white;
                padding: 12px 8px;
                border: none;
                font-weight: 600;
                color: #1D1D1F;
            }
        """)
        table.setShowGrid(False)
        table.setColumnCount(4)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        
    def setup_timer(self):
        """设置定时器"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(60000)  # 每分钟更新一次
        
    def update_stats(self):
        """更新统计信息"""
        try:
            # 更新总计信息
            total = self.api_monitor.get_total_usage()
            self.total_calls.setText(f"总调用次数: {total['total_calls']}")
            self.total_tokens.setText(f"总Token数: {total['total_tokens']}")
            self.total_cost.setText(f"总成本: ${total['total_cost']:.2f}")
            
            # 更新每日统计
            daily_stats = self.api_monitor.get_daily_usage()
            self.daily_table.setRowCount(len(daily_stats))
            
            for i, stats in enumerate(daily_stats):
                self.daily_table.setItem(i, 0, QTableWidgetItem(stats["date"]))
                self.daily_table.setItem(i, 1, QTableWidgetItem(str(stats["calls"])))
                self.daily_table.setItem(i, 2, QTableWidgetItem(str(stats["tokens"])))
                self.daily_table.setItem(i, 3, QTableWidgetItem(f"${stats['cost']:.2f}"))
                
                # 设置颜色（今天的数据高亮显示）
                if stats["date"] == datetime.now().strftime("%Y-%m-%d"):
                    for j in range(4):
                        item = self.daily_table.item(i, j)
                        item.setBackground(QColor("#e6f3ff"))
                        
            # 更新每月统计
            monthly_stats = self.api_monitor.get_monthly_usage()
            self.monthly_table.setRowCount(len(monthly_stats))
            
            for i, stats in enumerate(monthly_stats):
                self.monthly_table.setItem(i, 0, QTableWidgetItem(stats["month"]))
                self.monthly_table.setItem(i, 1, QTableWidgetItem(str(stats["calls"])))
                self.monthly_table.setItem(i, 2, QTableWidgetItem(str(stats["tokens"])))
                self.monthly_table.setItem(i, 3, QTableWidgetItem(f"${stats['cost']:.2f}"))
                
                # 设置颜色（当月的数据高亮显示）
                if stats["month"] == datetime.now().strftime("%Y-%m"):
                    for j in range(4):
                        item = self.monthly_table.item(i, j)
                        item.setBackground(QColor("#e6f3ff"))
                        
            # 调整列宽
            self.daily_table.resizeColumnsToContents()
            self.monthly_table.resizeColumnsToContents()
            
        except Exception as e:
            self.logger.error(f"更新API统计信息失败: {str(e)}")
            
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        self.update_stats()
        self.timer.start()
        
    def hideEvent(self, event):
        """隐藏事件"""
        super().hideEvent(event)
        self.timer.stop()
        
    def closeEvent(self, event):
        """关闭事件"""
        self.timer.stop()
        super().closeEvent(event) 