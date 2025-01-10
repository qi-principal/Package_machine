import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    """配置管理器，处理配置文件的加载和保存"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.default_config: Dict[str, Any] = {}
        self.user_config: Dict[str, Any] = {}
        
        # 获取用户配置目录
        self.user_config_dir = os.path.join(os.path.expanduser('~'), '.package_machine')
        self.user_config_path = os.path.join(self.user_config_dir, 'config.json')
        
        # 获取默认配置文件路径
        if getattr(sys, 'frozen', False):
            # 如果是打包后的可执行文件
            base_path = sys._MEIPASS
        else:
            # 如果是开发环境
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        self.default_config_path = os.path.join(base_path, 'src', 'default_config.json')
        
        # 初始化配置
        self._init_config()
    
    def _init_config(self):
        """初始化配置"""
        # 加载默认配置
        try:
            with open(self.default_config_path, 'r', encoding='utf-8') as f:
                self.default_config = json.load(f)
        except Exception as e:
            self.logger.error(f"加载默认配置失败: {e}")
            self.default_config = {}
        
        # 确保用户配置目录存在
        os.makedirs(self.user_config_dir, exist_ok=True)
        
        # 加载用户配置
        if os.path.exists(self.user_config_path):
            try:
                with open(self.user_config_path, 'r', encoding='utf-8') as f:
                    self.user_config = json.load(f)
            except Exception as e:
                self.logger.error(f"加载用户配置失败: {e}")
                self.user_config = {}
        
        # 如果用户配置不存在，创建一个空的配置文件
        if not os.path.exists(self.user_config_path):
            self.save_user_config({})
    
    def get_config(self, key: str, default=None) -> Any:
        """获取配置值，优先使用用户配置"""
        return self.user_config.get(key, self.default_config.get(key, default))
    
    def set_config(self, key: str, value: Any):
        """设置用户配置"""
        self.user_config[key] = value
        self.save_user_config()
    
    def save_user_config(self, config: Dict[str, Any] = None):
        """保存用户配置到文件"""
        if config is not None:
            self.user_config = config
        
        try:
            with open(self.user_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.user_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存用户配置失败: {e}")
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置（默认配置和用户配置的合并结果）"""
        config = self.default_config.copy()
        config.update(self.user_config)
        return config 