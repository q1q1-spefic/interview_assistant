#!/usr/bin/env python3
"""
用户数据迁移工具
配置路径: user_data_migration.py (项目根目录)
"""

import sqlite3
import json
from datetime import datetime
from loguru import logger

class UserDataMigrator:
    """用户数据迁移器"""
    
    def __init__(self, db_path: str = "data/templates.db"):
        self.db_path = db_path
    
    def migrate_guest_data_to_user(self, user_id: str, guest_data: dict = None):
        """将游客数据迁移到用户账户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 迁移模板数据
            if guest_data and 'templates' in guest_data:
                for template in guest_data['templates']:
                    cursor.execute('''
                        UPDATE templates 
                        SET user_id = ? 
                        WHERE id = ? AND user_id IS NULL
                    ''', (user_id, template['id']))
            
            # 迁移简历版本数据
            if guest_data and 'resume_versions' in guest_data:
                for version in guest_data['resume_versions']:
                    cursor.execute('''
                        UPDATE resume_versions 
                        SET user_id = ? 
                        WHERE version_id = ? AND user_id IS NULL
                    ''', (user_id, version['version_id']))
            
            conn.commit()
            logger.info(f"游客数据迁移完成: 用户 {user_id}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"数据迁移失败: {e}")
            raise
        finally:
            conn.close()
    
    def cleanup_anonymous_data(self, days_old: int = 7):
        """清理旧的匿名数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 计算截止时间
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
            
            # 清理旧的匿名模板
            cursor.execute('''
                DELETE FROM templates 
                WHERE user_id IS NULL 
                AND datetime(created_time) < datetime(?, 'unixepoch')
            ''', (cutoff_time,))
            
            template_count = cursor.rowcount
            
            # 清理旧的匿名简历版本
            cursor.execute('''
                DELETE FROM resume_versions 
                WHERE user_id IS NULL 
                AND datetime(created_time) < datetime(?, 'unixepoch')
            ''', (cutoff_time,))
            
            version_count = cursor.rowcount
            
            conn.commit()
            logger.info(f"清理完成: 删除 {template_count} 个匿名模板, {version_count} 个匿名简历版本")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"清理匿名数据失败: {e}")
        finally:
            conn.close()

# 全局迁移器实例
user_data_migrator = UserDataMigrator()