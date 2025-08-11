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