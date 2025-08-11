#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask应用主测试文件
"""
import unittest
import json
import os
import tempfile
import shutil
from pathlib import Path
import sys

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, load_config, save_config, allowed_file
from unittest.mock import patch, MagicMock


class TestKindleTransferApp(unittest.TestCase):
    """测试Kindle Transfer应用的主要功能"""
    
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
        
        # 创建临时配置文件
        self.config_file = os.path.join(self.test_dir, 'config.json')
        self.test_config = {
            'kindle_email': 'test@kindle.com',
            'smtp_email': 'test@163.com',
            'smtp_password': 'testpass123',
            'smtp_server': 'smtp.163.com',
            'smtp_port': '465'
        }
        
        # 保存测试配置
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_config, f)
        
        # 补丁配置文件路径
        self.config_patcher = patch('app.CONFIG_FILE', self.config_file)
        self.config_patcher.start()
    
    def tearDown(self):
        """测试后的清理"""
        self.config_patcher.stop()
        
        # 清理临时目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_index_route(self):
        """测试主页路由"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)
    
    def test_allowed_file(self):
        """测试文件扩展名检查"""
        # 允许的文件
        self.assertTrue(allowed_file('test.pdf'))
        self.assertTrue(allowed_file('book.epub'))
        self.assertTrue(allowed_file('document.mobi'))
        self.assertTrue(allowed_file('text.txt'))
        self.assertTrue(allowed_file('doc.doc'))
        self.assertTrue(allowed_file('document.docx'))
        
        # 不允许的文件
        self.assertFalse(allowed_file('test.exe'))
        self.assertFalse(allowed_file('script.js'))
        self.assertFalse(allowed_file('image.jpg'))
        self.assertFalse(allowed_file('test'))  # 无扩展名
    
    def test_config_get(self):
        """测试获取配置"""
        response = self.client.get('/api/config')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['kindle_email'], 'test@kindle.com')
        self.assertEqual(data['smtp_email'], 'test@163.com')
        # 密码应该被隐藏
        self.assertEqual(data['smtp_password'], '********')
    
    def test_config_post(self):
        """测试保存配置"""
        new_config = {
            'kindle_email': 'new@kindle.com',
            'smtp_email': 'new@163.com',
            'smtp_password': 'newpass123',
            'smtp_server': 'smtp.163.com',
            'smtp_port': '465'
        }
        
        response = self.client.post('/api/config',
                                   data=json.dumps(new_config),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], '配置已保存')
        
        # 验证配置已保存
        saved_config = load_config()
        self.assertEqual(saved_config['kindle_email'], 'new@kindle.com')
        self.assertEqual(saved_config['smtp_password'], 'newpass123')
    
    def test_config_password_preserve(self):
        """测试保存配置时保留原密码"""
        update_config = {
            'kindle_email': 'updated@kindle.com',
            'smtp_email': 'test@163.com',
            'smtp_password': '********',  # 未更改的密码
            'smtp_server': 'smtp.163.com',
            'smtp_port': '465'
        }
        
        response = self.client.post('/api/config',
                                   data=json.dumps(update_config),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # 验证密码未被更改
        saved_config = load_config()
        self.assertEqual(saved_config['smtp_password'], 'testpass123')
    
    def test_upload_no_file(self):
        """测试上传文件 - 没有文件"""
        response = self.client.post('/api/upload')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], '没有文件')
    
    def test_upload_empty_filename(self):
        """测试上传文件 - 空文件名"""
        data = {'file': (None, '')}
        response = self.client.post('/api/upload',
                                   data=data,
                                   content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        
        result = json.loads(response.data)
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], '没有选择文件')
    
    def test_upload_invalid_extension(self):
        """测试上传文件 - 无效扩展名"""
        data = {'file': (b'test content', 'test.exe')}
        response = self.client.post('/api/upload',
                                   data=data,
                                   content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        
        result = json.loads(response.data)
        self.assertFalse(result['success'])
        self.assertEqual(result['message'], '不支持的文件格式')
    
    def test_upload_valid_file(self):
        """测试上传文件 - 有效文件"""
        # 创建测试文件内容
        test_content = b'This is a test PDF content'
        data = {'file': (test_content, 'test.pdf')}
        
        response = self.client.post('/api/upload',
                                   data=data,
                                   content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '文件上传成功')
        self.assertEqual(result['file']['name'], 'test.pdf')
        
        # 验证文件已保存
        saved_files = os.listdir(self.upload_dir)
        self.assertEqual(len(saved_files), 1)
        self.assertIn('test.pdf', saved_files[0])
    
    @patch('app.convert_pdf_to_epub')
    def test_convert_pdf(self, mock_convert):
        """测试PDF转换"""
        # 创建测试PDF文件
        test_pdf = os.path.join(self.upload_dir, 'test.pdf')
        test_epub = os.path.join(self.upload_dir, 'test.epub')
        
        with open(test_pdf, 'wb') as f:
            f.write(b'PDF content')
        
        # 模拟转换成功
        mock_convert.return_value = test_epub
        
        # 创建EPUB文件以模拟转换结果
        with open(test_epub, 'wb') as f:
            f.write(b'EPUB content')
        
        response = self.client.post('/api/convert',
                                   data=json.dumps({'filepath': test_pdf}),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], '转换成功')
        self.assertEqual(data['converted_path'], test_epub)
        self.assertEqual(data['format'], 'EPUB')
    
    def test_convert_non_pdf(self):
        """测试非PDF文件转换"""
        # 创建测试TXT文件
        test_txt = os.path.join(self.upload_dir, 'test.txt')
        with open(test_txt, 'w', encoding='utf-8') as f:
            f.write('Test content')
        
        response = self.client.post('/api/convert',
                                   data=json.dumps({'filepath': test_txt}),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], '无需转换')
        self.assertEqual(data['converted_path'], test_txt)
        self.assertEqual(data['format'], 'TXT')
    
    def test_convert_file_not_exists(self):
        """测试转换不存在的文件"""
        response = self.client.post('/api/convert',
                                   data=json.dumps({'filepath': '/nonexistent/file.pdf'}),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], '文件不存在')
    
    @patch('app.send_to_kindle')
    def test_send_to_kindle_api(self, mock_send):
        """测试发送到Kindle"""
        # 创建测试文件
        test_file = os.path.join(self.upload_dir, 'test.epub')
        with open(test_file, 'wb') as f:
            f.write(b'EPUB content')
        
        # 模拟发送成功
        mock_send.return_value = True
        
        response = self.client.post('/api/send',
                                   data=json.dumps({'filepath': test_file}),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], '发送成功！请在Kindle上查收')
        
        # 验证调用参数
        mock_send.assert_called_once_with(
            kindle_email='test@kindle.com',
            sender_email='test@163.com',
            sender_password='testpass123',
            file_path=test_file,
            smtp_server='smtp.163.com',
            smtp_port=465
        )
    
    def test_send_no_kindle_email(self):
        """测试发送到Kindle - 没有配置Kindle邮箱"""
        # 清空Kindle邮箱配置
        config = load_config()
        config['kindle_email'] = ''
        save_config(config)
        
        test_file = os.path.join(self.upload_dir, 'test.epub')
        with open(test_file, 'wb') as f:
            f.write(b'EPUB content')
        
        response = self.client.post('/api/send',
                                   data=json.dumps({'filepath': test_file}),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], '请先配置Kindle邮箱')
    
    def test_send_no_smtp_config(self):
        """测试发送到Kindle - 没有配置发送邮箱"""
        # 清空SMTP配置
        config = load_config()
        config['smtp_email'] = ''
        save_config(config)
        
        test_file = os.path.join(self.upload_dir, 'test.epub')
        with open(test_file, 'wb') as f:
            f.write(b'EPUB content')
        
        response = self.client.post('/api/send',
                                   data=json.dumps({'filepath': test_file}),
                                   content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], '请先配置发送邮箱')
    
    @patch('app.send_to_kindle')
    @patch('app.convert_pdf_to_epub')
    def test_process_file(self, mock_convert, mock_send):
        """测试一键处理功能"""
        # 模拟转换和发送成功
        test_epub = os.path.join(self.upload_dir, 'test.epub')
        mock_convert.return_value = test_epub
        mock_send.return_value = True
        
        # 创建EPUB文件
        with open(test_epub, 'wb') as f:
            f.write(b'EPUB content')
        
        # 上传PDF文件
        test_content = b'This is a test PDF content'
        data = {'file': (test_content, 'test.pdf')}
        
        response = self.client.post('/api/process',
                                   data=data,
                                   content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], '处理完成！文件已发送到Kindle')
        self.assertEqual(result['details']['original_file'], 'test.pdf')
        self.assertTrue(result['details']['converted'])
        self.assertEqual(result['details']['sent_to'], 'test@kindle.com')
    
    def test_get_history(self):
        """测试获取历史记录"""
        # 创建几个测试文件
        test_files = ['book1.pdf', 'book2.epub', 'book3.mobi']
        for filename in test_files:
            filepath = os.path.join(self.upload_dir, filename)
            with open(filepath, 'w') as f:
                f.write('test content')
        
        response = self.client.get('/api/history')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)
        
        # 验证文件信息
        filenames = [item['name'] for item in data]
        for filename in test_files:
            self.assertIn(filename, filenames)
        
        # 验证每个文件都有必要的字段
        for item in data:
            self.assertIn('name', item)
            self.assertIn('size', item)
            self.assertIn('time', item)


if __name__ == '__main__':
    unittest.main(verbosity=2)