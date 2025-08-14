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
from dotenv import load_dotenv
import logging
import time
import sys

# 加载.env文件
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('kindle_transfer.log')
    ]
)
logger = logging.getLogger(__name__)

# 导入工具模块
from app.utils.pdf_converter import convert_pdf_to_epub
from app.utils.kindle_sender import send_to_kindle
from app.utils.file_helper import safe_filename, generate_unique_filename

app = Flask(__name__, 
            template_folder='app/templates',
            static_folder='app/static')

# 添加请求日志
@app.before_request
def log_request_info():
    logger.info(f'Headers: {dict(request.headers)}')
    logger.info(f'Body Size: {request.content_length}')
    logger.info(f'Method: {request.method}, Path: {request.path}')

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
    """加载配置，优先从环境变量读取，其次从config.json"""
    config = {}
    
    # 先尝试从文件加载
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    # 环境变量覆盖文件配置
    env_config = {
        'kindle_email': os.getenv('KINDLE_EMAIL'),
        'smtp_email': os.getenv('SMTP_EMAIL'),
        'smtp_password': os.getenv('SMTP_PASSWORD'),
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.163.com'),
        'smtp_port': os.getenv('SMTP_PORT', '465')
    }
    
    # 只覆盖非空的环境变量
    for key, value in env_config.items():
        if value:
            config[key] = value
    
    return config

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
    logger.info("[UPLOAD] 开始处理文件上传请求")
    
    if 'file' not in request.files:
        logger.error("[UPLOAD] 请求中没有找到文件")
        return jsonify({'success': False, 'message': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        logger.error("[UPLOAD] 文件名为空")
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    logger.info(f"[UPLOAD] 接收到文件: {file.filename}")
    
    if not allowed_file(file.filename):
        logger.error(f"[UPLOAD] 不支持的文件格式: {file.filename}")
        return jsonify({'success': False, 'message': '不支持的文件格式'}), 400
    
    # 保存文件，保留原始文件名
    original_filename = file.filename
    # 生成唯一且安全的文件名（保留中文）
    filename = generate_unique_filename(original_filename, app.config['UPLOAD_FOLDER'])
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    logger.info(f"[UPLOAD] 准备保存文件: {original_filename} -> {filepath}")
    
    try:
        file.save(filepath)
        logger.info(f"[UPLOAD] 文件保存成功: {filepath}")
    except Exception as e:
        logger.error(f"[UPLOAD] 文件保存失败: {e}")
        return jsonify({'success': False, 'message': f'文件保存失败: {str(e)}'}), 500
    
    # 获取文件信息
    file_size = os.path.getsize(filepath) / 1024 / 1024  # MB
    logger.info(f"[UPLOAD] 文件大小: {file_size:.2f}MB")
    
    response = {
        'success': True,
        'message': '文件上传成功',
        'file': {
            'name': original_filename,  # 返回原始文件名
            'path': filepath,
            'size': round(file_size, 2),
            'saved_as': filename  # 实际保存的文件名
        }
    }
    
    logger.info(f"[UPLOAD] 上传完成，返回响应: {response}")
    return jsonify(response)

@app.route('/api/convert', methods=['POST'])
def convert_file():
    """转换文件格式"""
    logger.info("[CONVERT] 开始处理转换请求")
    
    data = request.json
    filepath = data.get('filepath')
    logger.info(f"[CONVERT] 要转换的文件: {filepath}")
    
    if not filepath or not os.path.exists(filepath):
        logger.error(f"[CONVERT] 文件不存在: {filepath}")
        return jsonify({'success': False, 'message': '文件不存在'}), 400
    
    try:
        # 如果是PDF，根据配置决定是否转换
        if filepath.lower().endswith('.pdf'):
            if app.config.get('CONVERT_PDF_TO_EPUB', False):
                # 转换为EPUB
                logger.info("[CONVERT] 开始转换PDF到EPUB")
                epub_path = convert_pdf_to_epub(filepath)
                if epub_path and os.path.exists(epub_path):
                    logger.info(f"[CONVERT] 转换成功: {epub_path}")
                    return jsonify({
                        'success': True,
                        'message': '转换成功',
                        'converted_path': epub_path,
                        'format': 'EPUB'
                    })
                else:
                    logger.error("[CONVERT] 转换失败")
                    return jsonify({'success': False, 'message': '转换失败'}), 500
            else:
                # 直接返回PDF，不转换
                logger.info("[CONVERT] PDF无需转换，直接发送")
                return jsonify({
                    'success': True,
                    'message': '无需转换，直接发送PDF',
                    'converted_path': filepath,
                    'format': 'PDF'
                })
        else:
            # 其他格式直接返回
            file_format = filepath.split('.')[-1].upper()
            logger.info(f"[CONVERT] {file_format}格式无需转换")
            return jsonify({
                'success': True,
                'message': '无需转换',
                'converted_path': filepath,
                'format': file_format
            })
    
    except Exception as e:
        logger.error(f"[CONVERT] 转换出错: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/send', methods=['POST'])
def send_to_kindle_api():
    """发送到Kindle"""
    logger.info("[SEND] 开始处理发送请求")
    
    data = request.json
    filepath = data.get('filepath')
    logger.info(f"[SEND] 要发送的文件: {filepath}")
    
    if not filepath or not os.path.exists(filepath):
        logger.error(f"[SEND] 文件不存在: {filepath}")
        return jsonify({'success': False, 'message': '文件不存在'}), 400
    
    # 加载配置
    config = load_config()
    
    if not config.get('kindle_email'):
        logger.error("[SEND] 未配置Kindle邮箱")
        return jsonify({'success': False, 'message': '请先配置Kindle邮箱'}), 400
    
    if not config.get('smtp_email') or not config.get('smtp_password'):
        logger.error("[SEND] 未配置发送邮箱")
        return jsonify({'success': False, 'message': '请先配置发送邮箱'}), 400
    
    try:
        # 发送文件
        logger.info(f"[SEND] 发送文件到: {config['kindle_email']}")
        logger.info(f"[SEND] 使用SMTP: {config.get('smtp_server', 'smtp.163.com')}:{config.get('smtp_port', 465)}")
        
        success = send_to_kindle(
            kindle_email=config['kindle_email'],
            sender_email=config['smtp_email'],
            sender_password=config['smtp_password'],
            file_path=filepath,
            smtp_server=config.get('smtp_server', 'smtp.163.com'),
            smtp_port=int(config.get('smtp_port', 465))
        )
        
        if success:
            logger.info("[SEND] 发送成功！")
            return jsonify({
                'success': True,
                'message': '发送成功！请在Kindle上查收'
            })
        else:
            logger.error("[SEND] 发送失败")
            return jsonify({'success': False, 'message': '发送失败，请检查配置'}), 500
    
    except Exception as e:
        logger.error(f"[SEND] 发送出错: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/send-to-kindle', methods=['POST'])
def api_send_to_kindle():
    """
    纯API接口：接收文件并发送到Kindle
    
    请求参数：
    - file: 要发送的文件（必需）
    - convert_pdf: 是否转换PDF为EPUB（可选，默认false）
    - kindle_email: 目标Kindle邮箱（可选，默认使用环境变量）
    
    返回：
    - 成功：{'success': true, 'message': '...', 'details': {...}}
    - 失败：{'success': false, 'error': '...'}
    """
    logger.info("[API-SEND] ========== 开始处理API发送请求 ==========")
    logger.info(f"[API-SEND] 请求headers: {dict(request.headers)}")
    logger.info(f"[API-SEND] 请求form数据: {dict(request.form)}")
    
    # 1. 验证文件
    if 'file' not in request.files:
        logger.error("[API-SEND] 请求中没有找到文件")
        return jsonify({
            'success': False,
            'error': '没有上传文件'
        }), 400
    
    file = request.files['file']
    logger.info(f"[API-SEND] 收到文件: {file.filename}")
    
    if file.filename == '':
        logger.error("[API-SEND] 文件名为空")
        return jsonify({
            'success': False,
            'error': '文件名为空'
        }), 400
    
    if not allowed_file(file.filename):
        logger.error(f"[API-SEND] 不支持的文件格式: {file.filename}")
        return jsonify({
            'success': False,
            'error': f'不支持的文件格式。支持的格式：{", ".join(app.config["ALLOWED_EXTENSIONS"])}'
        }), 400
    
    try:
        # 2. 获取配置
        config = load_config()
        
        # 允许通过请求参数覆盖某些配置
        if request.form.get('kindle_email'):
            config['kindle_email'] = request.form.get('kindle_email')
        
        convert_pdf = request.form.get('convert_pdf', 'false').lower() == 'true'
        
        # 3. 保存文件
        original_filename = file.filename
        filename = generate_unique_filename(original_filename, app.config['UPLOAD_FOLDER'])
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        logger.info(f"[API-SEND] 保存文件: {original_filename} -> {filepath}")
        file.save(filepath)
        logger.info(f"[API-SEND] 文件保存成功，大小: {os.path.getsize(filepath) / (1024*1024):.2f}MB")
        
        # 4. 处理文件（可能需要转换）
        final_path = filepath
        converted = False
        
        if filepath.lower().endswith('.pdf') and convert_pdf:
            logger.info("[API-SEND] 开始转换PDF到EPUB")
            try:
                epub_path = convert_pdf_to_epub(filepath)
                if epub_path and os.path.exists(epub_path):
                    final_path = epub_path
                    converted = True
                    logger.info(f"[API-SEND] PDF转换成功: {epub_path}")
            except Exception as e:
                logger.error(f"[API-SEND] PDF转换失败: {e}")
        
        # 5. 发送到Kindle
        logger.info(f"[API-SEND] 准备发送文件到Kindle: {config['kindle_email']}")
        logger.info(f"[API-SEND] 使用SMTP服务器: {config.get('smtp_server', 'smtp.163.com')}:{config.get('smtp_port', 465)}")
        logger.info(f"[API-SEND] 发送文件: {final_path}")
        
        success = send_to_kindle(
            kindle_email=config['kindle_email'],
            sender_email=config['smtp_email'],
            sender_password=config['smtp_password'],
            file_path=final_path,
            smtp_server=config.get('smtp_server', 'smtp.163.com'),
            smtp_port=int(config.get('smtp_port', 465))
        )
        
        if success:
            response = {
                'success': True,
                'message': '文件已成功发送到Kindle',
                'details': {
                    'original_filename': original_filename,
                    'file_size_mb': round(os.path.getsize(final_path) / 1024 / 1024, 2),
                    'converted_to_epub': converted,
                    'sent_to': config['kindle_email'],
                    'format': 'EPUB' if converted else filepath.split('.')[-1].upper()
                }
            }
            logger.info(f"[API-SEND] 发送成功！返回响应: {response}")
            logger.info("[API-SEND] ========== API发送请求处理完成 ==========")
            return jsonify(response)
        else:
            logger.error("[API-SEND] 发送失败！")
            logger.info("[API-SEND] ========== API发送请求处理失败 ==========")
            return jsonify({
                'success': False,
                'error': '发送失败，请检查SMTP配置'
            }), 500
    
    except Exception as e:
        logger.error(f"[API-SEND] 处理出错: {str(e)}", exc_info=True)
        logger.info("[API-SEND] ========== API发送请求处理异常 ==========")
        return jsonify({
            'success': False,
            'error': f'处理失败: {str(e)}'
        }), 500

@app.route('/api/process', methods=['POST'])
def process_file():
    """一键处理：上传、转换、发送"""
    start_time = time.time()
    logger.info(f"========== 开始处理文件上传 ==========")
    
    if 'file' not in request.files:
        logger.error("请求中没有文件")
        return jsonify({'success': False, 'message': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        logger.error("文件名为空")
        return jsonify({'success': False, 'message': '没有选择文件'}), 400
    
    if not allowed_file(file.filename):
        logger.error(f"不支持的文件格式: {file.filename}")
        return jsonify({'success': False, 'message': '不支持的文件格式'}), 400
    
    try:
        # 1. 保存文件，保留原始文件名
        original_filename = file.filename
        file_size_mb = len(file.read()) / (1024 * 1024)
        file.seek(0)  # 重置文件指针
        logger.info(f"接收文件: {original_filename}, 大小: {file_size_mb:.2f}MB")
        
        save_start = time.time()
        filename = generate_unique_filename(original_filename, app.config['UPLOAD_FOLDER'])
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 分块保存大文件
        logger.info(f"开始保存文件到: {filepath}")
        chunk_size = 4096  # 4KB chunks
        with open(filepath, 'wb') as f:
            while True:
                chunk = file.stream.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
        
        save_time = time.time() - save_start
        logger.info(f"文件保存完成，耗时: {save_time:.2f}秒, 速度: {file_size_mb/save_time:.2f}MB/s")
        
        # 2. 转换格式（如果需要）
        final_path = filepath
        if filepath.lower().endswith('.pdf') and app.config.get('CONVERT_PDF_TO_EPUB', False):
            convert_start = time.time()
            logger.info("开始转换PDF到EPUB...")
            epub_path = convert_pdf_to_epub(filepath)
            if epub_path and os.path.exists(epub_path):
                final_path = epub_path
                convert_time = time.time() - convert_start
                logger.info(f"PDF转换完成，耗时: {convert_time:.2f}秒")
            else:
                logger.error("PDF转换失败")
                return jsonify({'success': False, 'message': '文件转换失败'}), 500
        
        # 3. 发送到Kindle
        config = load_config()
        
        if not config.get('kindle_email'):
            logger.error("未配置Kindle邮箱")
            return jsonify({'success': False, 'message': '请先配置Kindle邮箱'}), 400
        
        if not config.get('smtp_email') or not config.get('smtp_password'):
            logger.error("未配置SMTP")
            return jsonify({'success': False, 'message': '请先配置发送邮箱'}), 400
        
        send_start = time.time()
        logger.info(f"开始发送邮件到: {config['kindle_email']}")
        logger.info(f"文件大小: {os.path.getsize(final_path) / (1024*1024):.2f}MB")
        
        success = send_to_kindle(
            kindle_email=config['kindle_email'],
            sender_email=config['smtp_email'],
            sender_password=config['smtp_password'],
            file_path=final_path,
            smtp_server=config.get('smtp_server', 'smtp.163.com'),
            smtp_port=int(config.get('smtp_port', 465))
        )
        
        send_time = time.time() - send_start
        total_time = time.time() - start_time
        
        if success:
            logger.info(f"发送成功！邮件发送耗时: {send_time:.2f}秒")
            logger.info(f"总处理时间: {total_time:.2f}秒")
            logger.info(f"========== 处理完成 ==========")
            
            return jsonify({
                'success': True,
                'message': '处理完成！文件已发送到Kindle',
                'details': {
                    'original_file': original_filename,
                    'converted': filepath != final_path,
                    'sent_to': config['kindle_email'],
                    'format': 'EPUB' if filepath != final_path else filepath.split('.')[-1].upper(),
                    'processing_time': f"{total_time:.2f}秒"
                }
            })
        else:
            logger.error(f"发送失败，耗时: {send_time:.2f}秒")
            return jsonify({'success': False, 'message': '发送失败，请检查配置'}), 500
    
    except Exception as e:
        logger.error(f"处理出错: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/docs')
def api_docs():
    """API文档"""
    return jsonify({
        'name': 'Kindle Transfer API',
        'version': '2.0',
        'description': '既包含Web界面，也提供API接口',
        'web_interface': 'http://localhost:5000',
        'api_endpoints': [
            {
                'path': '/api/send-to-kindle',
                'method': 'POST',
                'description': '上传文件并发送到Kindle（纯API接口）',
                'parameters': {
                    'file': '要发送的文件 (必需)',
                    'convert_pdf': '是否转换PDF为EPUB，true/false (可选)',
                    'kindle_email': '目标Kindle邮箱 (可选，默认使用环境变量)'
                },
                'example': 'curl -X POST -F "file=@book.pdf" http://localhost:5000/api/send-to-kindle'
            },
            {
                'path': '/api/process',
                'method': 'POST',
                'description': 'Web界面使用的处理接口'
            },
            {
                'path': '/api/config',
                'method': 'GET/POST',
                'description': '配置管理'
            },
            {
                'path': '/api/history',
                'method': 'GET',
                'description': '获取传输历史'
            }
        ]
    })

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