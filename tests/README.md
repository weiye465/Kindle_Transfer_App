# Kindle Transfer App 测试文档

## 📁 测试文件结构

```
tests/
├── test_app.py              # Flask应用主测试
├── test_pdf_converter.py    # PDF转换功能测试
├── test_kindle_sender.py    # 邮件发送功能测试
├── test_integration.py      # 集成测试
├── run_tests.py            # 测试运行脚本
├── test_config.json        # 测试配置文件
├── sample_data/            # 测试数据目录
│   └── sample.txt         # 示例文本文件
└── reports/               # 测试报告目录（自动生成）
    ├── test_report.json   # JSON格式报告
    └── test_report.html   # HTML格式报告
```

## 🚀 运行测试

### 运行所有测试
```bash
# 在项目根目录运行
python tests/run_tests.py

# 或者使用unittest
python -m unittest discover tests
```

### 运行特定测试模块
```bash
# 只运行主应用测试
python tests/run_tests.py -t test_app

# 只运行PDF转换测试
python tests/run_tests.py -t test_pdf_converter

# 只运行邮件发送测试
python tests/run_tests.py -t test_kindle_sender

# 只运行集成测试
python tests/run_tests.py -t test_integration
```

### 运行特定测试类或方法
```bash
# 运行特定的测试类
python tests/run_tests.py -t test_app.TestKindleTransferApp

# 运行特定的测试方法
python tests/run_tests.py -t test_app.TestKindleTransferApp.test_upload_valid_file
```

### 命令行参数
```bash
# 查看所有可用的测试模块
python tests/run_tests.py --list

# 设置输出详细程度
python tests/run_tests.py -v 0  # 静默模式
python tests/run_tests.py -v 1  # 正常模式
python tests/run_tests.py -v 2  # 详细模式（默认）

# 不生成测试报告
python tests/run_tests.py --no-report

# 指定测试文件模式
python tests/run_tests.py -p "test_*.py"
```

## 📊 测试覆盖范围

### 1. **主应用测试** (test_app.py)
- ✅ 路由测试（主页、API端点）
- ✅ 文件上传验证
- ✅ 文件格式检查
- ✅ 配置管理（读取、保存、密码保护）
- ✅ 文件转换API
- ✅ 发送到Kindle API
- ✅ 历史记录功能
- ✅ 错误处理

### 2. **PDF转换器测试** (test_pdf_converter.py)
- ✅ Calibre查找（Windows/Linux/macOS）
- ✅ PDF到EPUB转换
- ✅ 中文文件名支持
- ✅ 输出目录指定
- ✅ Docker环境兼容
- ✅ 异常处理

### 3. **邮件发送器测试** (test_kindle_sender.py)
- ✅ SMTP配置自动识别
- ✅ SSL/TLS连接支持
- ✅ 文件大小限制检查（50MB）
- ✅ 认证错误处理
- ✅ 中文文件名编码
- ✅ 自定义邮件主题
- ✅ 邮件结构验证

### 4. **集成测试** (test_integration.py)
- ✅ 完整工作流程（上传→转换→发送）
- ✅ 一键处理功能
- ✅ 多文件格式支持
- ✅ 并发上传测试
- ✅ 配置持久化
- ✅ 错误恢复
- ✅ 中文支持

## 📈 测试报告

测试完成后会自动生成两种格式的报告：

### JSON报告 (test_report.json)
```json
{
  "timestamp": "2024-01-01 12:00:00",
  "total_tests": 50,
  "passed": 48,
  "failed": 1,
  "errors": 0,
  "skipped": 1,
  "success": false,
  "test_results": [...]
}
```

### HTML报告 (test_report.html)
- 可视化测试结果
- 通过率进度条
- 详细的测试列表
- 失败原因展示

## 🔧 测试环境要求

- Python 3.8+
- Flask及相关依赖
- unittest（Python内置）
- 可选：Calibre（用于PDF转换测试）

## 💡 最佳实践

### PDF转EPUB最有效的方法：

1. **使用Calibre（推荐）**
   - 最成熟的电子书转换工具
   - 支持智能格式化和启发式处理
   - 保持原始排版和图片
   ```python
   # 已在pdf_converter.py中实现
   convert_pdf_to_epub(pdf_path, output_dir)
   ```

2. **优化转换参数**
   ```python
   # 当前使用的优化参数
   "--enable-heuristics",     # 启用智能处理
   "--margin-top", "20",      # 设置页边距
   "--pretty-print",          # 美化输出
   "--insert-blank-line",     # 段落间空行
   "--language", "zh-CN"      # 中文优化
   ```

3. **备选方案**
   - 如果没有Calibre，直接发送PDF到Kindle
   - Kindle的Send to Kindle服务会自动转换
   - 适合简单的文本PDF

4. **性能优化建议**
   - 批量转换时使用多线程
   - 缓存转换结果避免重复转换
   - 对大文件进行分块处理

## 🐛 常见问题

1. **测试失败：找不到Calibre**
   - 解决：安装Calibre或使用Docker环境
   - 测试会自动跳过需要Calibre的部分

2. **邮件发送测试失败**
   - 确保测试配置文件中的邮箱信息正确
   - 某些测试使用mock对象，不需要真实邮箱

3. **文件权限错误**
   - 确保tests目录有写入权限
   - Windows用户以管理员身份运行

## 📝 添加新测试

在相应的测试文件中添加新的测试方法：

```python
def test_new_feature(self):
    """测试新功能"""
    # 准备测试数据
    test_data = {...}
    
    # 执行测试
    result = function_to_test(test_data)
    
    # 验证结果
    self.assertEqual(result, expected_value)
```

## 🔄 持续集成

可以将测试集成到CI/CD流程中：

```yaml
# GitHub Actions示例
- name: Run tests
  run: |
    pip install -r requirements.txt
    python tests/run_tests.py
```