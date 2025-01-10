"""
异常处理模块
提供全局异常处理和错误恢复功能
"""
import sys
import logging
import traceback
import time
from typing import Optional, Callable, Any, Dict
from functools import wraps
from datetime import datetime

class ErrorHandler:
    """错误处理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_callbacks: Dict[str, Callable] = {}
        
    def register_error_callback(self, error_type: str, callback: Callable):
        """
        注册错误回调函数
        
        Args:
            error_type: 错误类型
            callback: 回调函数
        """
        self.error_callbacks[error_type] = callback
        
    def handle_error(self, error: Exception, context: Optional[Dict] = None):
        """
        处理错误
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        error_type = error.__class__.__name__
        
        # 记录错误信息
        self.logger.error(
            f"错误类型: {error_type}\n"
            f"错误信息: {str(error)}\n"
            f"错误上下文: {context or {}}\n"
            f"堆栈跟踪:\n{traceback.format_exc()}"
        )
        
        # 调用对应的错误处理回调
        if error_type in self.error_callbacks:
            try:
                self.error_callbacks[error_type](error, context)
            except Exception as callback_error:
                self.logger.error(f"错误处理回调执行失败: {str(callback_error)}")
                
class ErrorRecovery:
    """错误恢复器"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)
        
    def retry_on_error(self, func: Callable) -> Callable:
        """
        错误重试装饰器
        
        Args:
            func: 需要重试的函数
            
        Returns:
            Callable: 包装后的函数
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(self.max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    self.logger.warning(
                        f"函数 {func.__name__} 执行失败 "
                        f"(尝试 {attempt + 1}/{self.max_retries}): {str(e)}"
                    )
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        
            raise last_error
            
        return wrapper
        
class ErrorTracker:
    """错误跟踪器"""
    
    def __init__(self, log_file: str = "error_tracking.log"):
        self.log_file = log_file
        self.logger = logging.getLogger(__name__)
        
    def track_error(self, error: Exception, context: Optional[Dict] = None):
        """
        跟踪错误
        
        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_type = error.__class__.__name__
        
        error_info = (
            f"[{timestamp}] {error_type}: {str(error)}\n"
            f"上下文: {context or {}}\n"
            f"堆栈跟踪:\n{traceback.format_exc()}\n"
            f"{'-' * 80}\n"
        )
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(error_info)
        except Exception as e:
            self.logger.error(f"写入错误跟踪日志失败: {str(e)}")
            
class ErrorAnalyzer:
    """错误分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_stats: Dict[str, int] = {}
        
    def analyze_error(self, error: Exception) -> Dict[str, Any]:
        """
        分析错误
        
        Args:
            error: 异常对象
            
        Returns:
            Dict[str, Any]: 错误分析结果
        """
        error_type = error.__class__.__name__
        
        # 更新错误统计
        self.error_stats[error_type] = self.error_stats.get(error_type, 0) + 1
        
        # 分析错误
        analysis = {
            "error_type": error_type,
            "error_message": str(error),
            "occurrence_count": self.error_stats[error_type],
            "stack_trace": traceback.extract_tb(sys.exc_info()[2]),
            "severity": self._determine_severity(error),
            "suggested_action": self._suggest_action(error)
        }
        
        self.logger.info(f"错误分析完成: {analysis}")
        return analysis
        
    def _determine_severity(self, error: Exception) -> str:
        """
        确定错误严重程度
        
        Args:
            error: 异常对象
            
        Returns:
            str: 严重程度（低、中、高）
        """
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            return "高"
        elif isinstance(error, (ValueError, TypeError)):
            return "中"
        else:
            return "低"
            
    def _suggest_action(self, error: Exception) -> str:
        """
        建议处理方法
        
        Args:
            error: 异常对象
            
        Returns:
            str: 建议的处理方法
        """
        if isinstance(error, (FileNotFoundError, PermissionError)):
            return "检查文件权限和路径"
        elif isinstance(error, (ValueError, TypeError)):
            return "检查输入参数类型和值"
        elif isinstance(error, MemoryError):
            return "检查内存使用情况并清理"
        else:
            return "查看详细错误日志进行分析"
            
def global_exception_handler(exctype, value, tb):
    """
    全局异常处理函数
    
    Args:
        exctype: 异常类型
        value: 异常值
        tb: 堆栈跟踪对象
    """
    logger = logging.getLogger(__name__)
    
    # 记录未捕获的异常
    logger.critical(
        f"未捕获的异常:\n"
        f"类型: {exctype.__name__}\n"
        f"信息: {str(value)}\n"
        f"堆栈:\n{''.join(traceback.format_tb(tb))}"
    )
    
    # 对于特定类型的错误进行特殊处理
    if issubclass(exctype, KeyboardInterrupt):
        logger.info("程序被用户中断")
        sys.__excepthook__(exctype, value, tb)
        return
        
    if issubclass(exctype, MemoryError):
        logger.critical("内存不足，尝试进行垃圾回收")
        import gc
        gc.collect()
        
    if issubclass(exctype, SystemExit):
        logger.info("程序正常退出")
        sys.__excepthook__(exctype, value, tb)
        return
        
# 设置全局异常处理器
sys.excepthook = global_exception_handler 