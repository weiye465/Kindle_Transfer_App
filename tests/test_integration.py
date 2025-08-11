#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试文件 - 测试完整的工作流程
"""
import unittest
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import time

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from app.utils.pdf_converter import convert_pdf_to_epub
from app.utils.kindle_sender import send_to_kindle


class TestIntegration(unittest.TestCase):
    """集成测试 - 测试完整的文件处理流程"""
    
    def setUp(self):
        """测试前的设置"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        self.upload_dir = os.path.join(self.test_dir, 'uploads')
        os.makedirs(self.upload_dir, exist_ok=True)
        self.app.config['UPLOAD_FOLDER'] = self.upload_dir
        
        # 创建测试配置
        self.config_file = os.path.join(self.test_dir, 'config.json')
        self.test_config = {
            'kindle_email': 'integration_test@kindle.com',
            'smtp_email': 'sender@163.com',
            'smtp_password': 'test_password',
            'smtp_server': 'smtp.163.com',
            'smtp_port': '465'
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_config, f)
        
        # 补丁配置文件路径
        self.config_patcher = patch('app.CONFIG_FILE', self.config_file)
        self.config_patcher.start()
        
        # 创建测试文件
        self.create_test_files()
    
    def tearDown(self):
        """测试后的清理"""
        self.config_patcher.stop()
        
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def create_test_files(self):
        """创建测试文件"""
        # PDF文件
        self.test_pdf = os.path.join(self.test_dir, 'test_book.pdf')
        with open(self.test_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\nTest PDF content for integration testing')
        
        # EPUB文件
        self.test_epub = os.path.join(self.test_dir, 'test_book.epub')
        with open(self.test_epub, 'wb') as f:
            f.write(b'EPUB content for integration testing')
        
        # TXT文件
        self.test_txt = os.path.join(self.test_dir, 'test_book.txt')
        with open(self.test_txt, 'w', encoding='utf-8') as f:
            f.write('Plain text content for integration testing')
        
        # MOBI文件
        self.test_mobi = os.path.join(self.test_dir, 'test_book.mobi')
        with open(self.test_mobi, 'wb') as f:
            f.write(b'MOBI content for integration testing')
    
    @patch('app.send_to_kindle')
    @patch('app.convert_pdf_to_epub')
    def test_complete_workflow_pdf(self, mock_convert, mock_send):
        """测试完整工作流程 - PDF文件"""
        # 设置模拟返回值
        converted_epub = os.path.join(self.upload_dir, 'converted.epub')
        mock_convert.return_value = converted_epub
        mock_send.return_value = True
        
        # 创建转换后的文件
        with open(converted_epub, 'wb') as f:
            f.write(b'Converted EPUB content')
        
        # 1. 上传PDF文件
        with open(self.test_pdf, 'rb') as f:
            pdf_content = f.read()
        
        upload_response = self.client.post(
            '/api/upload',
            data={'file': (pdf_content, 'test_book.pdf')},
            content_type='multipart/form-data'
        )
        
        self.assertEqual(upload_response.status_code, 200)
        upload_data = json.loads(upload_response.data)
        self.assertTrue(upload_data['success'])
        
        uploaded_file = upload_data['file']['path']
        
        # 2. 转换PDF到EPUB
        convert_response = self.client.post(
            '/api/convert',
            data=json.dumps({'filepath': uploaded_file}),
            content_type='application/json'
        )
        
        self.assertEqual(convert_response.status_code, 200)
        convert_data = json.loads(convert_response.data)
        self.assertTrue(convert_data['success'])
        self.assertEqual(convert_data['format'], 'EPUB')
        
        # 3. 发送到Kindle
        send_response = self.client.post(
            '/api/send',
            data=json.dumps({'filepath': convert_data['converted_path']}),
            content_type='application/json'
        )
        
        self.assertEqual(send_response.status_code, 200)
        send_data = json.loads(send_response.data)
        self.assertTrue(send_data['success'])
        
        # 验证调用
        mock_convert.assert_called_once()
        mock_send.assert_called_once()
    
    @patch('app.send_to_kindle')
    def test_complete_workflow_epub(self, mock_send):
        """测试完整工作流程 - EPUB文件（无需转换）"""
        mock_send.return_value = True
        
        # 1. 上传EPUB文件
        with open(self.test_epub, 'rb') as f:
            epub_content = f.read()
        
        upload_response = self.client.post(
            '/api/upload',
            data={'file': (epub_content, 'test_book.epub')},
            content_type='multipart/form-data'
        )
        
        self.assertEqual(upload_response.status_code, 200)
        upload_data = json.loads(upload_response.data)
        uploaded_file = upload_data['file']['path']
        
        # 2. 转换（应该直接返回原文件）
        convert_response = self.client.post(
            '/api/convert',
            data=json.dumps({'filepath': uploaded_file}),
            content_type='application/json'
        )
        
        self.assertEqual(convert_response.status_code, 200)
        convert_data = json.loads(convert_response.data)
        self.assertEqual(convert_data['message'], '无需转换')
        self.assertEqual(convert_data['format'], 'EPUB')
        
        # 3. 发送到Kindle
        send_response = self.client.post(
            '/api/send',
            data=json.dumps({'filepath': convert_data['converted_path']}),
            content_type='application/json'
        )
        
        self.assertEqual(send_response.status_code, 200)
        send_data = json.loads(send_response.data)
        self.assertTrue(send_data['success'])
    
    @patch('app.send_to_kindle')
    @patch('app.convert_pdf_to_epub')
    def test_one_click_process(self, mock_convert, mock_send):
        """测试一键处理功能"""
        # 设置模拟返回值
        converted_epub = os.path.join(self.upload_dir, 'converted.epub')
        mock_convert.return_value = converted_epub
        mock_send.return_value = True
        
        # 创建转换后的文件
        with open(converted_epub, 'wb') as f:
            f.write(b'Converted EPUB content')
        
        # 使用一键处理API
        with open(self.test_pdf, 'rb') as f:
            pdf_content = f.read()
        
        response = self.client.post(
            '/api/process',
            data={'file': (pdf_content, 'test_book.pdf')},
            content_type='multipart/form-data'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], '处理完成！文件已发送到Kindle')
        self.assertTrue(data['details']['converted'])
        self.assertEqual(data['details']['sent_to'], 'integration_test@kindle.com')
        
        # 验证所有步骤都被执行
        mock_convert.assert_called_once()
        mock_send.assert_called_once()
    
    def test_history_tracking(self):
        """测试历史记录功能"""
        # 上传多个文件
        test_files = [
            ('test1.pdf', b'PDF content 1'),
            ('test2.epub', b'EPUB content 2'),
            ('test3.mobi', b'MOBI content 3')
        ]
        
        for filename, content in test_files:
            response = self.client.post(
                '/api/upload',
                data={'file': (content, filename)},
                content_type='multipart/form-data'
            )
            self.assertEqual(response.status_code, 200)
            # 添加小延迟以确保时间戳不同
            time.sleep(0.1)
        
        # 获取历史记录
        history_response = self.client.get('/api/history')
        self.assertEqual(history_response.status_code, 200)
        
        history_data = json.loads(history_response.data)
        self.assertIsInstance(history_data, list)
        self.assertGreaterEqual(len(history_data), 3)
        
        # 验证历史记录按时间倒序排列
        for i in range(len(history_data) - 1):
            self.assertGreaterEqual(
                history_data[i]['time'],
                history_data[i + 1]['time']
            )
    
    def test_config_persistence(self):
        """测试配置持久化"""
        # 更新配置
        new_config = {
            'kindle_email': 'new_test@kindle.com',
            'smtp_email': 'new_sender@gmail.com',
            'smtp_password': 'new_password',
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': '587'
        }
        
        response = self.client.post(
            '/api/config',
            data=json.dumps(new_config),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # 读取配置验证持久化
        get_response = self.client.get('/api/config')
        self.assertEqual(get_response.status_code, 200)
        
        saved_config = json.loads(get_response.data)
        self.assertEqual(saved_config['kindle_email'], 'new_test@kindle.com')
        self.assertEqual(saved_config['smtp_email'], 'new_sender@gmail.com')
        self.assertEqual(saved_config['smtp_server'], 'smtp.gmail.com')
        self.assertEqual(saved_config['smtp_port'], '587')
        # 密码应该被隐藏
        self.assertEqual(saved_config['smtp_password'], '********')
    
    @patch('app.send_to_kindle')
    def test_error_handling_send_failure(self, mock_send):
        """测试错误处理 - 发送失败"""
        mock_send.return_value = False
        
        # 创建测试文件
        test_file = os.path.join(self.upload_dir, 'test.epub')
        with open(test_file, 'wb') as f:
            f.write(b'Test content')
        
        response = self.client.post(
            '/api/send',
            data=json.dumps({'filepath': test_file}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], '发送失败，请检查配置')
    
    @patch('app.convert_pdf_to_epub')
    def test_error_handling_convert_failure(self, mock_convert):
        """测试错误处理 - 转换失败"""
        mock_convert.return_value = None
        
        # 创建测试PDF
        test_pdf = os.path.join(self.upload_dir, 'test.pdf')
        with open(test_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\nTest PDF')
        
        response = self.client.post(
            '/api/convert',
            data=json.dumps({'filepath': test_pdf}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], '转换失败')
    
    def test_multiple_file_formats(self):
        """测试多种文件格式支持"""
        formats = {
            'pdf': b'%PDF-1.4\nPDF content',
            'epub': b'EPUB content',
            'mobi': b'MOBI content',
            'txt': b'Plain text content',
            'doc': b'DOC content',
            'docx': b'DOCX content'
        }
        
        for ext, content in formats.items():
            filename = f'test.{ext}'
            response = self.client.post(
                '/api/upload',
                data={'file': (content, filename)},
                content_type='multipart/form-data'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertEqual(data['file']['name'], filename)
    
    def test_concurrent_uploads(self):
        """测试并发上传"""
        import threading
        
        results = []
        
        def upload_file(index):
            """上传文件的线程函数"""
            content = f'Content {index}'.encode()
            filename = f'concurrent_{index}.txt'
            
            response = self.client.post(
                '/api/upload',
                data={'file': (content, filename)},
                content_type='multipart/form-data'
            )
            
            results.append({
                'index': index,
                'status': response.status_code,
                'data': json.loads(response.data)
            })
        
        # 创建多个线程同时上传
        threads = []
        for i in range(5):
            t = threading.Thread(target=upload_file, args=(i,))
            threads.append(t)
            t.start()
        
        # 等待所有线程完成
        for t in threads:
            t.join()
        
        # 验证所有上传都成功
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertEqual(result['status'], 200)
            self.assertTrue(result['data']['success'])
    
    def test_file_size_limit(self):
        """测试文件大小限制"""
        # 创建一个超过限制的文件（>100MB）
        large_content = b'0' * (101 * 1024 * 1024)  # 101MB
        
        # 注意：Flask的MAX_CONTENT_LENGTH会在请求级别拒绝大文件
        # 这个测试主要验证配置是否正确设置
        self.assertEqual(self.app.config['MAX_CONTENT_LENGTH'], 100 * 1024 * 1024)
    
    @patch('app.send_to_kindle')
    @patch('app.convert_pdf_to_epub')
    def test_chinese_filename_support(self, mock_convert, mock_send):
        """测试中文文件名支持"""
        mock_send.return_value = True
        
        # 上传中文名称的文件
        chinese_filename = '测试文档.pdf'
        content = b'%PDF-1.4\nChinese PDF content'
        
        response = self.client.post(
            '/api/upload',
            data={'file': (content, chinese_filename)},
            content_type='multipart/form-data'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['file']['name'], chinese_filename)
    
    def test_config_validation(self):
        """测试配置验证"""
        # 测试空配置
        empty_config = {}
        
        response = self.client.post(
            '/api/config',
            data=json.dumps(empty_config),
            content_type='application/json'
        )
        
        # 应该接受空配置（会保存为空）
        self.assertEqual(response.status_code, 200)
        
        # 测试无效的JSON
        response = self.client.post(
            '/api/config',
            data='invalid json',
            content_type='application/json'
        )
        
        # Flask会自动处理无效JSON
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main(verbosity=2)