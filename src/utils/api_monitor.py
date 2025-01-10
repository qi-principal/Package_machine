"""
OpenAI API监控模块
提供API调用统计和流量监控功能
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

class APIMonitor:
    """API监控类"""
    
    def __init__(self, log_file: str = "api_usage.json"):
        self.logger = logging.getLogger(__name__)
        self.log_file = log_file
        self.usage_data = self._load_usage_data()
        
    def _load_usage_data(self) -> Dict:
        """加载使用数据"""
        try:
            if Path(self.log_file).exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "daily_usage": {},
                "monthly_usage": {},
                "last_update": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"加载API使用数据失败: {str(e)}")
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "daily_usage": {},
                "monthly_usage": {},
                "last_update": datetime.now().isoformat()
            }
            
    def _save_usage_data(self):
        """保存使用数据"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.usage_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存API使用数据失败: {str(e)}")
            
    def record_api_call(self, model: str, prompt_tokens: int, completion_tokens: int):
        """
        记录API调用
        
        Args:
            model: 使用的模型名称
            prompt_tokens: 提示词token数
            completion_tokens: 完成词token数
        """
        try:
            # 计算成本（根据OpenAI的定价）
            cost = self._calculate_cost(model, prompt_tokens, completion_tokens)
            total_tokens = prompt_tokens + completion_tokens
            
            # 更新总计数据
            self.usage_data["total_calls"] += 1
            self.usage_data["total_tokens"] += total_tokens
            self.usage_data["total_cost"] += cost
            
            # 更新每日使用数据
            today = datetime.now().strftime("%Y-%m-%d")
            if today not in self.usage_data["daily_usage"]:
                self.usage_data["daily_usage"][today] = {
                    "calls": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            self.usage_data["daily_usage"][today]["calls"] += 1
            self.usage_data["daily_usage"][today]["tokens"] += total_tokens
            self.usage_data["daily_usage"][today]["cost"] += cost
            
            # 更新每月使用数据
            month = datetime.now().strftime("%Y-%m")
            if month not in self.usage_data["monthly_usage"]:
                self.usage_data["monthly_usage"][month] = {
                    "calls": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            self.usage_data["monthly_usage"][month]["calls"] += 1
            self.usage_data["monthly_usage"][month]["tokens"] += total_tokens
            self.usage_data["monthly_usage"][month]["cost"] += cost
            
            # 更新最后更新时间
            self.usage_data["last_update"] = datetime.now().isoformat()
            
            # 保存数据
            self._save_usage_data()
            
        except Exception as e:
            self.logger.error(f"记录API调用失败: {str(e)}")
            
    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        计算API调用成本
        
        Args:
            model: 使用的模型名称
            prompt_tokens: 提示词token数
            completion_tokens: 完成词token数
            
        Returns:
            float: 调用成本（美元）
        """
        # DeepSeek API定价
        pricing = {
            "deepseek-chat": {
                "prompt": 0.002,  # 每1000 tokens
                "completion": 0.002
            },
            "deepseek-coder": {
                "prompt": 0.003,
                "completion": 0.003
            }
        }
        
        if model not in pricing:
            self.logger.warning(f"未知模型 {model}，使用deepseek-chat的定价")
            model = "deepseek-chat"
            
        model_pricing = pricing[model]
        prompt_cost = (prompt_tokens / 1000) * model_pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * model_pricing["completion"]
        
        return prompt_cost + completion_cost
        
    def get_daily_usage(self, days: int = 7) -> List[Dict]:
        """
        获取每日使用统计
        
        Args:
            days: 获取最近几天的数据
            
        Returns:
            List[Dict]: 每日使用数据列表
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days-1)
            
            daily_stats = []
            current_date = start_date
            
            while current_date <= end_date:
                date_str = current_date.strftime("%Y-%m-%d")
                if date_str in self.usage_data["daily_usage"]:
                    stats = self.usage_data["daily_usage"][date_str]
                else:
                    stats = {"calls": 0, "tokens": 0, "cost": 0.0}
                    
                daily_stats.append({
                    "date": date_str,
                    **stats
                })
                
                current_date += timedelta(days=1)
                
            return daily_stats
            
        except Exception as e:
            self.logger.error(f"获取每日使用统计失败: {str(e)}")
            return []
            
    def get_monthly_usage(self, months: int = 3) -> List[Dict]:
        """
        获取每月使用统计
        
        Args:
            months: 获取最近几个月的数据
            
        Returns:
            List[Dict]: 每月使用数据列表
        """
        try:
            current_date = datetime.now()
            monthly_stats = []
            
            for i in range(months):
                month_str = (current_date - timedelta(days=30*i)).strftime("%Y-%m")
                if month_str in self.usage_data["monthly_usage"]:
                    stats = self.usage_data["monthly_usage"][month_str]
                else:
                    stats = {"calls": 0, "tokens": 0, "cost": 0.0}
                    
                monthly_stats.append({
                    "month": month_str,
                    **stats
                })
                
            return monthly_stats
            
        except Exception as e:
            self.logger.error(f"获取每月使用统计失败: {str(e)}")
            return []
            
    def get_total_usage(self) -> Dict:
        """
        获取总使用统计
        
        Returns:
            Dict: 总使用数据
        """
        return {
            "total_calls": self.usage_data["total_calls"],
            "total_tokens": self.usage_data["total_tokens"],
            "total_cost": self.usage_data["total_cost"],
            "last_update": self.usage_data["last_update"]
        } 