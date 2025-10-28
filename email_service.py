#!/usr/bin/env python3
"""
邮件服务模块 - 支持多种发送方式
配置路径: email_service.py (项目根目录)
"""

import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from loguru import logger

class EmailService:
    """多重邮件发送服务"""
    
    def __init__(self):
        # 多个SMTP配置（按优先级排序）
        self.smtp_configs = [
            {
                'name': 'Gmail',
                'host': 'smtp.gmail.com',
                'port': 587,
                'sender_email': 'interviewassistant.feedback@gmail.com',
                'sender_password': 'ecmx farh xjfd ypbp',
                'timeout': 10
            },
            {
                'name': '163',
                'host': 'smtp.163.com',
                'port': 25,
                'sender_email': 'interviewassistant@163.com',  # 如果有163邮箱的话
                'sender_password': '',  # 需要配置
                'timeout': 10
            }
        ]
        
        self.receiver_email = 'liu.lucian6@gmail.com'
        self.backup_file = 'data/feedback_backup.json'
        
        # 确保备份目录存在
        os.makedirs('data', exist_ok=True)
    
    def send_feedback_email(self, feedback_content, user_info):
        """发送反馈邮件（多重尝试）"""
        # 先保存到本地文件
        self._save_to_backup(feedback_content, user_info)
        
        # 尝试多种邮件服务
        for config in self.smtp_configs:
            if not config.get('sender_password'):
                continue
                
            try:
                logger.info(f"尝试通过 {config['name']} 发送邮件...")
                if self._send_via_smtp(feedback_content, user_info, config):
                    logger.info(f"✅ 通过 {config['name']} 发送成功")
                    return True
            except Exception as e:
                logger.warning(f"❌ {config['name']} 发送失败: {e}")
                continue
        
        # 所有邮件服务都失败，但已保存到本地
        logger.error("所有邮件服务都失败，反馈已保存到本地文件")
        return False
    
    def _send_via_smtp(self, feedback_content, user_info, config):
        """通过指定SMTP发送邮件"""
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = config['sender_email']
        msg['To'] = self.receiver_email
        msg['Subject'] = '【即答侠】用户反馈 - 来自 interviewasssistant.com'
        
        # 邮件正文
        email_body = f"""
======================
📝 用户反馈
======================

💬 对"即答侠"的改进建议：
{feedback_content}

📊 用户信息：
• 提交时间：{user_info['timestamp']}
• 用户IP：{user_info['ip_address']}
• 用户代理：{user_info['user_agent']}
• 来源页面：{user_info['referer']}
• 发送方式：{config['name']} SMTP

======================
即答侠反馈系统自动发送
https://interviewasssistant.com
"""
        
        msg.attach(MIMEText(email_body, 'plain', 'utf-8'))
        
        # 发送邮件
        server = smtplib.SMTP(config['host'], config['port'], timeout=config['timeout'])
        server.starttls()
        server.login(config['sender_email'], config['sender_password'])
        text = msg.as_string()
        server.sendmail(config['sender_email'], self.receiver_email, text)
        server.quit()
        
        return True
    
    def _save_to_backup(self, feedback_content, user_info):
        """保存反馈到本地文件"""
        try:
            feedback_data = {
                'feedback': feedback_content,
                'user_info': user_info,
                'saved_time': datetime.now().isoformat()
            }
            
            # 读取现有数据
            existing_data = []
            if os.path.exists(self.backup_file):
                try:
                    with open(self.backup_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except:
                    existing_data = []
            
            # 添加新数据
            existing_data.append(feedback_data)
            
            # 保存到文件
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"反馈已保存到本地文件: {self.backup_file}")
            
        except Exception as e:
            logger.error(f"保存反馈到本地文件失败: {e}")
    
    def get_backup_feedbacks(self):
        """获取本地备份的反馈"""
        try:
            if os.path.exists(self.backup_file):
                with open(self.backup_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"读取本地反馈失败: {e}")
            return []
    
    def send_backup_summary(self):
        """发送备份反馈汇总邮件"""
        backups = self.get_backup_feedbacks()
        if not backups:
            return False
        
        # 构建汇总邮件
        summary_content = f"""
======================
📋 反馈汇总报告
======================

📊 统计信息：
• 反馈总数：{len(backups)}
• 汇总时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📝 反馈详情：
"""
        
        for i, backup in enumerate(backups, 1):
            summary_content += f"""
--- 反馈 #{i} ---
💬 内容：{backup['feedback']}
⏰ 时间：{backup['user_info']['timestamp']}
🌐 IP：{backup['user_info']['ip_address']}
📱 设备：{backup['user_info']['user_agent'][:50]}...

"""
        
        summary_content += """
======================
即答侠反馈系统自动汇总
https://interviewasssistant.com
"""
        
        # 尝试发送汇总邮件
        user_info = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ip_address': 'system',
            'user_agent': 'feedback_system',
            'referer': 'auto_summary'
        }
        
        return self.send_feedback_email(f"汇总报告 - 共{len(backups)}条反馈", user_info)