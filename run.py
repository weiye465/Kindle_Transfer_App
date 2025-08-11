#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kindle Transfer App 启动脚本
"""
import os
import sys
from app import app

if __name__ == '__main__':
    # 确保上传目录存在
    os.makedirs('uploads', exist_ok=True)
    
    # 获取端口
    port = int(os.environ.get('PORT', 5000))
    
    # 启动应用
    print("=" * 60)
    print("Kindle Transfer App - 私人电子书传输工具")
    print("=" * 60)
    print(f"访问地址: http://localhost:{port}")
    print("按 Ctrl+C 停止服务")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.environ.get('FLASK_ENV') == 'development'
    )