#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理辅助工具
"""
import os
import re
from datetime import datetime


def safe_filename(filename):
    """
    生成安全的文件名，保留中文和基本字符
    
    Args:
        filename: 原始文件名
    
    Returns:
        安全的文件名
    """
    # 分离文件名和扩展名
    name, ext = os.path.splitext(filename)
    
    # 保留中文、英文、数字、下划线、连字符、点号
    # 移除或替换其他特殊字符
    safe_name = re.sub(r'[^\w\u4e00-\u9fa5\s\-\.]', '_', name)
    
    # 移除多余的空格和特殊字符
    safe_name = safe_name.strip()
    
    # 如果文件名为空，使用默认名称
    if not safe_name:
        safe_name = 'document'
    
    # 限制文件名长度（保留扩展名的空间）
    max_length = 200  # Windows文件名限制
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length]
    
    return safe_name + ext


def generate_unique_filename(original_filename, upload_dir):
    """
    生成唯一的文件名，避免冲突
    
    Args:
        original_filename: 原始文件名
        upload_dir: 上传目录
    
    Returns:
        唯一的文件名
    """
    # 获取安全的文件名
    safe_name = safe_filename(original_filename)
    
    # 添加时间戳前缀确保唯一性
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_name = f"{timestamp}_{safe_name}"
    
    # 检查文件是否存在，如果存在则添加序号
    base_name, ext = os.path.splitext(unique_name)
    counter = 1
    final_name = unique_name
    
    while os.path.exists(os.path.join(upload_dir, final_name)):
        final_name = f"{base_name}_{counter}{ext}"
        counter += 1
    
    return final_name


def get_file_info(filepath):
    """
    获取文件信息
    
    Args:
        filepath: 文件路径
    
    Returns:
        文件信息字典
    """
    if not os.path.exists(filepath):
        return None
    
    stat = os.stat(filepath)
    return {
        'path': filepath,
        'name': os.path.basename(filepath),
        'size': stat.st_size,
        'size_mb': round(stat.st_size / 1024 / 1024, 2),
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'extension': os.path.splitext(filepath)[1].lower()
    }


def extract_original_filename(saved_filename):
    """
    从保存的文件名中提取原始文件名（去除时间戳前缀）
    
    Args:
        saved_filename: 保存的文件名（包含时间戳）
    
    Returns:
        原始文件名
    """
    # 匹配时间戳格式：YYYYMMDD_HHMMSS_
    pattern = r'^\d{8}_\d{6}_(.+)$'
    match = re.match(pattern, saved_filename)
    
    if match:
        return match.group(1)
    
    # 如果没有匹配的时间戳格式，返回原文件名
    return saved_filename