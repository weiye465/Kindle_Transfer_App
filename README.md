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

1. 构建并启动：
```bash
docker-compose up -d
```

2. 停止服务：
```bash
docker-compose down
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

## License

MIT