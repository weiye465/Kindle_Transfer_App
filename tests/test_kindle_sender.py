#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kindle邮件发送器测试文件
"""
import unittest
import os
import sys
import tempfile
import shutil
import smtplib
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from email.mime.multipart import MIMEMultipart

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.kindle_sender import send_to_kindle, get_smtp_config


class TestKindleSender(unittest.TestCase):
    """测试Kindle邮件发送功能"""
    
    def setUp(self):
        """测试前的设置"""
        # 创建临时目录和文件
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, 'test.epub')
        
        # 创建测试文件（小于50MB）
        with open(self.test_file, 'wb') as f:
            f.write(b'Test EPUB content for Kindle')
        
        # 测试配置
        self.test_config = {
            'kindle_email': 'test@kindle.com',
            'sender_email': 'sender@163.com',
            'sender_password': 'test_password',
            'smtp_server': 'smtp.163.com',
            'smtp_port': 465
        }
    
    def tearDown(self):
        """测试后的清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_get_smtp_config(self):
        """测试获取SMTP配置"""
        # 测试163邮箱
        server, port = get_smtp_config('user@163.com')
        self.assertEqual(server, 'smtp.163.com')
        self.assertEqual(port, 465)
        
        # 测试126邮箱
        server, port = get_smtp_config('user@126.com')
        self.assertEqual(server, 'smtp.126.com')
        self.assertEqual(port, 465)
        
        # 测试QQ邮箱
        server, port = get_smtp_config('user@qq.com')
        self.assertEqual(server, 'smtp.qq.com')
        self.assertEqual(port, 587)
        
        # 测试Gmail
        server, port = get_smtp_config('user@gmail.com')
        self.assertEqual(server, 'smtp.gmail.com')
        self.assertEqual(port, 587)
        
        # 测试Outlook
        server, port = get_smtp_config('user@outlook.com')
        self.assertEqual(server, 'smtp-mail.outlook.com')
        self.assertEqual(port, 587)
        
        # 测试Hotmail
        server, port = get_smtp_config('user@hotmail.com')
        self.assertEqual(server, 'smtp-mail.outlook.com')
        self.assertEqual(port, 587)
        
        # 测试未知邮箱（使用默认配置）
        server, port = get_smtp_config('user@unknown.com')
        self.assertEqual(server, 'smtp.163.com')
        self.assertEqual(port, 465)
        
        # 测试大小写处理
        server, port = get_smtp_config('USER@QQ.COM')
        self.assertEqual(server, 'smtp.qq.com')
        self.assertEqual(port, 587)
    
    @patch('smtplib.SMTP_SSL')
    def test_send_to_kindle_success_ssl(self, mock_smtp_ssl):
        """测试成功发送邮件（SSL连接）"""
        # 设置模拟SMTP服务器
        mock_server = MagicMock()
        mock_smtp_ssl.return_value = mock_server
        
        result = send_to_kindle(
            kindle_email=self.test_config['kindle_email'],
            sender_email=self.test_config['sender_email'],
            sender_password=self.test_config['sender_password'],
            file_path=self.test_file,
            smtp_server=self.test_config['smtp_server'],
            smtp_port=self.test_config['smtp_port']
        )
        
        self.assertTrue(result)
        
        # 验证SMTP调用
        mock_smtp_ssl.assert_called_once_with('smtp.163.com', 465)
        mock_server.login.assert_called_once_with('sender@163.com', 'test_password')
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()
        
        # 验证发送参数
        send_args = mock_server.sendmail.call_args[0]
        self.assertEqual(send_args[0], 'sender@163.com')  # 发送者
        self.assertEqual(send_args[1], 'test@kindle.com')  # 接收者
        self.assertIsInstance(send_args[2], str)  # 邮件内容
    
    @patch('smtplib.SMTP')
    def test_send_to_kindle_success_tls(self, mock_smtp):
        """测试成功发送邮件（TLS连接）"""
        # 设置模拟SMTP服务器
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        result = send_to_kindle(
            kindle_email='test@kindle.com',
            sender_email='sender@qq.com',
            sender_password='test_password',
            file_path=self.test_file,
            smtp_server='smtp.qq.com',
            smtp_port=587
        )
        
        self.assertTrue(result)
        
        # 验证SMTP调用
        mock_smtp.assert_called_once_with('smtp.qq.com', 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('sender@qq.com', 'test_password')
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()
    
    def test_send_to_kindle_file_not_exists(self):
        """测试发送不存在的文件"""
        non_existent_file = os.path.join(self.test_dir, 'nonexistent.epub')
        
        result = send_to_kindle(
            kindle_email=self.test_config['kindle_email'],
            sender_email=self.test_config['sender_email'],
            sender_password=self.test_config['sender_password'],
            file_path=non_existent_file,
            smtp_server=self.test_config['smtp_server'],
            smtp_port=self.test_config['smtp_port']
        )
        
        self.assertFalse(result)
    
    def test_send_to_kindle_file_too_large(self):
        """测试发送超过50MB的文件"""
        # 创建一个大文件（模拟超过50MB）
        large_file = os.path.join(self.test_dir, 'large.epub')
        
        # 创建51MB的文件
        with open(large_file, 'wb') as f:
            f.write(b'0' * (51 * 1024 * 1024))
        
        result = send_to_kindle(
            kindle_email=self.test_config['kindle_email'],
            sender_email=self.test_config['sender_email'],
            sender_password=self.test_config['sender_password'],
            file_path=large_file,
            smtp_server=self.test_config['smtp_server'],
            smtp_port=self.test_config['smtp_port']
        )
        
        self.assertFalse(result)
    
    @patch('smtplib.SMTP_SSL')
    def test_send_to_kindle_auth_error(self, mock_smtp_ssl):
        """测试认证失败的情况"""
        # 模拟认证错误
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Authentication failed')
        mock_smtp_ssl.return_value = mock_server
        
        result = send_to_kindle(
            kindle_email=self.test_config['kindle_email'],
            sender_email=self.test_config['sender_email'],
            sender_password='wrong_password',
            file_path=self.test_file,
            smtp_server=self.test_config['smtp_server'],
            smtp_port=self.test_config['smtp_port']
        )
        
        self.assertFalse(result)
        mock_server.login.assert_called_once()
    
    @patch('smtplib.SMTP_SSL')
    def test_send_to_kindle_smtp_exception(self, mock_smtp_ssl):
        """测试SMTP异常"""
        # 模拟SMTP异常
        mock_server = MagicMock()
        mock_server.sendmail.side_effect = smtplib.SMTPException('SMTP error')
        mock_smtp_ssl.return_value = mock_server
        
        result = send_to_kindle(
            kindle_email=self.test_config['kindle_email'],
            sender_email=self.test_config['sender_email'],
            sender_password=self.test_config['sender_password'],
            file_path=self.test_file,
            smtp_server=self.test_config['smtp_server'],
            smtp_port=self.test_config['smtp_port']
        )
        
        self.assertFalse(result)
    
    @patch('smtplib.SMTP_SSL')
    def test_send_to_kindle_general_exception(self, mock_smtp_ssl):
        """测试一般异常"""
        # 模拟连接异常
        mock_smtp_ssl.side_effect = Exception('Connection error')
        
        result = send_to_kindle(
            kindle_email=self.test_config['kindle_email'],
            sender_email=self.test_config['sender_email'],
            sender_password=self.test_config['sender_password'],
            file_path=self.test_file,
            smtp_server=self.test_config['smtp_server'],
            smtp_port=self.test_config['smtp_port']
        )
        
        self.assertFalse(result)
    
    @patch('smtplib.SMTP_SSL')
    def test_send_with_custom_subject(self, mock_smtp_ssl):
        """测试自定义邮件主题"""
        mock_server = MagicMock()
        mock_smtp_ssl.return_value = mock_server
        
        result = send_to_kindle(
            kindle_email=self.test_config['kindle_email'],
            sender_email=self.test_config['sender_email'],
            sender_password=self.test_config['sender_password'],
            file_path=self.test_file,
            smtp_server=self.test_config['smtp_server'],
            smtp_port=self.test_config['smtp_port'],
            subject='Custom Subject'
        )
        
        self.assertTrue(result)
        
        # 验证邮件内容包含自定义主题
        send_args = mock_server.sendmail.call_args[0]
        email_content = send_args[2]
        self.assertIn('Subject: Custom Subject', email_content)
    
    @patch('smtplib.SMTP_SSL')
    def test_send_with_chinese_filename(self, mock_smtp_ssl):
        """测试中文文件名的处理"""
        # 创建中文名称的文件
        chinese_file = os.path.join(self.test_dir, '测试文档.epub')
        with open(chinese_file, 'wb') as f:
            f.write(b'Chinese EPUB content')
        
        mock_server = MagicMock()
        mock_smtp_ssl.return_value = mock_server
        
        result = send_to_kindle(
            kindle_email=self.test_config['kindle_email'],
            sender_email=self.test_config['sender_email'],
            sender_password=self.test_config['sender_password'],
            file_path=chinese_file,
            smtp_server=self.test_config['smtp_server'],
            smtp_port=self.test_config['smtp_port']
        )
        
        self.assertTrue(result)
        
        # 验证邮件发送
        mock_server.sendmail.assert_called_once()
        
        # 验证邮件内容包含文件名
        send_args = mock_server.sendmail.call_args[0]
        email_content = send_args[2]
        # 中文文件名应该被正确编码
        self.assertIsInstance(email_content, str)
    
    @patch('smtplib.SMTP_SSL')
    def test_send_with_convert_subject(self, mock_smtp_ssl):
        """测试使用convert主题（Kindle自动转换）"""
        mock_server = MagicMock()
        mock_smtp_ssl.return_value = mock_server
        
        result = send_to_kindle(
            kindle_email=self.test_config['kindle_email'],
            sender_email=self.test_config['sender_email'],
            sender_password=self.test_config['sender_password'],
            file_path=self.test_file,
            smtp_server=self.test_config['smtp_server'],
            smtp_port=self.test_config['smtp_port'],
            subject='convert'  # 默认主题，会触发Kindle自动转换
        )
        
        self.assertTrue(result)
        
        # 验证邮件主题
        send_args = mock_server.sendmail.call_args[0]
        email_content = send_args[2]
        self.assertIn('Subject: convert', email_content)
    
    @patch('smtplib.SMTP_SSL')
    def test_email_structure(self, mock_smtp_ssl):
        """测试邮件结构"""
        mock_server = MagicMock()
        mock_smtp_ssl.return_value = mock_server
        
        result = send_to_kindle(
            kindle_email=self.test_config['kindle_email'],
            sender_email=self.test_config['sender_email'],
            sender_password=self.test_config['sender_password'],
            file_path=self.test_file,
            smtp_server=self.test_config['smtp_server'],
            smtp_port=self.test_config['smtp_port']
        )
        
        self.assertTrue(result)
        
        # 获取发送的邮件内容
        send_args = mock_server.sendmail.call_args[0]
        email_content = send_args[2]
        
        # 验证邮件头
        self.assertIn('From: sender@163.com', email_content)
        self.assertIn('To: test@kindle.com', email_content)
        self.assertIn('Subject: convert', email_content)
        
        # 验证MIME类型
        self.assertIn('Content-Type: multipart/mixed', email_content)
        self.assertIn('Content-Disposition: attachment', email_content)
        
        # 验证附件
        self.assertIn('test.epub', email_content)


if __name__ == '__main__':
    unittest.main(verbosity=2)