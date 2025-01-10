"""
应用程序入口模块
"""
import sys
import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from src.ui.main_window import MainWindow
from src.config.config_manager import ConfigManager
from src.utils.performance import (
    PerformanceMonitor, MemoryManager,
    performance_logger
)
from src.utils.error_handler import (
    ErrorHandler, ErrorTracker, ErrorAnalyzer,
    global_exception_handler
)

def setup_logging():
    """配置日志系统"""
    # 创建logs目录（如果不存在）
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # 生成日志文件名（使用当前时间）
    log_filename = os.path.join(
        'logs', 
        f'debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    )
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # 文件处理器
            logging.FileHandler(log_filename, encoding='utf-8'),
            # 控制台处理器
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.info("日志系统初始化完成")
    logging.debug(f"日志文件: {log_filename}")

class Application:
    """应用程序类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 初始化性能监控
        self.performance_monitor = PerformanceMonitor()
        self.memory_manager = MemoryManager(threshold_mb=512)  # 设置内存阈值为512MB
        
        # 初始化错误处理
        self.error_handler = ErrorHandler()
        self.error_tracker = ErrorTracker()
        self.error_analyzer = ErrorAnalyzer()
        
        # 注册错误处理回调
        self.register_error_callbacks()
        
    def register_error_callbacks(self):
        """注册错误处理回调函数"""
        # 注册内存错误处理
        def handle_memory_error(error, context):
            self.logger.error("检测到内存错误，开始清理...")
            self.memory_manager.cleanup()
            
        self.error_handler.register_error_callback("MemoryError", handle_memory_error)
        
        # 注册文件操作错误处理
        def handle_file_error(error, context):
            self.logger.error(f"文件操作失败: {context.get('file_path', 'unknown')}")
            self.error_tracker.track_error(error, context)
            
        self.error_handler.register_error_callback("FileNotFoundError", handle_file_error)
        self.error_handler.register_error_callback("PermissionError", handle_file_error)
        
    @performance_logger
    def initialize(self):
        """初始化应用程序"""
        try:
            # 创建应用实例
            self.app = QApplication(sys.argv)
            
            # 加载配置
            self.config_manager = ConfigManager()
            
            # 设置界面风格
            self.setup_style()
            
            # 创建主窗口
            self.window = MainWindow()
            
            # 设置性能监控定时器
            self.setup_monitoring()
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e, {"stage": "initialization"})
            return False
            
    def setup_style(self):
        """设置界面风格"""
        theme = self.config_manager.get_config("ui.theme", "light")
        if theme == "dark":
            self.app.setStyle("Fusion")
            palette = self.app.palette()
            palette.setColor(palette.Window, Qt.black)
            palette.setColor(palette.WindowText, Qt.white)
            palette.setColor(palette.Base, Qt.darkGray)
            palette.setColor(palette.AlternateBase, Qt.black)
            palette.setColor(palette.ToolTipBase, Qt.white)
            palette.setColor(palette.ToolTipText, Qt.white)
            palette.setColor(palette.Text, Qt.white)
            palette.setColor(palette.Button, Qt.darkGray)
            palette.setColor(palette.ButtonText, Qt.white)
            palette.setColor(palette.BrightText, Qt.red)
            palette.setColor(palette.Link, Qt.blue)
            palette.setColor(palette.Highlight, Qt.blue)
            palette.setColor(palette.HighlightedText, Qt.black)
            self.app.setPalette(palette)
            
    def setup_monitoring(self):
        """设置性能监控"""
        # 每30秒记录一次性能信息
        def log_performance():
            self.performance_monitor.log_performance()
            self.memory_manager.monitor_and_cleanup()
            
        timer = self.app.startTimer(30000)  # 30秒
        self.app.timerEvent = lambda event: log_performance()
        
    @performance_logger
    def run(self):
        """运行应用程序"""
        try:
            # 显示主窗口
            self.window.show()
            
            # 运行应用
            return self.app.exec_()
            
        except Exception as e:
            self.error_handler.handle_error(e, {"stage": "runtime"})
            return 1
            
def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 创建应用实例
        application = Application()
        
        # 初始化应用
        if not application.initialize():
            logger.error("应用程序初始化失败")
            return 1
            
        # 运行应用
        return application.run()
        
    except Exception as e:
        logger.critical(f"应用程序启动失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 