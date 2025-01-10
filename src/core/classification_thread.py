"""
分类线程模块
提供异步文件分类功能
"""
from PyQt5.QtCore import QThread, pyqtSignal
import logging
import os
from typing import List

class ClassificationThread(QThread):
    """分类处理线程"""
    
    finished = pyqtSignal(dict)  # 完成信号，传递分类结果
    error = pyqtSignal(str)      # 错误信号
    progress = pyqtSignal(int)   # 进度信号
    status_updated = pyqtSignal(str)  # 状态更新信号
    
    def __init__(self, ai_classifier, files_info, target_base_dir, file_mover):
        super().__init__()
        self.ai_classifier = ai_classifier
        self.files_info = files_info
        self.target_base_dir = target_base_dir
        self.file_mover = file_mover
        self.logger = logging.getLogger(__name__)
        
    def get_existing_categories(self) -> List[str]:
        """获取目标目录下已存在的分类目录"""
        try:
            self.logger.debug(f"开始获取目标目录的已有分类: {self.target_base_dir}")
            
            if not os.path.exists(self.target_base_dir):
                self.logger.debug(f"目标目录不存在，将自动创建: {self.target_base_dir}")
                os.makedirs(self.target_base_dir)
                return []
                
            # 获取所有子目录
            categories = []
            for item in os.listdir(self.target_base_dir):
                item_path = os.path.join(self.target_base_dir, item)
                if os.path.isdir(item_path):
                    categories.append(item)
                    self.logger.debug(f"发现分类目录: {item}")
                    
            self.logger.debug(f"目标目录扫描完成，共发现 {len(categories)} 个分类目录")
            return categories
            
        except Exception as e:
            self.logger.error(f"获取已有分类目录时出错: {str(e)}")
            return []
    
    def run(self):
        """运行分类处理"""
        try:
            self.logger.debug("=== 开始文件分类任务 ===")
            self.status_updated.emit("开始进行AI分类...")
            
            # 获取已有分类
            self.logger.debug("正在扫描目标目录...")
            self.status_updated.emit("正在获取已有分类信息...")
            existing_categories = self.get_existing_categories()
            
            if existing_categories:
                msg = f"发现 {len(existing_categories)} 个已有分类目录: {existing_categories}"
                self.logger.debug(msg)
                self.status_updated.emit(msg)
            else:
                self.logger.debug("未发现已有分类目录，将创建新的分类")
                self.status_updated.emit("未发现已有分类目录")
            
            # 调用AI进行分类
            self.logger.debug("开始调用AI进行文件分类...")
            self.status_updated.emit("正在进行AI分类分析...")
            classification_results = self.ai_classifier.classify_files(
                self.files_info,
                existing_categories
            )
            self.logger.debug(f"AI分类完成，获得 {len(classification_results)} 个分类结果")
            
            # 处理每个文件
            self.logger.debug("开始处理分类结果...")
            self.status_updated.emit("开始移动文件到对应目录...")
            processed_count = 0
            success_count = 0
            error_count = 0
            
            for file_info in self.files_info:
                try:
                    file_path = file_info['absolute_path']
                    if file_path not in classification_results:
                        self.logger.warning(f"文件 {file_path} 没有分类结果，跳过处理")
                        continue
                        
                    result = classification_results[file_path]
                    target_folder = result['target_folder']
                    
                    # 创建目标文件夹
                    target_dir = os.path.join(self.target_base_dir, target_folder)
                    self.logger.debug(f"准备创建目标文件夹: {target_dir}")
                    self.status_updated.emit(f"创建目标文件夹: {target_dir}")
                    
                    # 移动文件
                    self.logger.debug(f"开始移动文件: {file_path} -> {target_dir}")
                    self.status_updated.emit(f"移动文件: {os.path.basename(file_path)} -> {target_folder}")
                    success = self.file_mover.move_file(file_path, target_dir)
                    
                    if success:
                        self.logger.debug(f"文件移动成功: {file_path}")
                        success_count += 1
                    else:
                        self.logger.error(f"文件移动失败: {file_path}")
                        error_count += 1
                        result['error'] = "文件移动失败"
                        
                    processed_count += 1
                    self.progress.emit(processed_count)
                    
                except Exception as e:
                    self.logger.error(f"处理文件 {file_path} 时出错: {str(e)}")
                    error_count += 1
                    classification_results[file_path] = {
                        'target_folder': '错误',
                        'reason': f'处理出错: {str(e)}',
                        'confidence': 0.0
                    }
                    
            # 输出处理统计
            summary = (
                f"处理完成，共处理 {processed_count} 个文件:\n"
                f"- 成功: {success_count} 个\n"
                f"- 失败: {error_count} 个"
            )
            self.logger.debug(summary)
            self.status_updated.emit(summary)
            
            self.finished.emit(classification_results)
            self.logger.debug("=== 文件分类任务结束 ===")
            
        except Exception as e:
            error_msg = f"分类线程执行出错: {str(e)}"
            self.logger.error(error_msg)
            self.error.emit(error_msg) 