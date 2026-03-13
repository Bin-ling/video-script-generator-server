"""
测试报告生成器
生成详细的测试报告，支持多种格式输出
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.system_test_framework import TestResult, TestReport, TestStatus, TestType


class ReportGenerator:
    def __init__(self, output_dir: str = "test_reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_json_report(self, report: TestReport) -> str:
        filename = f"test_report_{report.report_id}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def generate_html_report(self, report: TestReport) -> str:
        filename = f"test_report_{report.report_id}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        html_content = self._build_html_report(report)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def generate_markdown_report(self, report: TestReport) -> str:
        filename = f"test_report_{report.report_id}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        md_content = self._build_markdown_report(report)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return filepath
    
    def _build_html_report(self, report: TestReport) -> str:
        status_colors = {
            TestStatus.PASSED: '#28a745',
            TestStatus.FAILED: '#dc3545',
            TestStatus.ERROR: '#dc3545',
            TestStatus.SKIPPED: '#ffc107',
            TestStatus.PENDING: '#6c757d',
            TestStatus.RUNNING: '#17a2b8'
        }
        
        results_html = ""
        for result in report.results:
            color = status_colors.get(result.status, '#6c757d')
            results_html += f"""
            <tr>
                <td>{result.test_id}</td>
                <td>{result.test_name}</td>
                <td>{result.test_type.value}</td>
                <td><span style="color: {color}; font-weight: bold;">{result.status.value.upper()}</span></td>
                <td>{result.duration:.3f}s</td>
                <td>{result.error_message[:100] if result.error_message else '-'}</td>
            </tr>
            """
            if result.error_traceback:
                results_html += f"""
                <tr>
                    <td colspan="6" style="background-color: #f8f9fa; padding: 10px;">
                        <details>
                            <summary>错误详情</summary>
                            <pre style="white-space: pre-wrap; font-size: 12px;">{result.error_traceback}</pre>
                        </details>
                    </td>
                </tr>
                """
        
        pass_rate = (report.passed / report.total_tests * 100) if report.total_tests > 0 else 0
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>系统测试报告 - {report.report_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .header .subtitle {{
            opacity: 0.9;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-card .value {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .summary-card .label {{
            color: #666;
        }}
        .summary-card.passed .value {{ color: #28a745; }}
        .summary-card.failed .value {{ color: #dc3545; }}
        .summary-card.total .value {{ color: #007bff; }}
        .summary-card.rate .value {{ color: #17a2b8; }}
        .results-section {{
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .results-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            border-bottom: 1px solid #dee2e6;
        }}
        .results-header h2 {{
            margin: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .system-info {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-top: 20px;
        }}
        .system-info h3 {{
            margin-top: 0;
        }}
        .system-info pre {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 系统功能自查测试报告</h1>
        <div class="subtitle">
            报告ID: {report.report_id} | 
            环境: {report.environment} | 
            生成时间: {report.start_time.strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
    
    <div class="summary">
        <div class="summary-card total">
            <div class="value">{report.total_tests}</div>
            <div class="label">总测试数</div>
        </div>
        <div class="summary-card passed">
            <div class="value">{report.passed}</div>
            <div class="label">通过</div>
        </div>
        <div class="summary-card failed">
            <div class="value">{report.failed + report.errors}</div>
            <div class="label">失败</div>
        </div>
        <div class="summary-card rate">
            <div class="value">{pass_rate:.1f}%</div>
            <div class="label">通过率</div>
        </div>
    </div>
    
    <div class="results-section">
        <div class="results-header">
            <h2>📋 测试结果详情</h2>
        </div>
        <table>
            <thead>
                <tr>
                    <th>测试ID</th>
                    <th>测试名称</th>
                    <th>测试类型</th>
                    <th>状态</th>
                    <th>耗时</th>
                    <th>错误信息</th>
                </tr>
            </thead>
            <tbody>
                {results_html}
            </tbody>
        </table>
    </div>
    
    <div class="system-info">
        <h3>💻 系统信息</h3>
        <pre>{json.dumps(report.system_info, ensure_ascii=False, indent=2)}</pre>
    </div>
    
    <div class="footer">
        <p>报告生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
        """
        
        return html
    
    def _build_markdown_report(self, report: TestReport) -> str:
        pass_rate = (report.passed / report.total_tests * 100) if report.total_tests > 0 else 0
        duration = (report.end_time - report.start_time).total_seconds() if report.end_time else 0
        
        md = f"""# 系统功能自查测试报告

## 📊 概览

| 指标 | 值 |
|------|-----|
| 报告ID | {report.report_id} |
| 环境 | {report.environment} |
| 开始时间 | {report.start_time.strftime('%Y-%m-%d %H:%M:%S')} |
| 结束时间 | {report.end_time.strftime('%Y-%m-%d %H:%M:%S') if report.end_time else '-'} |
| 总耗时 | {duration:.2f}秒 |

## 📈 测试结果统计

| 类型 | 数量 |
|------|------|
| 总测试数 | {report.total_tests} |
| ✅ 通过 | {report.passed} |
| ❌ 失败 | {report.failed} |
| ⚠️ 错误 | {report.errors} |
| ⏭️ 跳过 | {report.skipped} |
| **通过率** | **{pass_rate:.1f}%** |

## 📋 详细测试结果

| 测试ID | 测试名称 | 类型 | 状态 | 耗时 | 错误信息 |
|--------|----------|------|------|------|----------|
"""
        
        for result in report.results:
            status_icon = {
                TestStatus.PASSED: '✅',
                TestStatus.FAILED: '❌',
                TestStatus.ERROR: '⚠️',
                TestStatus.SKIPPED: '⏭️',
                TestStatus.PENDING: '⏳',
                TestStatus.RUNNING: '🔄'
            }.get(result.status, '❓')
            
            error_short = result.error_message[:50] + '...' if len(result.error_message) > 50 else result.error_message
            md += f"| {result.test_id} | {result.test_name} | {result.test_type.value} | {status_icon} {result.status.value} | {result.duration:.3f}s | {error_short or '-'} |\n"
        
        md += f"""
## 💻 系统信息

```json
{json.dumps(report.system_info, ensure_ascii=False, indent=2)}
```

## 📝 失败测试详情

"""
        
        failed_tests = [r for r in report.results if r.status in [TestStatus.FAILED, TestStatus.ERROR]]
        if failed_tests:
            for result in failed_tests:
                md += f"""### {result.test_id}: {result.test_name}

**错误信息**: {result.error_message}

**耗时**: {result.duration:.3f}秒

"""
                if result.error_traceback:
                    md += f"""**错误堆栈**:
```
{result.error_traceback}
```

"""
        else:
            md += "所有测试均通过！🎉\n"
        
        md += f"""
---

*报告生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return md
    
    def generate_all_reports(self, report: TestReport) -> Dict[str, str]:
        json_path = self.generate_json_report(report)
        html_path = self.generate_html_report(report)
        md_path = self.generate_markdown_report(report)
        
        return {
            'json': json_path,
            'html': html_path,
            'markdown': md_path
        }


class ConsoleReporter:
    COLORS = {
        'reset': '\033[0m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m'
    }
    
    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        return f"{cls.COLORS.get(color, '')}{text}{cls.COLORS['reset']}"
    
    @classmethod
    def print_header(cls, title: str):
        print("\n" + "=" * 60)
        print(cls.colorize(f"  {title}", 'cyan'))
        print("=" * 60)
    
    @classmethod
    def print_test_start(cls, test_id: str, test_name: str):
        print(f"\n{cls.colorize('▶', 'blue')} [{test_id}] {test_name}")
    
    @classmethod
    def print_test_result(cls, result: TestResult):
        status_colors = {
            TestStatus.PASSED: 'green',
            TestStatus.FAILED: 'red',
            TestStatus.ERROR: 'red',
            TestStatus.SKIPPED: 'yellow',
            TestStatus.PENDING: 'white',
            TestStatus.RUNNING: 'blue'
        }
        
        color = status_colors.get(result.status, 'white')
        icon = {
            TestStatus.PASSED: '✓',
            TestStatus.FAILED: '✗',
            TestStatus.ERROR: '⚠',
            TestStatus.SKIPPED: '○',
            TestStatus.PENDING: '○',
            TestStatus.RUNNING: '●'
        }.get(result.status, '?')
        
        status_text = cls.colorize(f"{icon} {result.status.value.upper()}", color)
        duration_text = cls.colorize(f"({result.duration:.3f}s)", 'magenta')
        
        print(f"  {status_text} {duration_text}")
        
        if result.error_message:
            print(cls.colorize(f"    错误: {result.error_message}", 'red'))
    
    @classmethod
    def print_summary(cls, report: TestReport):
        pass_rate = (report.passed / report.total_tests * 100) if report.total_tests > 0 else 0
        duration = (report.end_time - report.start_time).total_seconds() if report.end_time else 0
        
        print("\n" + "=" * 60)
        print(cls.colorize("  📊 测试结果汇总", 'cyan'))
        print("=" * 60)
        
        print(f"\n  总测试数: {cls.colorize(str(report.total_tests), 'blue')}")
        print(f"  {cls.colorize('✓ 通过', 'green')}: {report.passed}")
        print(f"  {cls.colorize('✗ 失败', 'red')}: {report.failed}")
        print(f"  {cls.colorize('⚠ 错误', 'red')}: {report.errors}")
        print(f"  {cls.colorize('○ 跳过', 'yellow')}: {report.skipped}")
        print(f"\n  通过率: {cls.colorize(f'{pass_rate:.1f}%', 'green' if pass_rate >= 80 else 'yellow' if pass_rate >= 50 else 'red')}")
        print(f"  总耗时: {cls.colorize(f'{duration:.2f}秒', 'magenta')}")
        
        print("\n" + "-" * 60)
        
        if pass_rate == 100:
            print(cls.colorize("  🎉 所有测试通过！", 'green'))
        elif pass_rate >= 80:
            print(cls.colorize("  ⚠️ 大部分测试通过，请检查失败的测试", 'yellow'))
        else:
            print(cls.colorize("  ❌ 测试失败率较高，请检查系统状态", 'red'))
        
        print("=" * 60 + "\n")


if __name__ == "__main__":
    generator = ReportGenerator()
    
    sample_report = TestReport(
        report_id="sample_001",
        start_time=datetime.now(),
        end_time=datetime.now(),
        total_tests=3,
        passed=2,
        failed=1,
        errors=0,
        skipped=0,
        results=[
            TestResult(
                test_id="TEST_001",
                test_name="示例测试1",
                test_type=TestType.UNIT,
                status=TestStatus.PASSED,
                duration=0.5
            ),
            TestResult(
                test_id="TEST_002",
                test_name="示例测试2",
                test_type=TestType.INTEGRATION,
                status=TestStatus.FAILED,
                duration=1.2,
                error_message="断言失败"
            )
        ],
        system_info={"os": "Windows", "python": "3.10"}
    )
    
    paths = generator.generate_all_reports(sample_report)
    print("生成的报告文件:")
    for fmt, path in paths.items():
        print(f"  {fmt}: {path}")
