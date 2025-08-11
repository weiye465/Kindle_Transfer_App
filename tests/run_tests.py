#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行脚本 - 运行所有测试并生成报告
"""
import sys
import os
import unittest
import time
from io import StringIO
import json

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ColoredTestResult(unittest.TextTestResult):
    """彩色测试结果输出"""
    
    # ANSI颜色代码
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_results = []
    
    def startTest(self, test):
        super().startTest(test)
        self.start_time = time.time()
    
    def addSuccess(self, test):
        super().addSuccess(test)
        elapsed = time.time() - self.start_time
        self.test_results.append({
            'test': str(test),
            'status': 'PASS',
            'time': elapsed
        })
        if self.showAll:
            self.stream.writeln(f"{self.GREEN}✓ PASS{self.RESET} ({elapsed:.3f}s)")
    
    def addError(self, test, err):
        super().addError(test, err)
        elapsed = time.time() - self.start_time
        self.test_results.append({
            'test': str(test),
            'status': 'ERROR',
            'time': elapsed,
            'error': str(err[1])
        })
        if self.showAll:
            self.stream.writeln(f"{self.RED}✗ ERROR{self.RESET} ({elapsed:.3f}s)")
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        elapsed = time.time() - self.start_time
        self.test_results.append({
            'test': str(test),
            'status': 'FAIL',
            'time': elapsed,
            'error': str(err[1])
        })
        if self.showAll:
            self.stream.writeln(f"{self.RED}✗ FAIL{self.RESET} ({elapsed:.3f}s)")
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        elapsed = time.time() - self.start_time
        self.test_results.append({
            'test': str(test),
            'status': 'SKIP',
            'time': elapsed,
            'reason': reason
        })
        if self.showAll:
            self.stream.writeln(f"{self.YELLOW}○ SKIP{self.RESET}: {reason}")


class ColoredTestRunner(unittest.TextTestRunner):
    """彩色测试运行器"""
    resultclass = ColoredTestResult


def run_tests(test_dir='tests', pattern='test_*.py', verbosity=2, 
              generate_report=True, run_specific=None):
    """
    运行测试
    
    Args:
        test_dir: 测试目录
        pattern: 测试文件模式
        verbosity: 详细程度 (0=静默, 1=正常, 2=详细)
        generate_report: 是否生成测试报告
        run_specific: 运行特定的测试模块或测试类
    
    Returns:
        测试结果
    """
    print(f"{ColoredTestResult.BOLD}=== Kindle Transfer App 测试套件 ==={ColoredTestResult.RESET}\n")
    
    # 创建测试套件
    if run_specific:
        # 运行特定测试
        if '.' in run_specific:
            # 运行特定的测试类或方法
            suite = unittest.TestLoader().loadTestsFromName(run_specific)
        else:
            # 运行特定的测试模块
            suite = unittest.TestLoader().loadTestsFromName(f'tests.{run_specific}')
    else:
        # 运行所有测试
        loader = unittest.TestLoader()
        suite = loader.discover(test_dir, pattern=pattern)
    
    # 运行测试
    runner = ColoredTestRunner(verbosity=verbosity)
    start_time = time.time()
    result = runner.run(suite)
    total_time = time.time() - start_time
    
    # 打印统计信息
    print(f"\n{ColoredTestResult.BOLD}=== 测试统计 ==={ColoredTestResult.RESET}")
    print(f"运行时间: {total_time:.2f} 秒")
    print(f"运行测试: {result.testsRun} 个")
    
    if result.wasSuccessful():
        print(f"{ColoredTestResult.GREEN}✓ 所有测试通过！{ColoredTestResult.RESET}")
    else:
        print(f"{ColoredTestResult.RED}✗ 测试失败！{ColoredTestResult.RESET}")
        print(f"  失败: {len(result.failures)} 个")
        print(f"  错误: {len(result.errors)} 个")
        print(f"  跳过: {len(result.skipped)} 个")
    
    # 生成测试报告
    if generate_report and hasattr(result, 'test_results'):
        generate_test_report(result)
    
    return result


def generate_test_report(result):
    """
    生成测试报告
    
    Args:
        result: 测试结果对象
    """
    report_dir = 'tests/reports'
    os.makedirs(report_dir, exist_ok=True)
    
    # 生成JSON报告
    json_report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_tests': result.testsRun,
        'passed': len([r for r in result.test_results if r['status'] == 'PASS']),
        'failed': len(result.failures),
        'errors': len(result.errors),
        'skipped': len(result.skipped),
        'success': result.wasSuccessful(),
        'test_results': result.test_results
    }
    
    json_file = os.path.join(report_dir, 'test_report.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)
    
    # 生成HTML报告
    html_content = generate_html_report(json_report)
    html_file = os.path.join(report_dir, 'test_report.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n测试报告已生成:")
    print(f"  JSON: {json_file}")
    print(f"  HTML: {html_file}")


def generate_html_report(report_data):
    """
    生成HTML格式的测试报告
    
    Args:
        report_data: 报告数据
    
    Returns:
        HTML内容
    """
    status_colors = {
        'PASS': '#28a745',
        'FAIL': '#dc3545',
        'ERROR': '#dc3545',
        'SKIP': '#ffc107'
    }
    
    # 生成测试结果行
    test_rows = ''
    for test in report_data['test_results']:
        status_color = status_colors.get(test['status'], '#6c757d')
        error_info = ''
        if 'error' in test:
            error_info = f'<br><small class="text-muted">{test.get("error", "")[:200]}...</small>'
        elif 'reason' in test:
            error_info = f'<br><small class="text-muted">原因: {test.get("reason", "")}</small>'
        
        test_rows += f'''
        <tr>
            <td>{test["test"]}{error_info}</td>
            <td><span class="badge" style="background-color: {status_color};">{test["status"]}</span></td>
            <td>{test["time"]:.3f}s</td>
        </tr>
        '''
    
    # 计算通过率
    pass_rate = (report_data['passed'] / report_data['total_tests'] * 100) if report_data['total_tests'] > 0 else 0
    
    html = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kindle Transfer App - 测试报告</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .summary-card {{
            margin-bottom: 20px;
        }}
        .badge {{
            padding: 5px 10px;
            color: white;
        }}
        .test-table {{
            margin-top: 20px;
        }}
        .progress {{
            height: 30px;
        }}
    </style>
</head>
<body>
    <div class="container mt-5">
        <h1 class="mb-4">📚 Kindle Transfer App - 测试报告</h1>
        
        <div class="row summary-card">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">测试概览</h5>
                        <p class="text-muted">生成时间: {report_data['timestamp']}</p>
                        
                        <div class="row mt-3">
                            <div class="col-md-3">
                                <h6>总测试数</h6>
                                <h3>{report_data['total_tests']}</h3>
                            </div>
                            <div class="col-md-3">
                                <h6>通过</h6>
                                <h3 class="text-success">{report_data['passed']}</h3>
                            </div>
                            <div class="col-md-3">
                                <h6>失败</h6>
                                <h3 class="text-danger">{report_data['failed'] + report_data['errors']}</h3>
                            </div>
                            <div class="col-md-3">
                                <h6>跳过</h6>
                                <h3 class="text-warning">{report_data['skipped']}</h3>
                            </div>
                        </div>
                        
                        <div class="mt-4">
                            <h6>通过率</h6>
                            <div class="progress">
                                <div class="progress-bar {'bg-success' if pass_rate >= 80 else 'bg-warning' if pass_rate >= 60 else 'bg-danger'}" 
                                     role="progressbar" 
                                     style="width: {pass_rate}%">
                                    {pass_rate:.1f}%
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card test-table">
            <div class="card-body">
                <h5 class="card-title">测试详情</h5>
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>测试名称</th>
                                <th>状态</th>
                                <th>耗时</th>
                            </tr>
                        </thead>
                        <tbody>
                            {test_rows}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    '''
    
    return html


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Kindle Transfer App 测试运行器')
    parser.add_argument('-v', '--verbosity', type=int, default=2, choices=[0, 1, 2],
                       help='测试输出详细程度 (0=静默, 1=正常, 2=详细)')
    parser.add_argument('-p', '--pattern', default='test_*.py',
                       help='测试文件匹配模式')
    parser.add_argument('-t', '--test', help='运行特定的测试模块、类或方法')
    parser.add_argument('--no-report', action='store_true',
                       help='不生成测试报告')
    parser.add_argument('--list', action='store_true',
                       help='列出所有可用的测试模块')
    
    args = parser.parse_args()
    
    if args.list:
        # 列出所有测试模块
        print("可用的测试模块:")
        test_files = [f[:-3] for f in os.listdir('tests') if f.startswith('test_') and f.endswith('.py')]
        for test_file in test_files:
            print(f"  - {test_file}")
        print(f"\n使用示例: python tests/run_tests.py -t {test_files[0]}")
        return
    
    # 运行测试
    result = run_tests(
        verbosity=args.verbosity,
        pattern=args.pattern,
        generate_report=not args.no_report,
        run_specific=args.test
    )
    
    # 返回退出码
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()