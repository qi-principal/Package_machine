"""
配置管理模块
提供配置的读写和管理功能
"""
import json
import os
import logging
from typing import Any, Dict, Optional

class ConfigManager:
    """配置管理类"""
    
    def __init__(self, config_file: str = "config.json"):
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file
        self.config: Dict[str, Any] = self._load_default_config()
        self._load_config()
        
    def _load_default_config(self) -> Dict[str, Any]:
        """
        加载默认配置
        
        Returns:
            Dict[str, Any]: 默认配置字典
        """
        return {
            "allowed_extensions": [
                ".txt", ".doc", ".docx", ".pdf",
                ".jpg", ".jpeg", ".png", ".gif",
                ".mp3", ".mp4", ".zip", ".rar"
            ],
            "backup_enabled": True,
            "backup_dir": "backups",
            "max_file_size": 1024 * 1024 * 100,  # 100MB
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "ui": {
                "theme": "light",
                "language": "zh_CN",
                "window_size": {
                    "width": 800,
                    "height": 600
                }
            }
        }
        
    def _load_config(self) -> None:
        """从文件加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 更新默认配置，保留默认值
                    self._update_nested_dict(self.config, loaded_config)
        except Exception as e:
            self.logger.error(f"加载配置文件时发生错误: {str(e)}")
            
    def _update_nested_dict(self, base_dict: dict, update_dict: dict) -> None:
        """
        递归更新嵌套字典
        
        Args:
            base_dict: 基础字典
            update_dict: 更新字典
        """
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._update_nested_dict(base_dict[key], value)
            else:
                base_dict[key] = value
                
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            self.logger.error(f"保存配置文件时发生错误: {str(e)}")
            return False
            
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        try:
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def set_config(self, key: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            
        Returns:
            bool: 设置是否成功
        """
        try:
            keys = key.split('.')
            config = self.config
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            config[keys[-1]] = value
            return True
        except Exception as e:
            self.logger.error(f"设置配置项 {key} 时发生错误: {str(e)}")
            return False
            
    def get_allowed_extensions(self) -> list:
        """
        获取允许的文件扩展名列表
        
        Returns:
            list: 允许的文件扩展名列表
        """
        return self.get_config('allowed_extensions', [])
        
    def add_allowed_extension(self, extension: str) -> bool:
        """
        添加允许的文件扩展名
        
        Args:
            extension: 文件扩展名
            
        Returns:
            bool: 添加是否成功
        """
        if not extension.startswith('.'):
            extension = f'.{extension}'
        extensions = self.get_allowed_extensions()
        if extension.lower() not in [ext.lower() for ext in extensions]:
            extensions.append(extension.lower())
            return self.set_config('allowed_extensions', extensions)
        return True
        
    def remove_allowed_extension(self, extension: str) -> bool:
        """
        移除允许的文件扩展名
        
        Args:
            extension: 文件扩展名
            
        Returns:
            bool: 移除是否成功
        """
        if not extension.startswith('.'):
            extension = f'.{extension}'
        extensions = self.get_allowed_extensions()
        extensions = [ext for ext in extensions if ext.lower() != extension.lower()]
        return self.set_config('allowed_extensions', extensions) 