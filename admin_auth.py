#!/usr/bin/env python3
"""
管理员认证中间件
配置路径: admin_auth.py (项目根目录)
"""

import os
from functools import wraps
from flask import request, jsonify, session, redirect, url_for
from loguru import logger

# 管理员密码（环境变量）
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查管理员会话
        if not session.get('admin_authenticated'):
            # 简单密码验证
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header == f'Bearer {ADMIN_PASSWORD}':
                session['admin_authenticated'] = True
                session.permanent = True
            else:
                if request.is_json:
                    return jsonify({'error': '需要管理员权限', 'admin_required': True}), 401
                return redirect('/admin/login')
        
        return f(*args, **kwargs)
    return decorated_function

def check_admin_auth():
    """检查管理员认证状态"""
    return session.get('admin_authenticated', False)