#!/usr/bin/env python3
"""
用户ID获取辅助函数
配置路径: user_id_helper.py (项目根目录)
"""

def get_current_user_id():
    """获取当前登录用户ID"""
    try:
        from flask import request, has_request_context
        if has_request_context():
            current_user = getattr(request, 'current_user', None)
            if current_user:
                return current_user.user_id
    except:
        pass
    return None