"""
文件系统处理模块
提供文件系统操作功能
"""
import os
import logging
from datetime import datetime
from typing import List, Dict

class FileSystemHandler:
    """文件系统处理类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("文件系统处理器初始化完成")
        
    def collect_files_info(self, directory: str) -> List[Dict]:
        """收集目录中的文件信息"""
        try:
            self.logger.debug(f"开始收集目录信息: {directory}")
            files_info = []
            
            # 检查目录是否存在
            if not os.path.exists(directory):
                self.logger.error(f"目录不存在: {directory}")
                raise FileNotFoundError(f"目录不存在: {directory}")
                
            # 遍历目录
            for root, _, files in os.walk(directory):
                self.logger.debug(f"扫描目录: {root}")
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        self.logger.debug(f"处理文件: {file_path}")
                        
                        # 获取文件信息
                        stat = os.stat(file_path)
                        file_info = {
                            "name": file,
                            "absolute_path": file_path,
                            "relative_path": os.path.relpath(file_path, directory),
                            "size": stat.st_size,
                            "modified_time": datetime.fromtimestamp(stat.st_mtime),
                            "created_time": datetime.fromtimestamp(stat.st_ctime)
                        }
                        
                        self.logger.debug(
                            f"文件信息: 大小={self._format_size(stat.st_size)}, "
                            f"修改时间={file_info['modified_time']}"
                        )
                        
                        files_info.append(file_info)
                        
                    except Exception as e:
                        self.logger.error(f"处理文件 {file} 时出错: {str(e)}")
                        continue
                        
            self.logger.debug(f"文件信息收集完成，共 {len(files_info)} 个文件")
            return files_info
            
        except Exception as e:
            self.logger.error(f"收集文件信息时出错: {str(e)}")
            raise
            
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
        
    def create_directory(self, path: str) -> bool:
        """创建目录"""
        try:
            self.logger.debug(f"尝试创建目录: {path}")
            if not os.path.exists(path):
                os.makedirs(path)
                self.logger.info(f"目录创建成功: {path}")
            else:
                self.logger.debug(f"目录已存在: {path}")
            return True
            
        except Exception as e:
            self.logger.error(f"创建目录失败: {str(e)}")
            return False
            
    def delete_empty_directories(self, directory: str) -> int:
        """删除空目录"""
        try:
            self.logger.debug(f"开始清理空目录: {directory}")
            count = 0
            
            for root, dirs, _ in os.walk(directory, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                            count += 1
                            self.logger.debug(f"删除空目录: {dir_path}")
                    except Exception as e:
                        self.logger.error(f"删除目录 {dir_path} 时出错: {str(e)}")
                        continue
                        
            self.logger.info(f"清理完成，共删除 {count} 个空目录")
            return count
            
        except Exception as e:
            self.logger.error(f"清理空目录时出错: {str(e)}")
            return 0 