"""
分类存储系统
提供分类数据的持久化存储和管理功能
"""
import os
import json
import sqlite3
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime

class CategoryStorage:
    """分类存储管理类"""
    
    def __init__(self, db_path: str = "categories.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self) -> None:
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建分类表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # 创建文件-分类映射表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    category_id INTEGER NOT NULL,
                    confidence FLOAT DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (id),
                    UNIQUE (file_path, category_id)
                )
                """)
                
                # 创建分类历史表
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS category_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    category_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                )
                """)
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"初始化数据库时发生错误: {str(e)}")
            raise
            
    def add_category(self, category_name: str) -> bool:
        """
        添加新分类
        
        Args:
            category_name: 分类名称
            
        Returns:
            bool: 添加是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                    (category_name,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"添加分类 {category_name} 时发生错误: {str(e)}")
            return False
            
    def get_all_categories(self) -> List[str]:
        """
        获取所有分类
        
        Returns:
            List[str]: 分类名称列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM categories ORDER BY name")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"获取分类列表时发生错误: {str(e)}")
            return []
            
    def add_file_category(self, file_path: str, category_name: str, confidence: float = 1.0) -> bool:
        """
        为文件添加分类
        
        Args:
            file_path: 文件路径
            category_name: 分类名称
            confidence: 分类置信度
            
        Returns:
            bool: 添加是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 确保分类存在
                cursor.execute(
                    "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                    (category_name,)
                )
                
                # 获取分类ID
                cursor.execute(
                    "SELECT id FROM categories WHERE name = ?",
                    (category_name,)
                )
                category_id = cursor.fetchone()[0]
                
                # 添加文件-分类映射
                cursor.execute("""
                INSERT OR REPLACE INTO file_categories 
                (file_path, category_id, confidence) VALUES (?, ?, ?)
                """, (file_path, category_id, confidence))
                
                # 记录历史
                cursor.execute("""
                INSERT INTO category_history 
                (file_path, category_id, action) VALUES (?, ?, 'add')
                """, (file_path, category_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"为文件 {file_path} 添加分类 {category_name} 时发生错误: {str(e)}")
            return False
            
    def get_file_categories(self, file_path: str) -> List[Dict]:
        """
        获取文件的所有分类
        
        Args:
            file_path: 文件路径
            
        Returns:
            List[Dict]: 分类信息列表，包含分类名称和置信度
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT c.name, fc.confidence
                FROM file_categories fc
                JOIN categories c ON fc.category_id = c.id
                WHERE fc.file_path = ?
                ORDER BY fc.confidence DESC
                """, (file_path,))
                
                return [
                    {"category": name, "confidence": confidence}
                    for name, confidence in cursor.fetchall()
                ]
                
        except Exception as e:
            self.logger.error(f"获取文件 {file_path} 的分类时发生错误: {str(e)}")
            return []
            
    def remove_file_category(self, file_path: str, category_name: str) -> bool:
        """
        移除文件的分类
        
        Args:
            file_path: 文件路径
            category_name: 分类名称
            
        Returns:
            bool: 移除是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取分类ID
                cursor.execute(
                    "SELECT id FROM categories WHERE name = ?",
                    (category_name,)
                )
                result = cursor.fetchone()
                if not result:
                    return False
                    
                category_id = result[0]
                
                # 删除文件-分类映射
                cursor.execute("""
                DELETE FROM file_categories 
                WHERE file_path = ? AND category_id = ?
                """, (file_path, category_id))
                
                # 记录历史
                cursor.execute("""
                INSERT INTO category_history 
                (file_path, category_id, action) VALUES (?, ?, 'remove')
                """, (file_path, category_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"移除文件 {file_path} 的分类 {category_name} 时发生错误: {str(e)}")
            return False
            
    def get_files_by_category(self, category_name: str) -> List[str]:
        """
        获取指定分类下的所有文件
        
        Args:
            category_name: 分类名称
            
        Returns:
            List[str]: 文件路径列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT fc.file_path
                FROM file_categories fc
                JOIN categories c ON fc.category_id = c.id
                WHERE c.name = ?
                ORDER BY fc.file_path
                """, (category_name,))
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"获取分类 {category_name} 下的文件时发生错误: {str(e)}")
            return []
            
    def get_category_history(self, file_path: Optional[str] = None) -> List[Dict]:
        """
        获取分类历史记录
        
        Args:
            file_path: 可选的文件路径过滤
            
        Returns:
            List[Dict]: 历史记录列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if file_path:
                    cursor.execute("""
                    SELECT ch.file_path, c.name, ch.action, ch.created_at
                    FROM category_history ch
                    JOIN categories c ON ch.category_id = c.id
                    WHERE ch.file_path = ?
                    ORDER BY ch.created_at DESC
                    """, (file_path,))
                else:
                    cursor.execute("""
                    SELECT ch.file_path, c.name, ch.action, ch.created_at
                    FROM category_history ch
                    JOIN categories c ON ch.category_id = c.id
                    ORDER BY ch.created_at DESC
                    """)
                    
                return [
                    {
                        "file_path": row[0],
                        "category": row[1],
                        "action": row[2],
                        "timestamp": row[3]
                    }
                    for row in cursor.fetchall()
                ]
                
        except Exception as e:
            self.logger.error(f"获取分类历史记录时发生错误: {str(e)}")
            return []
            
    def cleanup_invalid_entries(self) -> int:
        """
        清理无效的分类记录（指向不存在文件的记录）
        
        Returns:
            int: 清理的记录数量
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取所有文件路径
                cursor.execute("SELECT DISTINCT file_path FROM file_categories")
                file_paths = cursor.fetchall()
                
                # 检查并删除不存在的文件记录
                cleaned_count = 0
                for (file_path,) in file_paths:
                    if not os.path.exists(file_path):
                        cursor.execute("""
                        DELETE FROM file_categories WHERE file_path = ?
                        """, (file_path,))
                        cleaned_count += cursor.rowcount
                        
                conn.commit()
                return cleaned_count
                
        except Exception as e:
            self.logger.error(f"清理无效分类记录时发生错误: {str(e)}")
            return 0 