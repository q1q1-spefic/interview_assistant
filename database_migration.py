#!/usr/bin/env python3
"""
数据库迁移脚本
配置路径: database_migration.py (项目根目录)
"""

import sqlite3
import os
from loguru import logger

def migrate_database():
    """执行数据库迁移"""
    db_path = "data/templates.db"
    
    # 确保数据库文件存在
    if not os.path.exists(db_path):
        logger.info("数据库文件不存在，将在首次使用时创建")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查 templates 表是否有 user_id 字段
        cursor.execute("PRAGMA table_info(templates)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in columns:
            logger.info("为 templates 表添加 user_id 字段...")
            cursor.execute('ALTER TABLE templates ADD COLUMN user_id TEXT')
            logger.info("✅ templates 表 user_id 字段添加成功")
        else:
            logger.info("templates 表已有 user_id 字段")
        
        # 检查 resume_versions 表是否存在且有 user_id 字段
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='resume_versions'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(resume_versions)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns:
                logger.info("为 resume_versions 表添加 user_id 字段...")
                cursor.execute('ALTER TABLE resume_versions ADD COLUMN user_id TEXT')
                logger.info("✅ resume_versions 表 user_id 字段添加成功")
            else:
                logger.info("resume_versions 表已有 user_id 字段")
        
        # 检查 template_usage 表是否存在且有 user_id 字段
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='template_usage'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(template_usage)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_id' not in columns:
                logger.info("为 template_usage 表添加 user_id 字段...")
                cursor.execute('ALTER TABLE template_usage ADD COLUMN user_id TEXT')
                logger.info("✅ template_usage 表 user_id 字段添加成功")
            else:
                logger.info("template_usage 表已有 user_id 字段")
        
        conn.commit()
        logger.info("🎉 数据库迁移完成")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"数据库迁移失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()