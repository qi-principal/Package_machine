"""
主窗口模块
提供应用程序的主界面
"""
import os
import sys
import asyncio
from typing import Optional, List, Dict
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, QTreeView,
    QProgressBar, QMessageBox, QComboBox, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDockWidget, QMenu, QAction, QTextEdit, QDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDateTime
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPalette, QColor

from src.core.file_system import FileSystemHandler
from src.core.file_filter import FileFilter
from src.core.file_mover import FileMover
from src.core.ai_classifier import AIClassifier
from src.core.category_storage import CategoryStorage
from src.config.config_manager import ConfigManager
from src.ui.settings_dialog import SettingsDialog
from src.ui.performance_monitor_widget import PerformanceMonitorWidget
from src.ui.api_monitor_widget import APIMonitorWidget
from src.utils.performance import performance_logger
from src.utils.error_handler import ErrorHandler
import logging

class ClassificationThread(QThread):
    """分类处理线程"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    
    def __init__(self, classifier: AIClassifier, files_info: List[Dict], target_base_dir: str, file_mover):
        super().__init__()
        self.classifier = classifier
        self.files_info = files_info
        self.target_base_dir = target_base_dir
        self.file_mover = file_mover
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        """运行分类处理"""
        try:
            # 增强文件信息
            self.status_updated.emit("正在准备文件信息...")
            logging.debug("开始增强文件信息...")
            enhanced_info = self.classifier.enhance_files_info(self.files_info)
            total_files = len(enhanced_info)
            logging.debug(f"文件信息增强完成，共 {total_files} 个文件")
            
            # 获取目标目录中已存在的分类
            existing_categories = []
            if os.path.exists(self.target_base_dir):
                existing_categories = [
                    d for d in os.listdir(self.target_base_dir)
                    if os.path.isdir(os.path.join(self.target_base_dir, d))
                ]
            logging.debug(f"发现已有分类目录: {existing_categories}")
            
            # 批量处理文件
            batch_size = 10
            results = {}
            
            for i in range(0, total_files, batch_size):
                batch = enhanced_info[i:i+batch_size]
                current_batch_size = len(batch)
                current_range = f"{i+1}-{min(i+current_batch_size, total_files)}"
                
                logging.debug(f"开始处理第 {current_range} 批次文件")
                self.status_updated.emit(
                    f"正在处理第 {current_range} 个文件 (共 {total_files} 个)..."
                )
                
                # 调用分类方法，传入existing_categories参数
                logging.debug("调用AI分类器...")
                batch_results = self.classifier.classify_files(batch, existing_categories)
                logging.debug(f"批次处理完成，获得 {len(batch_results)} 个结果")
                results.update(batch_results)
                
                progress = min(100, int((i + len(batch)) / total_files * 100))
                logging.debug(f"当前进度: {progress}%")
                self.progress.emit(progress)
                
            logging.debug("所有批次处理完成，准备更新结果...")
            self.status_updated.emit("分类完成，正在更新结果...")
            self.finished.emit(results)
            
        except Exception as e:
            logging.error(f"分类线程执行出错: {str(e)}")
            logging.debug("错误详情:", exc_info=True)
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化核心组件
        self.file_system = FileSystemHandler()
        self.file_filter = FileFilter()
        self.file_mover = FileMover()
        self.ai_classifier = AIClassifier(self.config_manager)
        self.category_storage = CategoryStorage()
        self.error_handler = ErrorHandler()
        
        # 初始化UI
        self.init_ui()
        self.load_config()
        
        # 初始化状态变量
        self.selected_directory = None
        self.classification_thread = None
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("智能文件分类系统")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置窗口背景色
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f7;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #0066CC;
            }
            QPushButton:pressed {
                background-color: #005299;
            }
            QLineEdit {
                border: 1px solid #E5E5EA;
                border-radius: 10px;
                padding: 8px 12px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #007AFF;
            }
            QComboBox {
                border: 1px solid #E5E5EA;
                border-radius: 10px;
                padding: 8px 12px;
                background-color: white;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(resources/down_arrow.png);
                width: 12px;
                height: 12px;
            }
            QTreeView, QTableWidget {
                background-color: white;
                border: 1px solid #E5E5EA;
                border-radius: 10px;
                padding: 5px;
            }
            QTreeView::item, QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #E5E5EA;
            }
            QTreeView::item:selected, QTableWidget::item:selected {
                background-color: #E5F3FF;
                color: #007AFF;
            }
            QHeaderView::section {
                background-color: #F5F5F7;
                padding: 8px;
                border: none;
                font-weight: 600;
            }
            QProgressBar {
                border: none;
                border-radius: 6px;
                background-color: #E5E5EA;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #007AFF;
                border-radius: 6px;
            }
            QDockWidget {
                border: 1px solid #E5E5EA;
                border-radius: 10px;
                background-color: white;
            }
            QDockWidget::title {
                background-color: #F5F5F7;
                padding: 8px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QMenuBar {
                background-color: white;
                border-bottom: 1px solid #E5E5EA;
            }
            QMenuBar::item {
                padding: 8px 12px;
                background-color: transparent;
            }
            QMenuBar::item:selected {
                background-color: #E5F3FF;
                color: #007AFF;
            }
            QMenu {
                background-color: white;
                border: 1px solid #E5E5EA;
                border-radius: 10px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 5px;
            }
            QMenu::item:selected {
                background-color: #E5F3FF;
                color: #007AFF;
            }
        """)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建顶部工具栏
        toolbar_layout = QHBoxLayout()
        self.create_toolbar(toolbar_layout)
        main_layout.addLayout(toolbar_layout)
        
        # 创建主要内容区域
        content_layout = QHBoxLayout()
        self.create_content_area(content_layout)
        main_layout.addLayout(content_layout)
        
        # 创建状态栏
        self.create_status_bar()
        
        # 创建性能监控面板
        self.create_performance_monitor()
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 添加表格双击事件
        self.category_table.itemDoubleClicked.connect(self.show_ai_response_detail)
        
    def create_toolbar(self, layout: QHBoxLayout):
        """创建工具栏"""
        # 选择文件夹按钮
        self.select_folder_btn = QPushButton("选择文件夹", self)
        self.select_folder_btn.clicked.connect(self.select_folder)
        layout.addWidget(self.select_folder_btn)
        
        # 文件类型过滤
        self.file_type_combo = QComboBox(self)
        self.file_type_combo.addItem("所有文件")
        self.file_type_combo.addItems(self.config_manager.get_allowed_extensions())
        layout.addWidget(QLabel("文件类型:"))
        layout.addWidget(self.file_type_combo)
        
        # 搜索框
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("搜索文件...")
        self.search_input.textChanged.connect(self.filter_files)
        layout.addWidget(self.search_input)
        
        # 开始分类按钮
        self.start_btn = QPushButton("开始分类", self)
        self.start_btn.clicked.connect(self.start_classification)
        layout.addWidget(self.start_btn)
        
        layout.addStretch()
        
    def create_content_area(self, layout: QHBoxLayout):
        """创建主要内容区域"""
        # 左侧布局（文件列表和日志区域）
        left_layout = QVBoxLayout()
        
        # 文件列表
        self.file_list = QTreeView(self)
        self.file_model = QStandardItemModel()
        self.file_model.setHorizontalHeaderLabels(["文件名", "大小", "修改时间"])
        self.file_list.setModel(self.file_model)
        self.file_list.setColumnWidth(0, 300)
        left_layout.addWidget(self.file_list)
        
        # 日志区域
        self.log_area = QTextEdit(self)
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(150)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #E5E5EA;
                border-radius: 10px;
                padding: 8px;
                font-family: monospace;
            }
        """)
        left_layout.addWidget(self.log_area)
        
        # 将左侧布局添加到主布局
        layout.addLayout(left_layout)
        
        # 分类结果表格
        self.category_table = QTableWidget(self)
        self.category_table.setColumnCount(4)
        self.category_table.setHorizontalHeaderLabels(["文件名", "分类", "置信度", "AI响应"])
        self.category_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.category_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.category_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.category_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(self.category_table)
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.hide()
        self.status_bar.addPermanentWidget(self.progress_bar)
        
    def create_performance_monitor(self):
        """创建性能监控面板"""
        # 创建性能监控面板
        self.performance_dock = QDockWidget("性能监控", self)
        self.performance_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea
        )
        self.performance_dock.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetClosable
        )
        
        self.performance_widget = PerformanceMonitorWidget()
        self.performance_dock.setWidget(self.performance_widget)
        
        # 创建API监控面板
        self.api_dock = QDockWidget("API监控", self)
        self.api_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea
        )
        self.api_dock.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetClosable
        )
        
        self.api_widget = APIMonitorWidget()
        self.api_dock.setWidget(self.api_widget)
        
        # 从配置中加载停靠位置
        performance_area = self.config_manager.get_config(
            "ui.dock.performance.area",
            Qt.RightDockWidgetArea
        )
        api_area = self.config_manager.get_config(
            "ui.dock.api.area",
            Qt.RightDockWidgetArea
        )
        
        # 添加到对应位置
        self.addDockWidget(performance_area, self.performance_dock)
        self.addDockWidget(api_area, self.api_dock)
        
        # 根据配置设置可见性
        self.performance_dock.setVisible(
            self.config_manager.get_config("ui.dock.performance.visible", True)
        )
        self.api_dock.setVisible(
            self.config_manager.get_config("ui.dock.api.visible", True)
        )
        
        # 连接信号
        self.performance_dock.visibilityChanged.connect(
            lambda visible: self.config_manager.set_config("ui.dock.performance.visible", visible)
        )
        self.api_dock.visibilityChanged.connect(
            lambda visible: self.config_manager.set_config("ui.dock.api.visible", visible)
        )
        
        # 连接停靠区域变化信号
        self.performance_dock.dockLocationChanged.connect(
            lambda area: self.config_manager.set_config("ui.dock.performance.area", area)
        )
        self.api_dock.dockLocationChanged.connect(
            lambda area: self.config_manager.set_config("ui.dock.api.area", area)
        )
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        select_folder_action = QAction("选择文件夹", self)
        select_folder_action.triggered.connect(self.select_folder)
        file_menu.addAction(select_folder_action)
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        # 性能监控菜单项
        toggle_performance_action = QAction("性能监控", self)
        toggle_performance_action.setCheckable(True)
        toggle_performance_action.setChecked(self.performance_dock.isVisible())
        toggle_performance_action.triggered.connect(self.performance_dock.setVisible)
        view_menu.addAction(toggle_performance_action)
        
        # API监控菜单项
        toggle_api_action = QAction("API监控", self)
        toggle_api_action.setCheckable(True)
        toggle_api_action.setChecked(self.api_dock.isVisible())
        toggle_api_action.triggered.connect(self.api_dock.setVisible)
        view_menu.addAction(toggle_api_action)
        
        # 重置布局菜单项
        reset_layout_action = QAction("重置布局", self)
        reset_layout_action.triggered.connect(self.reset_dock_layout)
        view_menu.addAction(reset_layout_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具")
        
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        cleanup_action = QAction("清理内存", self)
        cleanup_action.triggered.connect(self.performance_widget.cleanup_memory)
        tools_menu.addAction(cleanup_action)
        
    def load_config(self):
        """加载配置"""
        # 加载窗口大小
        width = self.config_manager.get_config("ui.window_size.width", 1200)
        height = self.config_manager.get_config("ui.window_size.height", 800)
        self.resize(width, height)
        
        # 加载文件类型过滤器
        extensions = self.config_manager.get_allowed_extensions()
        for ext in extensions:
            self.file_filter.add_allowed_extension(ext)
            
    @performance_logger
    def select_folder(self, event=None):
        """选择文件夹"""
        try:
            folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
            if folder:
                self.selected_directory = folder  # 更新选择的目录
                self.refresh_file_list()
                self.log_message(f"已选择文件夹: {folder}")
        except Exception as e:
            self.error_handler.handle_error(
                e, {"stage": "folder_selection", "folder": folder}
            )
            
    @performance_logger
    def refresh_file_list(self):
        """刷新文件列表"""
        self.file_model.clear()
        self.file_model.setHorizontalHeaderLabels(["文件名", "大小", "修改时间"])
        
        try:
            if not self.selected_directory:
                return
                
            files_info = self.file_system.collect_files_info(self.selected_directory)
            for file_info in files_info:
                if self.file_filter.is_allowed_file(file_info["absolute_path"]):
                    name_item = QStandardItem(file_info["name"])
                    size_item = QStandardItem(self.format_size(file_info["size"]))
                    time_item = QStandardItem(
                        file_info["modified_time"].strftime("%Y-%m-%d %H:%M:%S")
                    )
                    self.file_model.appendRow([name_item, size_item, time_item])
                    
        except Exception as e:
            self.error_handler.handle_error(
                e, {"stage": "refresh_file_list", "folder": self.selected_directory}
            )
            QMessageBox.warning(self, "错误", f"加载文件列表时发生错误：{str(e)}")
            
    def format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
        
    def filter_files(self):
        """过滤文件列表"""
        search_text = self.search_input.text().lower()
        for row in range(self.file_model.rowCount()):
            item = self.file_model.item(row, 0)
            if search_text in item.text().lower():
                self.file_list.setRowHidden(row, self.file_list.rootIndex(), False)
            else:
                self.file_list.setRowHidden(row, self.file_list.rootIndex(), True)
                
    @performance_logger
    def start_classification(self, event=None):
        """开始分类处理"""
        try:
            # 检查是否选择了目录
            if not self.selected_directory:
                QMessageBox.warning(self, "警告", "请先选择要分类的文件夹！")
                return
                
            # 检查是否设置了目标目录
            target_base_dir = self.config_manager.get_config("target_directory")
            if not target_base_dir:
                QMessageBox.warning(self, "警告", "请先在设置中配置目标目录！")
                return
                
            # 清空日志区域
            self.log_area.clear()
            self.log_message("开始文件分类处理...")
            
            # 收集文件信息
            self.log_message("正在收集文件信息...")
            files_info = self.file_system.collect_files_info(self.selected_directory)
            
            if not files_info:
                self.log_message("未发现任何文件！")
                return
                
            self.log_message(f"共发现 {len(files_info)} 个文件")
            
            # 过滤文件
            if self.file_filter.get_allowed_extensions():
                filtered_files = [
                    f for f in files_info 
                    if self.file_filter.is_allowed_file(f['name'])
                ]
                self.log_message(f"过滤后剩余 {len(filtered_files)} 个文件")
            else:
                filtered_files = files_info
                
            if not filtered_files:
                self.log_message("过滤后没有符合条件的文件！")
                return
                
            # 启动分类线程
            self.classification_thread = ClassificationThread(
                self.ai_classifier,
                filtered_files,
                target_base_dir,
                self.file_mover
            )
            self.classification_thread.finished.connect(self.handle_classification_complete)
            self.classification_thread.error.connect(self.handle_classification_error)
            self.classification_thread.progress.connect(self.update_progress)
            self.classification_thread.status_updated.connect(self.log_message)
            
            # 禁用按钮
            self.select_folder_btn.setEnabled(False)
            self.start_btn.setEnabled(False)
            
            # 显示进度条
            self.progress_bar.setMaximum(len(filtered_files))
            self.progress_bar.setValue(0)
            self.progress_bar.show()
            
            # 启动线程
            self.classification_thread.start()
            
        except Exception as e:
            self.log_message(f"错误：{str(e)}")
            QMessageBox.critical(self, "错误", f"开始分类时出错：{str(e)}")
            
    def handle_classification_complete(self, results):
        """处理分类完成"""
        try:
            self.log_message("分类处理完成！")
            
            # 更新结果表格
            self.category_table.setRowCount(0)
            for file_path, result in results.items():
                row = self.category_table.rowCount()
                self.category_table.insertRow(row)
                
                # 文件名
                self.category_table.setItem(row, 0, QTableWidgetItem(os.path.basename(file_path)))
                
                # 目标文件夹
                self.category_table.setItem(row, 1, QTableWidgetItem(result['target_folder']))
                
                # 置信度
                confidence_item = QTableWidgetItem(f"{result['confidence']*100:.1f}%")
                self.category_table.setItem(row, 2, confidence_item)
                
                # 分类理由
                reason_item = QTableWidgetItem(result['reason'])
                self.category_table.setItem(row, 3, reason_item)
                
            # 恢复按钮状态
            self.select_folder_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            
            # 隐藏进度条
            self.progress_bar.hide()
            
            # 显示统计信息
            self.log_message(f"共处理 {self.category_table.rowCount()} 个文件")
            
            # 开始移动文件
            self.move_files_to_categories(results)
            
        except Exception as e:
            self.log_message(f"显示结果时出错：{str(e)}")
            QMessageBox.critical(self, "错误", f"显示结果时出错：{str(e)}")
            
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
        
    def log_message(self, message):
        """记录日志消息"""
        current_time = QDateTime.currentDateTime().toString("HH:mm:ss")
        self.log_area.append(f"[{current_time}] {message}")
        # 滚动到底部
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )
        # 同时输出到控制台
        print(f"[{current_time}] {message}")
        
    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.config_manager, self)
        dialog.exec_()
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            # 保存窗口状态
            self.config_manager.set_config("ui.window_size.width", self.width())
            self.config_manager.set_config("ui.window_size.height", self.height())
            self.config_manager.set_config("ui.window_state", self.saveState().toHex().data().decode())
            
            # 保存停靠窗口状态
            self.config_manager.set_config("ui.dock.performance.area", self.dockWidgetArea(self.performance_dock))
            self.config_manager.set_config("ui.dock.api.area", self.dockWidgetArea(self.api_dock))
            self.config_manager.set_config("ui.dock.performance.visible", self.performance_dock.isVisible())
            self.config_manager.set_config("ui.dock.api.visible", self.api_dock.isVisible())
            
            # 保存所有配置
            self.config_manager.save_config()
            
        except Exception as e:
            self.error_handler.handle_error(e, {"stage": "window_close"})
            
        super().closeEvent(event)
        
    def show_ai_response_detail(self, item):
        """显示AI响应详细信息"""
        if item.column() == 3:  # AI响应列
            detail_dialog = QDialog(self)
            detail_dialog.setWindowTitle("AI响应详细信息")
            detail_dialog.setMinimumSize(600, 400)
            
            layout = QVBoxLayout(detail_dialog)
            
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlainText(item.text())
            layout.addWidget(text_edit)
            
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(detail_dialog.close)
            layout.addWidget(close_btn)
            
            detail_dialog.exec_() 

    def handle_classification_error(self, error_msg: str):
        """处理分类错误"""
        self.log_message(f"分类过程出错: {error_msg}")
        self.progress_bar.hide()
        self.select_folder_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
        QMessageBox.critical(self, "错误", f"分类过程中发生错误：{error_msg}")

    def handle_classification_results(self, results: Dict[str, Dict]):
        """处理分类结果"""
        try:
            self.log_message("分类处理完成！")
            
            # 更新结果表格
            self.category_table.setRowCount(0)
            for file_path, result in results.items():
                row = self.category_table.rowCount()
                self.category_table.insertRow(row)
                
                # 文件名
                self.category_table.setItem(row, 0, QTableWidgetItem(os.path.basename(file_path)))
                
                # 目标文件夹
                self.category_table.setItem(row, 1, QTableWidgetItem(result['target_folder']))
                
                # 置信度
                confidence_item = QTableWidgetItem(f"{result['confidence']*100:.1f}%")
                self.category_table.setItem(row, 2, confidence_item)
                
                # 分类理由
                reason_item = QTableWidgetItem(result['reason'])
                self.category_table.setItem(row, 3, reason_item)
                
            # 恢复按钮状态
            self.select_folder_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            
            # 隐藏进度条
            self.progress_bar.hide()
            
            # 显示统计信息
            self.log_message(f"共处理 {self.category_table.rowCount()} 个文件")
            
            # 开始移动文件
            self.move_files_to_categories(results)
            
        except Exception as e:
            self.log_message(f"显示结果时出错：{str(e)}")
            QMessageBox.critical(self, "错误", f"显示结果时出错：{str(e)}")

    def move_files_to_categories(self, results: Dict[str, Dict]):
        """将文件移动到对应的分类目录"""
        try:
            self.log_message("开始移动文件到对应目录...")
            target_base_dir = self.config_manager.get_config("target_directory")
            
            for file_path, result in results.items():
                target_folder = result['target_folder']
                target_dir = os.path.join(target_base_dir, target_folder)
                
                # 确保目标目录存在
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                    
                # 移动文件
                try:
                    self.file_mover.move_file(file_path, target_dir)
                    self.log_message(f"已移动: {os.path.basename(file_path)} -> {target_folder}")
                except Exception as e:
                    self.log_message(f"移动文件失败: {os.path.basename(file_path)} - {str(e)}")
                    
            self.log_message("文件移动完成")
            QMessageBox.information(self, "完成", "文件分类和移动完成")
            
        except Exception as e:
            self.log_message(f"移动文件时出错: {str(e)}")
            QMessageBox.critical(self, "错误", f"移动文件时出错：{str(e)}")

    def reset_dock_layout(self):
        """重置停靠窗口布局"""
        # 重置到默认位置
        self.addDockWidget(Qt.RightDockWidgetArea, self.performance_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.api_dock)
        
        # 显示所有面板
        self.performance_dock.setVisible(True)
        self.api_dock.setVisible(True)
        
        # 更新配置
        self.config_manager.set_config("ui.dock.performance.area", Qt.RightDockWidgetArea)
        self.config_manager.set_config("ui.dock.api.area", Qt.RightDockWidgetArea)
        self.config_manager.set_config("ui.dock.performance.visible", True)
        self.config_manager.set_config("ui.dock.api.visible", True) 