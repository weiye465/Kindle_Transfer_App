# Kindle Transfer App - 私人电子书传输工具

一个简单易用的Web应用，用于将PDF等文档自动转换并发送到Kindle设备。

## 功能特点

- 📚 支持多种格式：PDF、EPUB、MOBI、TXT、DOC、DOCX
- 🔄 自动转换：PDF自动转换为EPUB格式（需要Calibre）
- 📧 邮件推送：通过Send to Kindle服务发送到设备
- 🎨 友好界面：基于TailwindCSS的现代化UI
- 🐳 Docker部署：一键部署到服务器

## 本地运行

### 环境要求

- Python 3.8+
- Calibre（可选，用于PDF转换）

### 安装步骤

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 配置设置：
   编辑 `config.json` 文件，填入你的Kindle邮箱和发送邮箱信息
3. 运行应用：

```bash
# Windows
start.bat

# Linux/Mac
chmod +x start.sh
./start.sh

# 或直接运行
python run.py
```

4. 访问 http://localhost:5000

## Docker部署

### 使用Docker Compose（推荐）

#### 开发环境

```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 生产环境

```bash
# 使用生产配置启动（端口2437）
docker-compose -f docker-compose.prod.yml up -d

# 重新构建并启动
docker-compose -f docker-compose.prod.yml up -d --build
```

### 使用Docker命令

1. 构建镜像：

```bash
docker build -t kindle-transfer .
```

2. 运行容器：

```bash
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/config.json:/app/config.json \
  -v $(pwd)/uploads:/app/uploads \
  --name kindle-app \
  kindle-transfer
```

## 宝塔面板部署

1. **上传代码**：

   - 将整个项目文件夹上传到服务器
2. **安装Docker**：

   - 在宝塔面板软件商店安装Docker管理器
3. **构建运行**：

   ```bash
   cd /www/wwwroot/kindle-transfer
   docker-compose up -d
   ```
4. **配置反向代理**：

   - 在宝塔面板添加站点
   - 设置反向代理到 `http://127.0.0.1:5000`
   - 配置SSL证书（可选）

## 配置说明

### config.json

```json
{
  "kindle_email": "你的Kindle邮箱@kindle.com",
  "smtp_email": "发送邮箱@163.com",
  "smtp_password": "邮箱授权码",
  "smtp_server": "smtp.163.com",
  "smtp_port": "465"
}
```

### 邮箱设置

1. **Kindle邮箱**：

   - 登录 amazon.com
   - 管理内容和设备 → 首选项 → 个人文档设置
   - 查看你的Kindle邮箱地址
2. **发送邮箱**：

   - 需要开启SMTP服务
   - 使用授权码而非登录密码
   - 添加到亚马逊白名单

## 注意事项

- 文件大小限制：100MB
- 邮件附件限制：50MB
- 确保Kindle连接WiFi
- 发送邮箱必须在亚马逊白名单中

## 技术栈

- 后端：Python Flask
- 前端：TailwindCSS + Font Awesome
- 部署：Docker + Gunicorn

# 更新日志

## 2024-08-13 更新 - 修复生产环境部署问题

### 🐛 问题修复

1. **解决了Gunicorn导入错误**
   - 问题原因：`app.py`文件名与`app/`文件夹名冲突，导致Python模块导入混乱
   - 解决方案：
     - 创建`main.py`作为主入口文件（从`app.py`复制）
     - 修改Dockerfile使用`main:app`作为Gunicorn启动参数
     - 创建`wsgi.py`作为WSGI入口（备用）

2. **添加了详细的日志记录**
   - 在所有文件上传、转换、发送的关键位置添加了console.log
   - 日志格式：
     - `[UPLOAD]` - 文件上传相关
     - `[SEND]` - 文件发送相关  
     - `[CONVERT]` - 文件转换相关
     - `[API-SEND]` - API接口相关
     - `[KINDLE-SEND]` - Kindle邮件发送相关

3. **优化了Docker配置**
   - 分离开发和生产环境配置
   - `docker-compose.yml` - 开发环境（端口5000）
   - `docker-compose.prod.yml` - 生产环境（端口2437）
   - 移除了代码热更新挂载（避免覆盖容器内Python环境）

### 📝 新增文件
- `main.py` - 主入口文件（从app.py复制）
- `wsgi.py` - WSGI入口文件
- `docker-compose.prod.yml` - 生产环境配置
- `docker-compose.dev.yml` - 开发环境配置（带热更新）
- `deploy.md` - 部署指南文档

### 🚀 部署方式

**开发环境：**
```bash
docker-compose up -d
```

**生产环境：**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

# 更新说明 - PDF转换开关

## 🔄 主要更新

### 1. 添加了PDF转换开关

- 在 `app.py` 中添加配置项：`CONVERT_PDF_TO_EPUB = False`
- 默认设置为 `False`，即直接发送PDF文件到Kindle，不进行转换
- Kindle设备支持原生PDF阅读，可以直接查看

### 2. 代码修改

- **app.py**: 添加转换开关逻辑，根据配置决定是否转换PDF
- **pdf_converter.py**: 添加注释说明当前默认不转换
- **index.html**: 更新使用说明，提示PDF将直接发送
- **测试文件**: 更新测试用例以适应新逻辑

## 🚀 如何切换转换模式

### 方法1：修改代码配置

编辑 `app.py` 第28行：

```python
# 启用PDF转换
app.config['CONVERT_PDF_TO_EPUB'] = True

# 禁用PDF转换（默认）
app.config['CONVERT_PDF_TO_EPUB'] = False
```

### 方法2：环境变量（可选实现）

如果需要，可以通过环境变量控制：

```python
import os
app.config['CONVERT_PDF_TO_EPUB'] = os.environ.get('CONVERT_PDF', 'false').lower() == 'true'
```

## 📝 关于Flask热更新

Flask在开发模式下支持热更新：

### 当前运行方式

```bash
python app.py
```

这会启用 `debug=True` 模式，文件修改后会自动重启。

### 前端文件更新

- **Python文件修改**：Flask会自动重启
- **HTML/模板文件修改**：需要刷新浏览器（F5）
- **静态文件（CSS/JS）修改**：可能需要强制刷新（Ctrl+F5）清除缓存

### 确保热更新生效

1. 确认Flask以debug模式运行：

   ```python
   app.run(debug=True, host='0.0.0.0', port=5000)
   ```
2. 如果修改未生效，尝试：

   - 刷新浏览器（F5）
   - 强制刷新（Ctrl+F5）清除缓存
   - 重启Flask应用
3. 使用Flask开发服务器命令：

   ```bash
   export FLASK_APP=app.py
   export FLASK_ENV=development
   flask run --reload
   ```

## 🎯 当前默认行为

- PDF文件：直接发送，不转换
- EPUB/MOBI/TXT等：直接发送
- 所有文件都保持原格式发送到Kindle

## 💡 为什么不转换PDF？

1. Kindle原生支持PDF阅读
2. 避免转换过程中的格式问题
3. 保持原始排版和图片质量
4. 更快的处理速度（无需等待转换）

如需启用PDF转换功能，只需将 `CONVERT_PDF_TO_EPUB` 设置为 `True` 即可。

## License

MIT
