"""
主测试运行器
整合所有测试模块，提供完整的测试执行流程
"""

import os
import sys
import json
import time
import argparse
import platform
import threading
import schedule
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.system_test_framework import (
    TestRegistry, TestReport, TestResult, TestStatus, TestType, TestPriority, BaseTest
)
from tests.test_unit import register_unit_tests
from tests.test_integration import register_integration_tests
from tests.test_e2e import register_e2e_tests
from tests.test_reporter import ReportGenerator, ConsoleReporter


class SystemTestRunner:
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.registry = TestRegistry()
        self.report_generator = ReportGenerator()
        self.current_report: Optional[TestReport] = None
        self._stop_flag = False
    
    def register_all_tests(self):
        self.registry.clear()
        register_unit_tests()
        register_integration_tests()
        register_e2e_tests()
    
    def get_system_info(self) -> Dict[str, Any]:
        try:
            import psutil
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
        except:
            memory = None
            disk = None
        
        return {
            'os': platform.system(),
            'os_version': platform.version(),
            'python_version': platform.python_version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'memory': {
                'total': f"{memory.total / (1024**3):.2f} GB" if memory else 'N/A',
                'available': f"{memory.available / (1024**3):.2f} GB" if memory else 'N/A',
                'percent': f"{memory.percent}%" if memory else 'N/A'
            },
            'disk': {
                'total': f"{disk.total / (1024**3):.2f} GB" if disk else 'N/A',
                'free': f"{disk.free / (1024**3):.2f} GB" if disk else 'N/A',
                'percent': f"{disk.percent}%" if disk else 'N/A'
            },
            'environment': self.environment,
            'test_time': datetime.now().isoformat()
        }
    
    def run_tests(
        self,
        test_types: Optional[List[TestType]] = None,
        priorities: Optional[List[TestPriority]] = None,
        test_ids: Optional[List[str]] = None,
        parallel: bool = False,
        max_workers: int = 4
    ) -> TestReport:
        self.register_all_tests()
        
        tests = self.registry.get_all_tests()
        
        if test_ids:
            tests = [t for t in tests if t.test_id in test_ids]
        if test_types:
            tests = [t for t in tests if t.test_type in test_types]
        if priorities:
            tests = [t for t in tests if t.priority in priorities]
        
        tests.sort(key=lambda t: t.priority.value)
        
        report = TestReport(
            report_id=datetime.now().strftime('%Y%m%d_%H%M%S'),
            start_time=datetime.now(),
            environment=self.environment,
            system_info=self.get_system_info()
        )
        
        ConsoleReporter.print_header(f"系统功能自查测试 - {report.report_id}")
        print(f"环境: {self.environment}")
        print(f"测试数量: {len(tests)}")
        print(f"并行执行: {'是' if parallel else '否'}")
        
        if parallel:
            results = self._run_tests_parallel(tests, max_workers)
        else:
            results = self._run_tests_sequential(tests)
        
        report.results = results
        report.total_tests = len(results)
        report.passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        report.failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        report.errors = sum(1 for r in results if r.status == TestStatus.ERROR)
        report.skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)
        report.end_time = datetime.now()
        
        self.current_report = report
        
        ConsoleReporter.print_summary(report)
        
        return report
    
    def _run_tests_sequential(self, tests: List[BaseTest]) -> List[TestResult]:
        results = []
        for test in tests:
            if self._stop_flag:
                break
            
            ConsoleReporter.print_test_start(test.test_id, test.test_name)
            result = test.run()
            ConsoleReporter.print_test_result(result)
            results.append(result)
        
        return results
    
    def _run_tests_parallel(self, tests: List[BaseTest], max_workers: int) -> List[TestResult]:
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_test = {executor.submit(test.run): test for test in tests}
            
            for future in as_completed(future_to_test):
                if self._stop_flag:
                    executor.shutdown(wait=False)
                    break
                
                test = future_to_test[future]
                try:
                    result = future.result()
                    ConsoleReporter.print_test_start(test.test_id, test.test_name)
                    ConsoleReporter.print_test_result(result)
                    results.append(result)
                except Exception as e:
                    error_result = TestResult(
                        test_id=test.test_id,
                        test_name=test.test_name,
                        test_type=test.test_type,
                        status=TestStatus.ERROR,
                        error_message=str(e)
                    )
                    results.append(error_result)
        
        return sorted(results, key=lambda r: r.test_id)
    
    def generate_reports(self, report: Optional[TestReport] = None, formats: List[str] = None) -> Dict[str, str]:
        if report is None:
            report = self.current_report
        
        if report is None:
            raise ValueError("没有可用的测试报告")
        
        if formats is None:
            formats = ['json', 'html', 'markdown']
        
        paths = {}
        
        if 'json' in formats:
            paths['json'] = self.report_generator.generate_json_report(report)
        if 'html' in formats:
            paths['html'] = self.report_generator.generate_html_report(report)
        if 'markdown' in formats:
            paths['markdown'] = self.report_generator.generate_markdown_report(report)
        
        print("\n📁 生成的报告文件:")
        for fmt, path in paths.items():
            print(f"  [{fmt.upper()}] {path}")
        
        return paths
    
    def run_quick_check(self) -> TestReport:
        print("\n🚀 执行快速检查模式...")
        
        return self.run_tests(
            test_types=[TestType.UNIT],
            priorities=[TestPriority.CRITICAL, TestPriority.HIGH]
        )
    
    def run_full_check(self) -> TestReport:
        print("\n🔍 执行完整检查模式...")
        
        return self.run_tests()
    
    def run_smoke_test(self) -> TestReport:
        print("\n💨 执行冒烟测试...")
        
        return self.run_tests(
            priorities=[TestPriority.CRITICAL]
        )
    
    def stop(self):
        self._stop_flag = True


class ScheduledTestRunner:
    def __init__(self, runner: SystemTestRunner):
        self.runner = runner
        self._running = False
        self._thread = None
    
    def schedule_daily(self, time_str: str = "02:00"):
        schedule.clear()
        schedule.every().day.at(time_str).do(self._run_scheduled_test)
        print(f"已设置每日定时测试: {time_str}")
    
    def schedule_interval(self, hours: int = 6):
        schedule.clear()
        schedule.every(hours).hours.do(self._run_scheduled_test)
        print(f"已设置间隔测试: 每 {hours} 小时")
    
    def _run_scheduled_test(self):
        print(f"\n{'='*60}")
        print(f"定时测试开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        try:
            report = self.runner.run_tests()
            self.runner.generate_reports(report)
            
            if report.failed > 0 or report.errors > 0:
                self._send_alert(report)
        except Exception as e:
            print(f"定时测试执行失败: {str(e)}")
    
    def _send_alert(self, report: TestReport):
        print(f"\n⚠️ 测试失败告警!")
        print(f"失败: {report.failed}, 错误: {report.errors}")
    
    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
        print("定时测试服务已启动")
    
    def stop(self):
        self._running = False
        schedule.clear()
        print("定时测试服务已停止")
    
    def _run_scheduler(self):
        while self._running:
            schedule.run_pending()
            time.sleep(60)


def main():
    parser = argparse.ArgumentParser(
        description='系统功能自查测试脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python run_tests.py                    # 运行所有测试
  python run_tests.py --quick            # 快速检查
  python run_tests.py --smoke            # 冒烟测试
  python run_tests.py --type unit        # 只运行单元测试
  python run_tests.py --priority high    # 只运行高优先级测试
  python run_tests.py --parallel         # 并行执行
  python run_tests.py --schedule daily   # 设置每日定时测试
        """
    )
    
    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='快速检查模式（只运行单元测试的高优先级用例）'
    )
    
    parser.add_argument(
        '--smoke', '-s',
        action='store_true',
        help='冒烟测试模式（只运行关键测试）'
    )
    
    parser.add_argument(
        '--full', '-f',
        action='store_true',
        help='完整测试模式（运行所有测试）'
    )
    
    parser.add_argument(
        '--type', '-t',
        choices=['unit', 'integration', 'e2e'],
        action='append',
        help='指定测试类型（可多次使用）'
    )
    
    parser.add_argument(
        '--priority', '-p',
        choices=['critical', 'high', 'medium', 'low'],
        action='append',
        help='指定测试优先级（可多次使用）'
    )
    
    parser.add_argument(
        '--test-id', '-i',
        action='append',
        help='指定测试ID（可多次使用）'
    )
    
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='并行执行测试'
    )
    
    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=4,
        help='并行执行时的最大工作线程数（默认4）'
    )
    
    parser.add_argument(
        '--report', '-r',
        choices=['json', 'html', 'markdown', 'all'],
        default='all',
        help='报告格式（默认all）'
    )
    
    parser.add_argument(
        '--schedule',
        choices=['daily', 'interval'],
        help='设置定时任务'
    )
    
    parser.add_argument(
        '--schedule-time',
        default='02:00',
        help='每日定时测试时间（默认02:00）'
    )
    
    parser.add_argument(
        '--schedule-interval',
        type=int,
        default=6,
        help='间隔测试小时数（默认6小时）'
    )
    
    parser.add_argument(
        '--env', '-e',
        choices=['development', 'testing', 'production'],
        default='development',
        help='运行环境（默认development）'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='列出所有测试用例'
    )
    
    args = parser.parse_args()
    
    runner = SystemTestRunner(environment=args.env)
    runner.register_all_tests()
    
    if args.list:
        tests = runner.registry.get_all_tests()
        print("\n📋 已注册的测试用例:")
        print("-" * 60)
        
        current_type = None
        for test in sorted(tests, key=lambda t: (t.test_type.value, t.priority.value)):
            if test.test_type != current_type:
                current_type = test.test_type
                print(f"\n[{current_type.value.upper()}]")
            
            priority_icon = {
                TestPriority.CRITICAL: '🔴',
                TestPriority.HIGH: '🟠',
                TestPriority.MEDIUM: '🟡',
                TestPriority.LOW: '🟢'
            }.get(test.priority, '⚪')
            
            print(f"  {priority_icon} {test.test_id}: {test.test_name}")
        
        return
    
    if args.schedule:
        scheduled_runner = ScheduledTestRunner(runner)
        
        if args.schedule == 'daily':
            scheduled_runner.schedule_daily(args.schedule_time)
        else:
            scheduled_runner.schedule_interval(args.schedule_interval)
        
        scheduled_runner.start()
        
        print("\n定时测试服务运行中，按 Ctrl+C 停止...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            scheduled_runner.stop()
            print("\n定时测试服务已停止")
        
        return
    
    test_types = None
    if args.type:
        type_map = {
            'unit': TestType.UNIT,
            'integration': TestType.INTEGRATION,
            'e2e': TestType.E2E
        }
        test_types = [type_map[t] for t in args.type]
    
    priorities = None
    if args.priority:
        priority_map = {
            'critical': TestPriority.CRITICAL,
            'high': TestPriority.HIGH,
            'medium': TestPriority.MEDIUM,
            'low': TestPriority.LOW
        }
        priorities = [priority_map[p] for p in args.priority]
    
    if args.quick:
        report = runner.run_quick_check()
    elif args.smoke:
        report = runner.run_smoke_test()
    elif args.full or (not args.quick and not args.smoke and not args.type and not args.priority and not args.test_id):
        report = runner.run_full_check()
    else:
        report = runner.run_tests(
            test_types=test_types,
            priorities=priorities,
            test_ids=args.test_id,
            parallel=args.parallel,
            max_workers=args.workers
        )
    
    formats = ['json', 'html', 'markdown'] if args.report == 'all' else [args.report]
    runner.generate_reports(report, formats)
    
    exit_code = 0 if report.failed == 0 and report.errors == 0 else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
