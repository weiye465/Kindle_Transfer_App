#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kindle Transfer App - Flask主应用
私人版Kindle电子书传输应用
"""
from flask import Flask, render_template, request, jsonify, send_file
import os
import json
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
import tempfile
import shutil

# 导入工具模块
from app.utils.pdf_converter import convert_pdf_to_epub
from app.utils.kindle_sender import send_to_kindle
from app.utils.file_helper import safe_filename, generate_unique_filename

app = Flask(__name__, 
            template_folder='app/templates',
            static_folder='app/static')

# 配置
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'epub', 'mobi', 'txt', 'doc', 'docx'}
app.config['CONVERT_PDF_TO_EPUB'] = False  # 是否转换PDF到EPUB，False则直接发送PDF

# 配置文件路径
CONFIG_FILE = 'config.json'

# 确保上传文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def load_config():
    """加载配置"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    """主页"""
    config = load_config()
    return render_template('index.html', config=config)

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """处理配置"""
    if request.method == 'GET':
        config = load_config()
        # 隐藏密码
        if 'smtp_password' in config:
            config['smtp_password'] = '*' * 8
        return jsonify(config)
    
    elif request.method == 'POST':
        data = request.json
        current_config = load_config()
        
        # 如果密码没变，保留原密码
        if data.get('smtp_password') == '*' * 8:
            data['smtp_password'] = current_config.get('smtp_password', '')
        
        save_config(data)
        return jsonify({'success': True, 'message': '配置已保存'})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传文件"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': '不支持的文件格式'}), 400
    
    # 保存文件，保留原始文件名
    original_filename = file.filename
    # 生成唯一且安全的文件名（保留中文）
    filename = generate_unique_filename(original_filename, app.config['UPLOAD_FOLDER'])
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # 获取文件信息
    file_size = os.path.getsize(filepath) / 1024 / 1024  # MB
    
    return jsonify({
        'success': True,
        'message': '文件上传成功',
        'file': {
            'name': original_filename,  # 返回原始文件名
            'path': filepath,
            'size': round(file_size, 2),
            'saved_as': filename  # 实际保存的文件名
        }
    })

@app.route('/api/convert', methods=['POST'])
def convert_file():
    """转换文件格式"""
    data = request.json
    filepath = data.get('filepath')
    
    if not filepath or not os.path.exists(filepath):
        return jsonify({'success': False, 'message': '文件不存在'}), 400
    
    try:
        # 如果是PDF，根据配置决定是否转换
        if filepath.lower().endswith('.pdf'):
            if app.config.get('CONVERT_PDF_TO_EPUB', False):
                # 转换为EPUB
                epub_path = convert_pdf_to_epub(filepath)
                if epub_path and os.path.exists(epub_path):
                    return jsonify({
                        'success': True,
                        'message': '转换成功',
                        'converted_path': epub_path,
                        'format': 'EPUB'
                    })
                else:
                    return jsonify({'success': False, 'message': '转换失败'}), 500
            else:
                # 直接返回PDF，不转换
                return jsonify({
                    'success': True,
                    'message': '无需转换，直接发送PDF',
                    'converted_path': filepath,
                    'format': 'PDF'
                })
        else:
            # 其他格式直接返回
            return jsonify({
                'success': True,
                'message': '无需转换',
                'converted_path': filepath,
                'format': filepath.split('.')[-1].upper()
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/send', methods=['POST'])
def send_to_kindle_api():
    """发送到Kindle"""
    data = request.json
    filepath = data.get('filepath')
    
    if not filepath or not os.path.exists(filepath):
        return jsonify({'success': False, 'message': '文件不存在'}), 400
    
    # 加载配置
    config = load_config()
    
    if not config.get('kindle_email'):
        return jsonify({'success': False, 'message': '请先配置Kindle邮箱'}), 400
    
    if not config.get('smtp_email') or not config.get('smtp_password'):
        return jsonify({'success': False, 'message': '请先配置发送邮箱'}), 400
    
    try:
        # 发送文件
        success = send_to_kindle(
            kindle_email=config['kindle_email'],
            sender_email=config['smtp_email'],
            sender_password=config['smtp_password'],
            file_path=filepath,
            smtp_server=config.get('smtp_server', 'smtp.163.com'),
            smtp_port=int(config.get('smtp_port', 465))
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': '发送成功！请在Kindle上查收'
            })
        else:
            return jsonify({'success': False, 'message': '发送失败，请检查配置'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/process', methods=['POST'])
def process_file():
    """一键处理：上传、转换、发送"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': '不支持的文件格式'}), 400
    
    try:
        # 1. 保存文件，保留原始文件名
        original_filename = file.filename
        filename = generate_unique_filename(original_filename, app.config['UPLOAD_FOLDER'])
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 2. 转换格式（如果需要）
        final_path = filepath
        if filepath.lower().endswith('.pdf') and app.config.get('CONVERT_PDF_TO_EPUB', False):
            epub_path = convert_pdf_to_epub(filepath)
            if epub_path and os.path.exists(epub_path):
                final_path = epub_path
            else:
                return jsonify({'success': False, 'message': '文件转换失败'}), 500
        
        # 3. 发送到Kindle
        config = load_config()
        
        if not config.get('kindle_email'):
            return jsonify({'success': False, 'message': '请先配置Kindle邮箱'}), 400
        
        if not config.get('smtp_email') or not config.get('smtp_password'):
            return jsonify({'success': False, 'message': '请先配置发送邮箱'}), 400
        
        success = send_to_kindle(
            kindle_email=config['kindle_email'],
            sender_email=config['smtp_email'],
            sender_password=config['smtp_password'],
            file_path=final_path,
            smtp_server=config.get('smtp_server', 'smtp.163.com'),
            smtp_port=int(config.get('smtp_port', 465))
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': '处理完成！文件已发送到Kindle',
                'details': {
                    'original_file': original_filename,  # 使用原始文件名
                    'converted': filepath != final_path,
                    'sent_to': config['kindle_email'],
                    'format': 'EPUB' if filepath != final_path else filepath.split('.')[-1].upper()
                }
            })
        else:
            return jsonify({'success': False, 'message': '发送失败，请检查配置'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/history')
def get_history():
    """获取传输历史"""
    # 简单实现：列出uploads文件夹中的文件
    files = []
    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    
    if upload_dir.exists():
        for file_path in upload_dir.glob('*'):
            if file_path.is_file():
                files.append({
                    'name': file_path.name,
                    'size': round(file_path.stat().st_size / 1024 / 1024, 2),
                    'time': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
    
    # 按时间倒序
    files.sort(key=lambda x: x['time'], reverse=True)
    return jsonify(files[:20])  # 只返回最近20个

if __name__ == '__main__':
    print("Kindle Transfer App - 启动中...")
    print("访问 http://localhost:5000 使用应用")
    app.run(debug=True, host='0.0.0.0', port=5000)