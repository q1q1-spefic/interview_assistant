#!/usr/bin/env python3
"""
邮箱验证系统
配置路径: email_verification.py (项目根目录)
"""

import sqlite3
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from loguru import logger

class EmailVerification:
    """邮箱验证管理器"""
    
    def __init__(self, db_path: str = "data/users.db"):
        self.db_path = db_path
        self._init_verification_table()
    
    def _init_verification_table(self):
        """初始化验证表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_verifications (
                user_id TEXT PRIMARY KEY,
                verification_code TEXT NOT NULL,
                created_time TEXT NOT NULL,
                verified_time TEXT,
                is_verified BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # 为用户表添加邮箱验证字段
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE')
        except sqlite3.OperationalError:
            pass
        
        conn.commit()
        conn.close()
    
    def send_verification_email(self, user_id: str, email: str, username: str) -> bool:
        """发送验证邮件"""
        verification_code = secrets.token_hex(16)
        
        # 保存验证码
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO email_verifications 
                (user_id, verification_code, created_time)
                VALUES (?, ?, ?)
            ''', (user_id, verification_code, datetime.now().isoformat()))
            
            conn.commit()
            
            # 发送邮件（模拟）
            verification_link = f"https://interviewasssistant.com/verify_email?code={verification_code}"
            
            logger.info(f"邮箱验证链接生成: {email} -> {verification_link}")
            # 这里应该集成真实的邮件发送服务
            
            return True
            
        except Exception as e:
            logger.error(f"发送验证邮件失败: {e}")
            return False
        finally:
            conn.close()
    
    def verify_email(self, verification_code: str) -> tuple:
        """验证邮箱"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT user_id, created_time 
                FROM email_verifications 
                WHERE verification_code = ? AND is_verified = FALSE
            ''', (verification_code,))
            
            result = cursor.fetchone()
            if not result:
                return False, '验证码无效'
            
            user_id, created_time = result
            
            # 检查验证码是否过期（24小时）
            created = datetime.fromisoformat(created_time)
            if datetime.now() - created > timedelta(hours=24):
                return False, '验证码已过期'
            
            # 更新验证状态
            cursor.execute('''
                UPDATE email_verifications 
                SET is_verified = TRUE, verified_time = ?
                WHERE verification_code = ?
            ''', (datetime.now().isoformat(), verification_code))
            
            cursor.execute('''
                UPDATE users 
                SET email_verified = TRUE
                WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            
            # 更新推广系统中的验证状态
            try:
                from referral_tracker import referral_tracker
                referral_tracker.update_email_verification(user_id)
            except:
                pass
            
            logger.info(f"邮箱验证成功: {user_id}")
            return True, user_id
            
        except Exception as e:
            logger.error(f"邮箱验证失败: {e}")
            return False, '验证失败'
        finally:
            conn.close()

# 全局实例
email_verification = EmailVerification()
