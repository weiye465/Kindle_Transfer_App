#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF转换器测试文件
"""
import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, call

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.pdf_converter import (
    find_calibre,
    convert_pdf_to_epub,
    convert_pdf_to_epub_docker
)


class TestPDFConverter(unittest.TestCase):
    """测试PDF转换功能"""
    
    def setUp(self):
        """测试前的设置"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        self.test_pdf = os.path.join(self.test_dir, 'test.pdf')
        
        # 创建测试PDF文件
        with open(self.test_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\nTest PDF content')
    
    def tearDown(self):
        """测试后的清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    @patch('platform.system')
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_find_calibre_windows(self, mock_exists, mock_run, mock_platform):
        """测试在Windows系统查找Calibre"""
        mock_platform.return_value = 'Windows'
        
        # 模拟where命令找到calibre
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='C:\\Program Files\\Calibre\\ebook-convert.exe'
        )
        
        result = find_calibre()
        self.assertEqual(result, 'C:\\Program Files\\Calibre\\ebook-convert.exe')
        
        # 验证调用了where命令
        mock_run.assert_called_with(
            ['where', 'ebook-convert'],
            capture_output=True,
            text=True
        )
    
    @patch('platform.system')
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_find_calibre_linux(self, mock_exists, mock_run, mock_platform):
        """测试在Linux系统查找Calibre"""
        mock_platform.return_value = 'Linux'
        
        # 模拟which命令找到calibre
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='/usr/bin/ebook-convert'
        )
        
        result = find_calibre()
        self.assertEqual(result, '/usr/bin/ebook-convert')
        
        # 验证调用了which命令
        mock_run.assert_called_with(
            ['which', 'ebook-convert'],
            capture_output=True,
            text=True
        )
    
    @patch('platform.system')
    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_find_calibre_not_found(self, mock_exists, mock_run, mock_platform):
        """测试找不到Calibre的情况"""
        mock_platform.return_value = 'Windows'
        
        # 模拟where命令失败
        mock_run.return_value = MagicMock(returncode=1)
        
        # 模拟所有路径都不存在
        mock_exists.return_value = False
        
        result = find_calibre()
        self.assertIsNone(result)
    
    @patch('platform.system')
    @patch('subprocess.run')
    def test_find_calibre_from_path(self, mock_run, mock_platform):
        """测试从PATH中查找Calibre"""
        mock_platform.return_value = 'Linux'
        
        # 创建一个实际存在的文件路径用于测试
        real_path = os.path.join(self.test_dir, 'ebook-convert')
        with open(real_path, 'w') as f:
            f.write('#!/bin/bash\n')
        
        # 模拟which命令找到calibre
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=real_path
        )
        
        with patch('pathlib.Path.exists') as mock_exists:
            # 对真实路径返回True，其他返回False
            def side_effect(path):
                return str(path) == real_path
            mock_exists.side_effect = side_effect
            
            result = find_calibre()
            self.assertEqual(result, real_path)
    
    @patch('app.utils.pdf_converter.find_calibre')
    def test_convert_pdf_to_epub_no_calibre(self, mock_find):
        """测试没有Calibre时的转换"""
        mock_find.return_value = None
        
        result = convert_pdf_to_epub(self.test_pdf)
        
        # 没有Calibre时应返回原文件路径
        self.assertEqual(result, self.test_pdf)
    
    @patch('app.utils.pdf_converter.find_calibre')
    @patch('subprocess.run')
    def test_convert_pdf_to_epub_success(self, mock_run, mock_find):
        """测试成功转换PDF到EPUB"""
        mock_find.return_value = '/usr/bin/ebook-convert'
        
        # 模拟转换成功
        mock_run.return_value = MagicMock(returncode=0)
        
        # 创建预期的EPUB文件
        expected_epub = os.path.join(self.test_dir, 'test.epub')
        
        with patch('pathlib.Path.exists') as mock_exists:
            # 模拟EPUB文件生成
            def exists_side_effect(path):
                if str(path) == expected_epub:
                    # 创建实际文件
                    with open(expected_epub, 'wb') as f:
                        f.write(b'EPUB content')
                    return True
                return os.path.exists(str(path))
            
            mock_exists.side_effect = exists_side_effect
            
            result = convert_pdf_to_epub(self.test_pdf)
            
            self.assertEqual(result, expected_epub)
            
            # 验证调用了正确的命令
            expected_cmd = [
                '/usr/bin/ebook-convert',
                self.test_pdf,
                expected_epub,
                '--enable-heuristics',
                '--margin-top', '20',
                '--margin-bottom', '20',
                '--margin-left', '20',
                '--margin-right', '20',
                '--pretty-print',
                '--insert-blank-line',
                '--language', 'zh-CN'
            ]
            
            mock_run.assert_called_once()
            actual_cmd = mock_run.call_args[0][0]
            self.assertEqual(actual_cmd, expected_cmd)
    
    @patch('app.utils.pdf_converter.find_calibre')
    @patch('subprocess.run')
    def test_convert_pdf_to_epub_failure(self, mock_run, mock_find):
        """测试转换失败的情况"""
        mock_find.return_value = '/usr/bin/ebook-convert'
        
        # 模拟转换失败
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr='Conversion error'
        )
        
        result = convert_pdf_to_epub(self.test_pdf)
        
        self.assertIsNone(result)
    
    def test_convert_pdf_to_epub_file_not_exists(self):
        """测试转换不存在的文件"""
        non_existent_file = os.path.join(self.test_dir, 'nonexistent.pdf')
        
        result = convert_pdf_to_epub(non_existent_file)
        
        self.assertIsNone(result)
    
    @patch('app.utils.pdf_converter.find_calibre')
    @patch('subprocess.run')
    def test_convert_pdf_with_output_dir(self, mock_run, mock_find):
        """测试指定输出目录的转换"""
        mock_find.return_value = '/usr/bin/ebook-convert'
        mock_run.return_value = MagicMock(returncode=0)
        
        # 创建输出目录
        output_dir = os.path.join(self.test_dir, 'output')
        expected_epub = os.path.join(output_dir, 'test.epub')
        
        with patch('pathlib.Path.exists') as mock_exists:
            def exists_side_effect(path):
                if str(path) == expected_epub:
                    # 创建输出目录和文件
                    os.makedirs(output_dir, exist_ok=True)
                    with open(expected_epub, 'wb') as f:
                        f.write(b'EPUB content')
                    return True
                return os.path.exists(str(path))
            
            mock_exists.side_effect = exists_side_effect
            
            result = convert_pdf_to_epub(self.test_pdf, output_dir)
            
            self.assertEqual(result, expected_epub)
            self.assertTrue(os.path.exists(output_dir))
    
    @patch('app.utils.pdf_converter.find_calibre')
    @patch('subprocess.run')
    def test_convert_pdf_exception_handling(self, mock_run, mock_find):
        """测试转换过程中的异常处理"""
        mock_find.return_value = '/usr/bin/ebook-convert'
        
        # 模拟subprocess.run抛出异常
        mock_run.side_effect = Exception('Unexpected error')
        
        result = convert_pdf_to_epub(self.test_pdf)
        
        self.assertIsNone(result)
    
    def test_convert_pdf_to_epub_docker(self):
        """测试Docker环境下的转换（简化版本）"""
        result = convert_pdf_to_epub_docker(self.test_pdf)
        
        # Docker版本应该直接返回原文件路径
        self.assertEqual(result, self.test_pdf)
    
    @patch('app.utils.pdf_converter.find_calibre')
    @patch('subprocess.run')
    def test_convert_with_chinese_filename(self, mock_run, mock_find):
        """测试中文文件名的处理"""
        mock_find.return_value = '/usr/bin/ebook-convert'
        mock_run.return_value = MagicMock(returncode=0)
        
        # 创建中文名称的PDF文件
        chinese_pdf = os.path.join(self.test_dir, '测试文档.pdf')
        with open(chinese_pdf, 'wb') as f:
            f.write(b'%PDF-1.4\nChinese PDF')
        
        expected_epub = os.path.join(self.test_dir, '测试文档.epub')
        
        with patch('pathlib.Path.exists') as mock_exists:
            def exists_side_effect(path):
                if str(path) == expected_epub:
                    with open(expected_epub, 'wb') as f:
                        f.write(b'EPUB content')
                    return True
                return os.path.exists(str(path))
            
            mock_exists.side_effect = exists_side_effect
            
            result = convert_pdf_to_epub(chinese_pdf)
            
            self.assertEqual(result, expected_epub)


if __name__ == '__main__':
    unittest.main(verbosity=2)