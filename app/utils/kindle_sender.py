#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kindle邮件发送工具
"""
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

def send_to_kindle(
    kindle_email,
    sender_email,
    sender_password,
    file_path,
    smtp_server="smtp.163.com",
    smtp_port=465,
    subject="convert"
):
    """
    发送文件到Kindle邮箱
    
    Args:
        kindle_email: Kindle邮箱地址
        sender_email: 发送方邮箱
        sender_password: 发送方邮箱密码/授权码
        file_path: 文件路径
        smtp_server: SMTP服务器
        smtp_port: SMTP端口
        subject: 邮件主题（convert会自动转换格式）
    
    Returns:
        bool: 是否发送成功
    """
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"错误: 文件不存在 - {file_path}")
        return False
    
    # 检查文件大小（邮件限制50MB）
    file_size_mb = file_path.stat().st_size / 1024 / 1024
    if file_size_mb > 50:
        print(f"警告: 文件大小 {file_size_mb:.1f}MB 超过50MB限制")
        return False
    
    print(f"准备发送: {file_path.name} ({file_size_mb:.1f}MB)")
    print(f"发送到: {kindle_email}")
    
    try:
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = kindle_email
        msg['Subject'] = subject
        
        # 添加邮件正文
        body = f"Sending {file_path.name} to Kindle\n\nKindle Transfer App"
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 添加附件
        with open(file_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        
        # 处理文件名编码
        filename = file_path.name
        part.add_header(
            'Content-Disposition',
            'attachment',
            filename=('utf-8', '', filename)
        )
        msg.attach(part)
        
        # 连接SMTP服务器
        print(f"连接SMTP服务器: {smtp_server}:{smtp_port}")
        
        if smtp_port == 465:
            # SSL连接
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            # TLS连接
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        
        # 登录
        print("登录邮箱...")
        server.login(sender_email, sender_password)
        
        # 发送邮件
        print("发送邮件...")
        text = msg.as_string()
        server.sendmail(sender_email, kindle_email, text)
        server.quit()
        
        print("发送成功！")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("错误: 邮箱认证失败，请检查邮箱和密码/授权码")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP错误: {e}")
        return False
    except Exception as e:
        print(f"发送失败: {e}")
        return False

def get_smtp_config(email):
    """
    根据邮箱类型返回SMTP配置
    
    Args:
        email: 邮箱地址
    
    Returns:
        tuple: (smtp_server, smtp_port)
    """
    email = email.lower()
    
    configs = {
        '163.com': ('smtp.163.com', 465),
        '126.com': ('smtp.126.com', 465),
        'qq.com': ('smtp.qq.com', 587),
        'gmail.com': ('smtp.gmail.com', 587),
        'outlook.com': ('smtp-mail.outlook.com', 587),
        'hotmail.com': ('smtp-mail.outlook.com', 587),
        'yeah.net': ('smtp.yeah.net', 465),
        'sina.com': ('smtp.sina.com', 465),
        'sohu.com': ('smtp.sohu.com', 465),
    }
    
    for domain, config in configs.items():
        if domain in email:
            return config
    
    # 默认配置
    return ('smtp.163.com', 465)