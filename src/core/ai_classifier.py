"""
AI分类器模块
提供基于DeepSeek的文件分类功能
"""
import os
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from src.utils.api_monitor import APIMonitor
from src.config.config_manager import ConfigManager
import re
import json

class AIClassifier:
    """AI分类器类"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.client = None
        self.logger = logging.getLogger(__name__)
        
    def _init_client(self):
        """初始化 DeepSeek API 客户端"""
        api_key = self._get_api_key()
        base_url = self.config_manager.get_config("deepseek.base_url", "https://api.deepseek.com/v1")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        
    def _create_batch_classification_prompt(self, files_info: List[Dict], existing_categories: List[str]) -> str:
        """创建批量文件分类提示"""
        self.logger.debug(f"开始创建分类提示，文件数量：{len(files_info)}，已有分类数量：{len(existing_categories)}")
        
        files_description = []
        for file in files_info:
            file_desc = [f"文件名: {file['name']}"]
            
            # 添加文件内容预览（如果有）
            if 'content_preview' in file:
                preview = file['content_preview']
                if preview:
                    file_desc.append(f"文件内容预览: {preview[:200]}...")
            
            # 添加基本信息
            file_desc.extend([
                f"大小: {self._format_size(file['size'])}",
                f"修改时间: {file['modified_time']}"
            ])
            
            files_description.append("\n".join(file_desc))
            self.logger.debug(f"添加文件描述: {file['name']}")
            
        # 添加已有分类信息
        if existing_categories:
            self.logger.debug(f"已有分类目录: {existing_categories}")
            existing_categories_str = "\n".join([f"- {cat}" for cat in existing_categories])
        else:
            self.logger.debug("没有已有分类目录")
            existing_categories_str = "暂无已有分类"
        
        prompt = (
            "请帮我将以下文件分类到合适的文件夹中。\n"
            "分类要求：\n"
            "1. 主要根据文件的实际内容和用途进行分类，而不是文件格式\n"
            "2. 相同格式的文件可能属于不同类别，需要深入分析文件名和内容含义\n"
            "3. 分类粒度要适中，既不要过于笼统也不要过于细致\n"
            "4. 文件夹名称使用有意义的中文词组\n"
            "5. 必须详细说明分类理由，重点解释基于内容的判断依据\n"
            "6. 优先复用已有的分类目录，但如果现有类别不合适，可以创建新的\n"
            "7. 对于内容相近的文件，应该分类到同一目录下\n\n"
            "返回格式要求：\n"
            "{\n"
            '    "example.docx": {\n'
            '        "target_folder": "产品文档",\n'
            '        "reason": "根据文件名和内容分析，这是一份产品相关的技术文档"\n'
            "    }\n"
            "}\n\n"
            f"已有的分类目录：\n{existing_categories_str}\n\n"
            "待分类文件：\n" + "\n---\n".join(files_description)
        )
        
        self.logger.debug(f"分类提示创建完成，提示内容:\n{prompt}")
        return prompt
        
    def classify_files(self, files_info: List[Dict], existing_categories: List[str]) -> Dict[str, Dict]:
        """批量分类文件"""
        try:
            self.logger.debug(f"开始批量分类文件，共 {len(files_info)} 个文件")
            self.logger.debug(f"已有分类目录: {existing_categories}")
            
            # 创建文件名到路径的映射
            filename_to_path = {
                file_info['name']: file_info['absolute_path']
                for file_info in files_info
            }
            
            # 初始化客户端
            self.logger.debug("正在初始化 DeepSeek 客户端...")
            self._init_client()
            self.logger.debug("DeepSeek 客户端初始化完成")
            
            # 创建分类提示
            self.logger.debug("开始生成分类提示...")
            prompt = self._create_batch_classification_prompt(files_info, existing_categories)
            self.logger.debug(f"分类提示生成完成，提示内容:\n{prompt}")
            
            # 调用 AI 接口
            self.logger.debug("开始调用 DeepSeek API...")
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": (
                        "你是一个专业的文件分类助手。请按照以下格式返回分类结果：\n"
                        "{\n"
                        '    "文件名.扩展名": {\n'
                        '        "target_folder": "目标文件夹名称",\n'
                        '        "reason": "分类理由"\n'
                        "    }\n"
                        "}\n"
                        "注意：\n"
                        "1. 返回格式必须是合法的JSON\n"
                        "2. 所有文本必须使用双引号\n"
                        "3. 优先使用已有的分类目录\n"
                        "4. 给出合理的分类理由\n"
                        "5. 使用文件名（不是完整路径）作为键"
                    )},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            self.logger.debug("DeepSeek API 调用完成")
            
            # 解析响应
            try:
                result_text = response.choices[0].message.content
                self.logger.debug(f"AI原始响应:\n{result_text}")
                
                # 尝试提取JSON部分
                try:
                    start_idx = result_text.find('{')
                    end_idx = result_text.rindex('}') + 1
                    if start_idx != -1 and end_idx != -1:
                        json_text = result_text[start_idx:end_idx]
                        self.logger.debug(f"提取的JSON文本:\n{json_text}")
                        classification_results = json.loads(json_text)
                    else:
                        raise ValueError("无法在响应中找到JSON格式的内容")
                except (ValueError, json.JSONDecodeError) as e:
                    self.logger.error(f"JSON解析失败: {str(e)}")
                    self.logger.error(f"原始响应内容: {result_text}")
                    raise ValueError(f"AI响应格式错误: {str(e)}")
                
                self.logger.debug(f"AI响应解析完成，获得 {len(classification_results)} 个分类结果")
                
                # 处理结果
                results = {}
                new_categories = set()
                reused_categories = set()
                
                for file_info in files_info:
                    filename = file_info['name']
                    file_path = file_info['absolute_path']
                    
                    if filename in classification_results:
                        result = classification_results[filename]
                        target_folder = result['target_folder']
                        
                        # 记录分类使用情况
                        if target_folder in existing_categories:
                            reused_categories.add(target_folder)
                        else:
                            new_categories.add(target_folder)
                            
                        results[file_path] = {
                            'target_folder': target_folder,
                            'reason': result['reason'],
                            'confidence': self._calculate_confidence(result)
                        }
                        self.logger.debug(f"文件 {filename} 被分类到 {target_folder}")
                    else:
                        results[file_path] = {
                            'target_folder': '未分类',
                            'reason': '无法确定合适的分类',
                            'confidence': 0.0
                        }
                        self.logger.debug(f"文件 {filename} 无法分类")
                
                # 输出分类统计信息
                self.logger.debug(f"分类完成统计:")
                self.logger.debug(f"- 复用已有分类: {len(reused_categories)} 个 {sorted(reused_categories)}")
                self.logger.debug(f"- 新建分类: {len(new_categories)} 个 {sorted(new_categories)}")
                
                return results
                
            except Exception as e:
                self.logger.error(f"处理AI响应时出错: {str(e)}")
                raise
                
        except Exception as e:
            self.logger.error(f"文件分类过程中出错: {str(e)}")
            raise
            
    def _calculate_confidence(self, result: Dict) -> float:
        """计算分类置信度"""
        # 基于分类理由的完整性和具体程度计算置信度
        confidence = 0.5  # 基础置信度
        
        if 'reason' in result and result['reason']:
            # 根据理由的长度和关键词增加置信度
            reason = result['reason']
            if len(reason) > 50:
                confidence += 0.2
            if '因为' in reason or '基于' in reason:
                confidence += 0.1
            if '特征' in reason or '类型' in reason:
                confidence += 0.1
            if '确定' in reason or '明确' in reason:
                confidence += 0.1
                
        return min(confidence, 1.0)  # 确保置信度不超过1.0
        
    def _get_api_key(self) -> str:
        """获取 API 密钥"""
        api_key = self.config_manager.get_config("deepseek.api_key")
        if not api_key:
            raise ValueError("未设置 DeepSeek API 密钥，请在设置中配置")
        return api_key
        
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
        
    def _is_text_file(self, extension: str) -> bool:
        """判断是否为文本文件"""
        text_extensions = {
            '.txt', '.md', '.py', '.java', '.cpp', '.h', '.c', '.js', 
            '.html', '.css', '.xml', '.json', '.yaml', '.yml', '.ini',
            '.cfg', '.conf', '.log', '.sql', '.sh', '.bat', '.ps1'
        }
        return extension.lower() in text_extensions
        
    def _extract_content_preview(self, file_path: str, max_length: int = 1000) -> Optional[str]:
        """提取文件内容预览"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(max_length)
                if len(content) == max_length:
                    content = content[:content.rindex(' ')] + '...'
                return content
        except Exception as e:
            self.logger.debug(f"提取文件 {file_path} 预览失败: {str(e)}")
            return None
        
    def enhance_files_info(self, files_info: List[Dict]) -> List[Dict]:
        """增强文件信息，添加额外的文件特征
        
        Args:
            files_info: 原始文件信息列表
            
        Returns:
            增强后的文件信息列表
        """
        self.logger.debug(f"开始增强文件信息，共 {len(files_info)} 个文件")
        enhanced_info = []
        
        for file_info in files_info:
            try:
                # 复制原始信息
                enhanced = file_info.copy()
                
                # 添加文件类型信息
                if "extension" not in enhanced:
                    enhanced["extension"] = os.path.splitext(enhanced["name"])[1].lower()
                
                # 添加文件大小的可读格式
                if "size" in enhanced:
                    enhanced["size_readable"] = self._format_size(enhanced["size"])
                
                # 尝试提取文本预览（仅对文本文件）
                if self._is_text_file(enhanced["extension"]):
                    preview = self._extract_content_preview(enhanced["absolute_path"])
                    if preview:
                        enhanced["content_preview"] = preview
                
                enhanced_info.append(enhanced)
                self.logger.debug(f"文件 {enhanced['name']} 信息增强完成")
                
            except Exception as e:
                self.logger.error(f"增强文件 {file_info.get('name', 'unknown')} 信息时出错: {str(e)}")
                # 如果增强失败，仍然添加原始信息
                enhanced_info.append(file_info)
                
        self.logger.debug("文件信息增强完成")
        return enhanced_info 