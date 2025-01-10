"""
性能优化模块
提供并行处理和内存管理功能
"""
import os
import gc
import psutil
import logging
import threading
from typing import List, Callable, Any, Dict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps
from time import time

class PerformanceMonitor:
    """性能监控类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.process = psutil.Process()
        
    def get_memory_usage(self) -> Dict[str, float]:
        """
        获取内存使用情况
        
        Returns:
            Dict[str, float]: 内存使用信息（单位：MB）
        """
        try:
            memory_info = self.process.memory_info()
            result = {
                "rss": memory_info.rss / 1024 / 1024,  # 物理内存
                "vms": memory_info.vms / 1024 / 1024,  # 虚拟内存
                "percent": self.process.memory_percent()  # 内存使用百分比
            }
            
            # 某些系统可能不支持shared属性
            try:
                result["shared"] = memory_info.shared / 1024 / 1024  # 共享内存
            except AttributeError:
                result["shared"] = 0  # 如果不支持，返回0
                
            return result
            
        except Exception as e:
            self.logger.error(f"获取内存使用情况失败: {str(e)}")
            return {
                "rss": 0,
                "vms": 0,
                "shared": 0,
                "percent": 0
            }
        
    def get_cpu_usage(self) -> float:
        """
        获取CPU使用率
        
        Returns:
            float: CPU使用百分比
        """
        return self.process.cpu_percent()
        
    def log_performance(self):
        """记录性能信息"""
        try:
            memory = self.get_memory_usage()
            cpu = self.get_cpu_usage()
            
            self.logger.info(
                f"性能监控 - CPU使用率: {cpu}%, "
                f"物理内存: {memory['rss']:.1f}MB, "
                f"内存使用率: {memory['percent']:.1f}%"
            )
        except Exception as e:
            self.logger.error(f"性能监控失败: {str(e)}")

def performance_logger(func):
    """性能日志装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            # 调用原始函数
            result = func(*args, **kwargs)
            
            # 计算执行时间和内存使用
            end_time = time()
            end_memory = psutil.Process().memory_info().rss
            
            execution_time = end_time - start_time
            memory_diff = (end_memory - start_memory) / 1024 / 1024  # MB
            
            # 记录性能日志
            logging.info(
                f"函数 {func.__name__} 执行完成 - "
                f"耗时: {execution_time:.2f}秒, "
                f"内存变化: {memory_diff:+.1f}MB"
            )
            
            return result
            
        except Exception as e:
            logging.error(f"函数 {func.__name__} 执行失败: {str(e)}")
            raise
            
    return wrapper

class ParallelProcessor:
    """并行处理器"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or os.cpu_count()
        self.logger = logging.getLogger(__name__)
        
    def process_in_threads(self, items: List[Any], worker_func: Callable, *args, **kwargs) -> List[Any]:
        """
        使用线程池处理任务
        
        Args:
            items: 待处理的项目列表
            worker_func: 工作函数
            *args, **kwargs: 传递给工作函数的参数
            
        Returns:
            List[Any]: 处理结果列表
        """
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for item in items:
                future = executor.submit(worker_func, item, *args, **kwargs)
                futures.append(future)
                
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"线程执行失败: {str(e)}")
                    
        return results
        
    def process_in_processes(self, items: List[Any], worker_func: Callable, *args, **kwargs) -> List[Any]:
        """
        使用进程池处理任务
        
        Args:
            items: 待处理的项目列表
            worker_func: 工作函数
            *args, **kwargs: 传递给工作函数的参数
            
        Returns:
            List[Any]: 处理结果列表
        """
        results = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for item in items:
                future = executor.submit(worker_func, item, *args, **kwargs)
                futures.append(future)
                
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"进程执行失败: {str(e)}")
                    
        return results

class MemoryManager:
    """内存管理器"""
    
    def __init__(self, threshold_mb: float = 1024):  # 1GB
        self.threshold_mb = threshold_mb
        self.logger = logging.getLogger(__name__)
        
    def check_memory(self) -> bool:
        """
        检查内存使用情况
        
        Returns:
            bool: 是否超过阈值
        """
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        return memory_mb > self.threshold_mb
        
    def cleanup(self):
        """清理内存"""
        try:
            # 手动触发垃圾回收
            gc.collect()
            
            # 记录清理效果
            before = psutil.Process().memory_info().rss / 1024 / 1024
            gc.collect()
            after = psutil.Process().memory_info().rss / 1024 / 1024
            
            self.logger.info(f"内存清理完成 - 释放: {before - after:.1f}MB")
            
        except Exception as e:
            self.logger.error(f"内存清理失败: {str(e)}")
            
    def monitor_and_cleanup(self):
        """监控并清理内存"""
        if self.check_memory():
            self.logger.warning(f"内存使用超过阈值 ({self.threshold_mb}MB)，开始清理")
            self.cleanup()
            
class BatchProcessor:
    """批处理器"""
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        self.logger = logging.getLogger(__name__)
        
    def process_in_batches(self, items: List[Any], processor_func: Callable, *args, **kwargs) -> List[Any]:
        """
        批量处理数据
        
        Args:
            items: 待处理的项目列表
            processor_func: 处理函数
            *args, **kwargs: 传递给处理函数的参数
            
        Returns:
            List[Any]: 处理结果列表
        """
        results = []
        total_items = len(items)
        
        for i in range(0, total_items, self.batch_size):
            batch = items[i:i + self.batch_size]
            try:
                batch_results = processor_func(batch, *args, **kwargs)
                results.extend(batch_results)
                
                progress = min(100, int((i + len(batch)) / total_items * 100))
                self.logger.info(f"批处理进度: {progress}%")
                
            except Exception as e:
                self.logger.error(f"批处理失败: {str(e)}")
                
        return results 