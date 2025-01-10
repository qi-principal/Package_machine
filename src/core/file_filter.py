"""
文件过滤器模块
提供文件类型过滤功能
"""
import os
import logging

class FileFilter:
    """文件过滤器类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.allowed_extensions = set()
        self.logger.debug("文件过滤器初始化完成")
        
    def add_allowed_extension(self, extension: str):
        """添加允许的文件扩展名"""
        if not extension.startswith('.'):
            extension = '.' + extension
        self.allowed_extensions.add(extension.lower())
        self.logger.debug(f"添加允许的扩展名: {extension}")
        
    def remove_allowed_extension(self, extension: str):
        """移除允许的文件扩展名"""
        if not extension.startswith('.'):
            extension = '.' + extension
        if extension.lower() in self.allowed_extensions:
            self.allowed_extensions.remove(extension.lower())
            self.logger.debug(f"移除扩展名: {extension}")
        
    def is_allowed_file(self, file_path: str) -> bool:
        """检查文件是否允许"""
        if not self.allowed_extensions:
            self.logger.debug(f"允许所有文件类型，通过: {file_path}")
            return True
            
        extension = os.path.splitext(file_path)[1].lower()
        is_allowed = extension in self.allowed_extensions
        
        self.logger.debug(
            f"检查文件 {file_path} - 扩展名: {extension} - "
            f"{'允许' if is_allowed else '不允许'}"
        )
        
        return is_allowed
        
    def get_allowed_extensions(self) -> list:
        """获取允许的扩展名列表"""
        extensions = list(self.allowed_extensions)
        self.logger.debug(f"当前允许的扩展名: {extensions}")
        return extensions 