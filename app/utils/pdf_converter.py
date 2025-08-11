#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF转换工具 - 使用Calibre转换PDF到EPUB
注意：当前配置默认不转换PDF，直接发送原始PDF文件到Kindle
"""
import os
import subprocess
from pathlib import Path
import platform

def find_calibre():
    """查找Calibre安装路径"""
    possible_paths = []
    
    if platform.system() == "Windows":
        possible_paths = [
            r"C:\Program Files\Calibre2\ebook-convert.exe",
            r"C:\Program Files (x86)\Calibre2\ebook-convert.exe",
            r"C:\Program Files\Calibre\ebook-convert.exe",
            r"C:\Program Files (x86)\Calibre\ebook-convert.exe",
        ]
        
        # 检查用户本地安装
        user_home = Path.home()
        possible_paths.extend([
            user_home / "AppData/Local/Programs/Calibre2/ebook-convert.exe",
            user_home / "AppData/Local/Programs/Calibre/ebook-convert.exe",
        ])
    elif platform.system() == "Linux":
        possible_paths = [
            "/usr/bin/ebook-convert",
            "/usr/local/bin/ebook-convert",
            "/opt/calibre/ebook-convert"
        ]
    elif platform.system() == "Darwin":  # macOS
        possible_paths = [
            "/Applications/calibre.app/Contents/MacOS/ebook-convert",
            "/usr/local/bin/ebook-convert"
        ]
    
    # 检查PATH中是否有ebook-convert
    try:
        if platform.system() == "Windows":
            result = subprocess.run(["where", "ebook-convert"], 
                                  capture_output=True, text=True)
        else:
            result = subprocess.run(["which", "ebook-convert"], 
                                  capture_output=True, text=True)
        
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    # 检查可能的安装路径
    for path in possible_paths:
        if Path(path).exists():
            return str(path)
    
    return None

def convert_pdf_to_epub(pdf_path, output_dir=None):
    """
    转换PDF到EPUB格式
    
    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录（可选）
    
    Returns:
        EPUB文件路径或None
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"错误: 文件不存在 - {pdf_path}")
        return None
    
    # 查找Calibre
    calibre_path = find_calibre()
    
    if not calibre_path:
        print("警告: Calibre未安装，无法转换PDF")
        print("请安装Calibre: https://calibre-ebook.com/download")
        # 如果没有Calibre，返回原文件（让用户直接发送PDF）
        return str(pdf_path)
    
    # 设置输出路径
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        epub_path = output_dir / f"{pdf_path.stem}.epub"
    else:
        epub_path = pdf_path.with_suffix('.epub')
    
    # 构建转换命令
    cmd = [
        calibre_path,
        str(pdf_path),
        str(epub_path),
        "--enable-heuristics",  # 启用启发式处理
        "--margin-top", "20",
        "--margin-bottom", "20",
        "--margin-left", "20",
        "--margin-right", "20",
        "--pretty-print",  # 美化输出
        "--insert-blank-line",  # 段落间插入空行
        "--language", "zh-CN",  # 设置语言为中文
    ]
    
    print(f"开始转换: {pdf_path.name} -> {epub_path.name}")
    
    try:
        # 执行转换
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0 and epub_path.exists():
            print(f"转换成功: {epub_path}")
            return str(epub_path)
        else:
            print(f"转换失败: {result.stderr if result.stderr else '未知错误'}")
            return None
            
    except Exception as e:
        print(f"转换出错: {e}")
        return None

# Docker环境下的简化版本（不依赖Calibre）
def convert_pdf_to_epub_docker(pdf_path):
    """
    Docker环境下的转换（直接返回PDF，让Kindle自己处理）
    """
    # 在Docker环境中，如果没有Calibre，直接返回PDF
    # Kindle的Send to Kindle服务可以接受PDF并自动转换
    return str(pdf_path)