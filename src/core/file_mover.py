"""
文件移动器模块
提供文件移动和复制功能
"""
import os
import shutil
import logging
from typing import Optional

class FileMover:
    """文件移动器类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("文件移动器初始化完成")
        
    def move_file(self, source: str, target_dir: str, new_name: Optional[str] = None) -> bool:
        """移动文件到目标目录"""
        try:
            self.logger.debug(f"准备移动文件: {source} -> {target_dir}")
            
            # 确保目标目录存在
            if not os.path.exists(target_dir):
                self.logger.debug(f"创建目标目录: {target_dir}")
                os.makedirs(target_dir)
                
            # 确定目标文件名
            if new_name:
                target_name = new_name
                self.logger.debug(f"使用新文件名: {new_name}")
            else:
                target_name = os.path.basename(source)
                self.logger.debug(f"使用原文件名: {target_name}")
                
            target_path = os.path.join(target_dir, target_name)
            
            # 检查目标文件是否已存在
            if os.path.exists(target_path):
                self.logger.debug(f"目标文件已存在: {target_path}")
                base, ext = os.path.splitext(target_name)
                counter = 1
                while os.path.exists(target_path):
                    new_name = f"{base}_{counter}{ext}"
                    target_path = os.path.join(target_dir, new_name)
                    counter += 1
                self.logger.debug(f"生成新的文件名: {new_name}")
                
            # 移动文件
            self.logger.debug(f"开始移动文件到: {target_path}")
            shutil.move(source, target_path)
            self.logger.info(f"文件移动成功: {source} -> {target_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"移动文件失败: {str(e)}")
            return False
            
    def copy_file(self, source: str, target_dir: str, new_name: Optional[str] = None) -> bool:
        """复制文件到目标目录"""
        try:
            self.logger.debug(f"准备复制文件: {source} -> {target_dir}")
            
            # 确保目标目录存在
            if not os.path.exists(target_dir):
                self.logger.debug(f"创建目标目录: {target_dir}")
                os.makedirs(target_dir)
                
            # 确定目标文件名
            if new_name:
                target_name = new_name
                self.logger.debug(f"使用新文件名: {new_name}")
            else:
                target_name = os.path.basename(source)
                self.logger.debug(f"使用原文件名: {target_name}")
                
            target_path = os.path.join(target_dir, target_name)
            
            # 检查目标文件是否已存在
            if os.path.exists(target_path):
                self.logger.debug(f"目标文件已存在: {target_path}")
                base, ext = os.path.splitext(target_name)
                counter = 1
                while os.path.exists(target_path):
                    new_name = f"{base}_{counter}{ext}"
                    target_path = os.path.join(target_dir, new_name)
                    counter += 1
                self.logger.debug(f"生成新的文件名: {new_name}")
                
            # 复制文件
            self.logger.debug(f"开始复制文件到: {target_path}")
            shutil.copy2(source, target_path)
            self.logger.info(f"文件复制成功: {source} -> {target_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"复制文件失败: {str(e)}")
            return False 