#!/usr/bin/env python3
"""
用户认证系统
配置路径: user_auth.py (项目根目录)
"""

import hashlib
import secrets
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from functools import wraps
from flask import session, request, jsonify, redirect, url_for
from loguru import logger

@dataclass
class User:
    """用户数据模型"""
    user_id: str
    username: str
    email: str
    phone: str
    password_hash: str
    created_time: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    login_attempts: int = 0
    locked_until: Optional[datetime] = None

class UserManager:
    """用户管理器"""
    
    def __init__(self, db_path: str = "data/users.db"):
        self.db_path = db_path
        self._init_user_tables()
    
    def _init_user_tables(self):
        """初始化用户数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                phone TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                created_time TEXT NOT NULL,
                last_login TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                login_attempts INTEGER DEFAULT 0,
                locked_until TEXT
            )
        ''')
        
        # 用户会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_time TEXT NOT NULL,
                expires_time TEXT NOT NULL,
                remember_me BOOLEAN DEFAULT FALSE,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # 为现有表添加用户ID字段
        try:
            cursor.execute('ALTER TABLE templates ADD COLUMN user_id TEXT')
        except sqlite3.OperationalError:
            pass  # 字段已存在
            
        try:
            cursor.execute('ALTER TABLE resume_versions ADD COLUMN user_id TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE template_usage ADD COLUMN user_id TEXT')
        except sqlite3.OperationalError:
            pass
        
        conn.commit()
        conn.close()
        logger.info("✅ 用户数据库表初始化完成")
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        try:
            salt, hash_hex = password_hash.split(':')
            password_hash_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_hash_check.hex() == hash_hex
        except:
            return False
    
    def _validate_email(self, email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_phone(self, phone: str) -> bool:
        """验证手机号格式"""
        pattern = r'^1[3-9]\d{9}$'
        return re.match(pattern, phone) is not None
    
    def register_user(self, username: str, password: str, 
                     email: str = None, phone: str = None) -> Tuple[bool, str]:
        """用户注册"""
        # 验证输入
        if not username or len(username) < 3:
            return False, "用户名至少3个字符"
        
        if not password or len(password) < 6:
            return False, "密码至少6个字符"
        
        if not email and not phone:
            return False, "请提供邮箱或手机号"
        
        if email and not self._validate_email(email):
            return False, "邮箱格式不正确"
        
        if phone and not self._validate_phone(phone):
            return False, "手机号格式不正确"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查用户名是否已存在
            cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                return False, "用户名已存在"
            
            # 检查邮箱是否已存在
            if email:
                cursor.execute('SELECT user_id FROM users WHERE email = ?', (email,))
                if cursor.fetchone():
                    return False, "邮箱已被注册"
            
            # 检查手机号是否已存在
            if phone:
                cursor.execute('SELECT user_id FROM users WHERE phone = ?', (phone,))
                if cursor.fetchone():
                    return False, "手机号已被注册"
            
            # 创建用户
            user_id = f"user_{secrets.token_hex(16)}"
            password_hash = self._hash_password(password)
            created_time = datetime.now()
            coupon_expires_at = created_time + timedelta(days=30)  # 代金券30天有效期
            
            cursor.execute('''
                INSERT INTO users (
                    user_id, username, email, phone, password_hash, created_time,
                    free_optimization_count, vip_type, coupon_used, coupon_expires_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, username, email, phone, password_hash, created_time.isoformat(),
                3, 'free', False, coupon_expires_at.isoformat()
            ))
            
            conn.commit()
            logger.info(f"新用户注册: {username} ({user_id}), 代金券到期: {coupon_expires_at}")
            return True, user_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"用户注册失败: {e}")
            return False, "注册失败，请重试"
        finally:
            conn.close()
    
    def login_user(self, login_id: str, password: str, 
                  remember_me: bool = False) -> Tuple[bool, str, Optional[User]]:
        """用户登录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 查找用户（支持用户名、邮箱、手机号登录）
            cursor.execute('''
                SELECT user_id, username, email, phone, password_hash, 
                       is_active, login_attempts, locked_until
                FROM users 
                WHERE username = ? OR email = ? OR phone = ?
            ''', (login_id, login_id, login_id))
            
            row = cursor.fetchone()
            if not row:
                return False, "用户不存在", None
            
            user_id, username, email, phone, password_hash, is_active, login_attempts, locked_until = row
            
            # 检查账户状态
            if not is_active:
                return False, "账户已被禁用", None
            
            # 检查账户锁定状态
            if locked_until:
                locked_time = datetime.fromisoformat(locked_until)
                if datetime.now() < locked_time:
                    return False, f"账户已锁定，请在{locked_time.strftime('%Y-%m-%d %H:%M')}后重试", None
                else:
                    # 解锁账户
                    cursor.execute('''
                        UPDATE users SET locked_until = NULL, login_attempts = 0 
                        WHERE user_id = ?
                    ''', (user_id,))
            
            # 验证密码
            if not self._verify_password(password, password_hash):
                # 增加登录失败次数
                new_attempts = login_attempts + 1
                if new_attempts >= 5:
                    # 锁定账户1小时
                    lock_until = datetime.now() + timedelta(hours=1)
                    cursor.execute('''
                        UPDATE users SET login_attempts = ?, locked_until = ? 
                        WHERE user_id = ?
                    ''', (new_attempts, lock_until.isoformat(), user_id))
                    conn.commit()
                    return False, "登录失败次数过多，账户已锁定1小时", None
                else:
                    cursor.execute('''
                        UPDATE users SET login_attempts = ? 
                        WHERE user_id = ?
                    ''', (new_attempts, user_id))
                    conn.commit()
                    return False, "密码错误", None
            
            # 登录成功，重置失败次数
            cursor.execute('''
                UPDATE users SET login_attempts = 0, locked_until = NULL, last_login = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))
            
            # 创建会话
            session_id = secrets.token_hex(32)
            expires_time = datetime.now() + (timedelta(days=30) if remember_me else timedelta(hours=12))
            
            cursor.execute('''
                INSERT INTO user_sessions 
                (session_id, user_id, created_time, expires_time, remember_me, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id, user_id, datetime.now().isoformat(), expires_time.isoformat(),
                remember_me, request.remote_addr or '', request.user_agent.string or ''
            ))
            
            conn.commit()
            
            user = User(
                user_id=user_id,
                username=username,
                email=email or '',
                phone=phone or '',
                password_hash=password_hash,
                created_time=datetime.now(),
                last_login=datetime.now(),
                is_active=is_active
            )
            
            logger.info(f"用户登录: {username} ({user_id})")
            return True, session_id, user
            
        except Exception as e:
            conn.rollback()
            logger.error(f"用户登录失败: {e}")
            return False, "登录失败，请重试", None
        finally:
            conn.close()
    
    def get_user_by_session(self, session_id: str) -> Optional[User]:
        """通过会话ID获取用户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT u.user_id, u.username, u.email, u.phone, u.password_hash,
                       u.created_time, u.last_login, u.is_active, s.expires_time
                FROM users u
                JOIN user_sessions s ON u.user_id = s.user_id
                WHERE s.session_id = ? AND u.is_active = TRUE
            ''', (session_id,))
            
            row = cursor.fetchone()
            if row:
                expires_time = datetime.fromisoformat(row[8])
                if datetime.now() < expires_time:
                    return User(
                        user_id=row[0],
                        username=row[1],
                        email=row[2] or '',
                        phone=row[3] or '',
                        password_hash=row[4],
                        created_time=datetime.fromisoformat(row[5]),
                        last_login=datetime.fromisoformat(row[6]) if row[6] else None,
                        is_active=row[7]
                    )
                else:
                    # 会话过期，删除
                    cursor.execute('DELETE FROM user_sessions WHERE session_id = ?', (session_id,))
                    conn.commit()
            
            return None
            
        except Exception as e:
            logger.error(f"获取用户会话失败: {e}")
            return None
        finally:
            conn.close()
    
    def logout_user(self, session_id: str):
        """用户登出"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM user_sessions WHERE session_id = ?', (session_id,))
            conn.commit()
            logger.info(f"用户登出: {session_id}")
        except Exception as e:
            logger.error(f"用户登出失败: {e}")
        finally:
            conn.close()
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                DELETE FROM user_sessions 
                WHERE expires_time < ?
            ''', (datetime.now().isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            if deleted_count > 0:
                logger.info(f"清理了 {deleted_count} 个过期会话")
                
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
        finally:
            conn.close()

# 装饰器
def login_required(f):
    """登录required装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"登录检查 - 路径: {request.path}")
        logger.info(f"会话数据: {dict(session)}")
        
        session_id = session.get('session_id') or request.headers.get('Authorization')
        logger.info(f"会话ID: {session_id}")
        
        if not session_id:
            logger.info("未找到会话ID")
            if request.is_json:
                return jsonify({'error': '请先登录', 'login_required': True}), 401
            return redirect(url_for('login'))
        
        # 从全局管理器获取用户管理器
        try:
            from global_manager import get_user_manager
            user_manager = get_user_manager()
            logger.info(f"用户管理器状态: {user_manager is not None}")
            
            if not user_manager:
                logger.error("用户管理器未初始化")
                if request.is_json:
                    return jsonify({'error': '系统初始化中，请稍后重试', 'login_required': True}), 503
                return redirect(url_for('login'))
                
            user = user_manager.get_user_by_session(session_id)
            logger.info(f"用户查询结果: {user is not None}")
            
            if not user:
                logger.info("会话无效或已过期")
                session.pop('session_id', None)
                if request.is_json:
                    return jsonify({'error': '登录已过期，请重新登录', 'login_required': True}), 401
                return redirect(url_for('login'))
            
            # 将用户信息添加到请求上下文
            request.current_user = user
            logger.info(f"登录验证成功: {user.username}")
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"登录验证失败: {e}")
            import traceback
            logger.error(f"登录验证异常详情: {traceback.format_exc()}")
            if request.is_json:
                return jsonify({'error': '系统错误，请重试', 'login_required': True}), 500
            return redirect(url_for('login'))
    
    return decorated_function

def get_current_user() -> Optional[User]:
    """获取当前登录用户"""
    try:
        from flask import request
        return getattr(request, 'current_user', None)
    except:
        return None


