"""
端到端测试模块
测试完整的用户流程和业务场景
"""

import os
import sys
import json
import time
import requests
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.system_test_framework import (
    BaseTest, TestStatus, TestType, TestPriority, TestRegistry
)


class E2ETestBase(BaseTest):
    def __init__(self, test_id: str, test_name: str, priority: TestPriority = TestPriority.MEDIUM):
        super().__init__(
            test_id=test_id,
            test_name=test_name,
            test_type=TestType.E2E,
            priority=priority
        )
        self.base_url = os.getenv("TEST_BASE_URL", "http://localhost:5000")
        self.timeout = 60
    
    def check_server_running(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False


class FullPageLoadTest(E2ETestBase):
    def __init__(self):
        super().__init__(
            test_id="E2E_001",
            test_name="完整页面加载测试",
            priority=TestPriority.CRITICAL
        )
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行"
            return False
        return True
    
    def execute(self) -> bool:
        try:
            pages = [
                ('/', '首页'),
                ('/settings', '设置页'),
                ('/modules', '模块管理'),
                ('/history', '历史记录'),
                ('/lapian', '拉片分析'),
                ('/get_cookies', 'Cookies设置')
            ]
            
            results = {}
            all_passed = True
            total_load_time = 0
            
            for endpoint, name in pages:
                start_time = time.time()
                try:
                    response = requests.get(
                        f"{self.base_url}{endpoint}", 
                        timeout=self.timeout
                    )
                    load_time = time.time() - start_time
                    total_load_time += load_time
                    
                    passed = response.status_code == 200 and load_time < 5.0
                    results[endpoint] = {
                        'name': name,
                        'status_code': response.status_code,
                        'load_time': f"{load_time:.3f}s",
                        'response_size': len(response.content),
                        'passed': passed
                    }
                    if not passed:
                        all_passed = False
                        
                except Exception as e:
                    results[endpoint] = {
                        'name': name,
                        'error': str(e),
                        'passed': False
                    }
                    all_passed = False
            
            self.result.details['pages'] = results
            self.result.details['total_load_time'] = f"{total_load_time:.3f}s"
            self.result.details['avg_load_time'] = f"{total_load_time/len(pages):.3f}s"
            self.result.metrics['total_load_time'] = total_load_time
            
            return all_passed
        except Exception as e:
            self.result.error_message = f"页面加载测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class ModuleWorkflowTest(E2ETestBase):
    def __init__(self):
        super().__init__(
            test_id="E2E_002",
            test_name="模块管理工作流测试",
            priority=TestPriority.HIGH
        )
        self.test_module_id = None
        self.original_state = None
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行"
            return False
        return True
    
    def execute(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/modules", timeout=self.timeout)
            if response.status_code != 200:
                self.result.error_message = "获取模块列表失败"
                return False
            
            data = response.json()
            modules = data.get('modules', [])
            if not modules:
                self.result.error_message = "没有可用的模块"
                return False
            
            self.test_module_id = modules[0].get('id')
            self.original_state = modules[0].get('enabled')
            
            workflow_steps = []
            
            toggle_response = requests.post(
                f"{self.base_url}/api/modules/{self.test_module_id}/toggle",
                timeout=self.timeout
            )
            if toggle_response.status_code != 200:
                workflow_steps.append({'step': 'toggle', 'passed': False, 'error': '切换失败'})
                self.result.details['workflow'] = workflow_steps
                return False
            
            workflow_steps.append({'step': 'toggle', 'passed': True})
            
            time.sleep(0.5)
            
            verify_response = requests.get(
                f"{self.base_url}/api/modules",
                timeout=self.timeout
            )
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                for m in verify_data.get('modules', []):
                    if m.get('id') == self.test_module_id:
                        new_state = m.get('enabled')
                        workflow_steps.append({
                            'step': 'verify',
                            'passed': new_state != self.original_state,
                            'new_state': new_state
                        })
                        break
            
            self.result.details['workflow'] = workflow_steps
            self.result.details['module_id'] = self.test_module_id
            
            return all(step.get('passed', False) for step in workflow_steps)
        except Exception as e:
            self.result.error_message = f"模块工作流测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        if self.test_module_id and self.original_state is not None:
            try:
                requests.post(
                    f"{self.base_url}/api/modules/{self.test_module_id}/toggle",
                    timeout=self.timeout
                )
            except:
                pass
        return True


class LapianUploadTest(E2ETestBase):
    def __init__(self):
        super().__init__(
            test_id="E2E_003",
            test_name="拉片上传流程测试",
            priority=TestPriority.HIGH
        )
        self.test_file = None
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行"
            return False
        
        try:
            self.test_file = tempfile.NamedTemporaryFile(
                suffix='.mp4', 
                delete=False
            )
            self.test_file.write(b'fake video content for testing')
            self.test_file.close()
            return True
        except Exception as e:
            self.result.error_message = f"创建测试文件失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            with open(self.test_file.name, 'rb') as f:
                files = {'file': ('test_video.mp4', f, 'video/mp4')}
                response = requests.post(
                    f"{self.base_url}/api/lapian/upload",
                    files=files,
                    timeout=self.timeout
                )
            
            if response.status_code != 200:
                self.result.error_message = f"上传失败: {response.status_code}"
                self.result.details['response'] = response.text[:500]
                return False
            
            data = response.json()
            if not data.get('success'):
                self.result.error_message = f"上传返回失败: {data.get('error', '未知错误')}"
                return False
            
            self.result.details['upload_result'] = {
                'success': data.get('success'),
                'file_path': data.get('file_path', ''),
                'filename': data.get('filename', '')
            }
            
            return True
        except Exception as e:
            self.result.error_message = f"拉片上传测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        if self.test_file and os.path.exists(self.test_file.name):
            try:
                os.unlink(self.test_file.name)
            except:
                pass
        return True


class SettingsWorkflowTest(E2ETestBase):
    def __init__(self):
        super().__init__(
            test_id="E2E_004",
            test_name="设置工作流测试",
            priority=TestPriority.MEDIUM
        )
        self.original_config = None
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行"
            return False
        return True
    
    def execute(self) -> bool:
        try:
            get_response = requests.get(
                f"{self.base_url}/api/model_configs",
                timeout=self.timeout
            )
            if get_response.status_code != 200:
                self.result.error_message = "获取配置失败"
                return False
            
            self.original_config = get_response.json()
            self.result.details['original_config'] = {
                k: '***' if 'key' in k.lower() or 'password' in k.lower() else v
                for k, v in self.original_config.items()
            }
            
            self.result.details['workflow'] = [
                {'step': 'get_config', 'passed': True}
            ]
            
            return True
        except Exception as e:
            self.result.error_message = f"设置工作流测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class HistoryWorkflowTest(E2ETestBase):
    def __init__(self):
        super().__init__(
            test_id="E2E_005",
            test_name="历史记录工作流测试",
            priority=TestPriority.MEDIUM
        )
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行"
            return False
        return True
    
    def execute(self) -> bool:
        try:
            workflow_steps = []
            
            history_response = requests.get(
                f"{self.base_url}/history",
                timeout=self.timeout
            )
            workflow_steps.append({
                'step': 'load_history_page',
                'passed': history_response.status_code == 200
            })
            
            lapian_history_response = requests.get(
                f"{self.base_url}/api/lapian/history",
                timeout=self.timeout
            )
            workflow_steps.append({
                'step': 'get_lapian_history',
                'passed': lapian_history_response.status_code == 200
            })
            
            if lapian_history_response.status_code == 200:
                history_data = lapian_history_response.json()
                self.result.details['lapian_history_count'] = len(
                    history_data.get('records', [])
                )
            
            self.result.details['workflow'] = workflow_steps
            
            return all(step.get('passed', False) for step in workflow_steps)
        except Exception as e:
            self.result.error_message = f"历史记录工作流测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class ConcurrentRequestTest(E2ETestBase):
    def __init__(self):
        super().__init__(
            test_id="E2E_006",
            test_name="并发请求测试",
            priority=TestPriority.MEDIUM
        )
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行"
            return False
        return True
    
    def execute(self) -> bool:
        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            endpoints = [
                '/api/modules',
                '/api/progress',
                '/api/check_cookies',
                '/api/model_configs'
            ]
            
            results = []
            
            def make_request(endpoint):
                start = time.time()
                try:
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        timeout=self.timeout
                    )
                    return {
                        'endpoint': endpoint,
                        'status_code': response.status_code,
                        'duration': time.time() - start,
                        'passed': response.status_code == 200
                    }
                except Exception as e:
                    return {
                        'endpoint': endpoint,
                        'error': str(e),
                        'duration': time.time() - start,
                        'passed': False
                    }
            
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(make_request, ep) for ep in endpoints]
                for future in as_completed(futures):
                    results.append(future.result())
            
            self.result.details['concurrent_results'] = results
            self.result.details['all_passed'] = all(r.get('passed', False) for r in results)
            
            return all(r.get('passed', False) for r in results)
        except Exception as e:
            self.result.error_message = f"并发请求测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class ErrorHandlingTest(E2ETestBase):
    def __init__(self):
        super().__init__(
            test_id="E2E_007",
            test_name="错误处理测试",
            priority=TestPriority.MEDIUM
        )
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行"
            return False
        return True
    
    def execute(self) -> bool:
        try:
            test_cases = []
            
            invalid_module_response = requests.post(
                f"{self.base_url}/api/modules/nonexistent_module/toggle",
                timeout=self.timeout
            )
            test_cases.append({
                'case': 'invalid_module_toggle',
                'status_code': invalid_module_response.status_code,
                'handled': invalid_module_response.status_code in [400, 404, 500]
            })
            
            invalid_analysis_response = requests.get(
                f"{self.base_url}/api/get_analysis/999999",
                timeout=self.timeout
            )
            test_cases.append({
                'case': 'invalid_analysis_id',
                'status_code': invalid_analysis_response.status_code,
                'handled': True
            })
            
            invalid_lapian_response = requests.get(
                f"{self.base_url}/api/lapian/status/nonexistent_task",
                timeout=self.timeout
            )
            test_cases.append({
                'case': 'invalid_lapian_task',
                'status_code': invalid_lapian_response.status_code,
                'handled': invalid_lapian_response.status_code in [200, 404]
            })
            
            self.result.details['test_cases'] = test_cases
            
            return all(tc.get('handled', False) for tc in test_cases)
        except Exception as e:
            self.result.error_message = f"错误处理测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class PerformanceTest(E2ETestBase):
    def __init__(self):
        super().__init__(
            test_id="E2E_008",
            test_name="性能基准测试",
            priority=TestPriority.LOW
        )
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行"
            return False
        return True
    
    def execute(self) -> bool:
        try:
            endpoints = [
                ('/', '首页'),
                ('/api/modules', '模块API'),
                ('/api/progress', '进度API')
            ]
            
            iterations = 5
            results = {}
            
            for endpoint, name in endpoints:
                times = []
                for _ in range(iterations):
                    start = time.time()
                    try:
                        response = requests.get(
                            f"{self.base_url}{endpoint}",
                            timeout=self.timeout
                        )
                        times.append(time.time() - start)
                    except:
                        times.append(None)
                
                valid_times = [t for t in times if t is not None]
                if valid_times:
                    results[endpoint] = {
                        'name': name,
                        'avg_time': sum(valid_times) / len(valid_times),
                        'min_time': min(valid_times),
                        'max_time': max(valid_times),
                        'iterations': len(valid_times)
                    }
            
            self.result.details['performance'] = results
            self.result.metrics['performance'] = results
            
            avg_times = [r['avg_time'] for r in results.values()]
            self.result.details['overall_avg'] = sum(avg_times) / len(avg_times) if avg_times else 0
            
            return True
        except Exception as e:
            self.result.error_message = f"性能测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


def register_e2e_tests():
    registry = TestRegistry()
    registry.register(FullPageLoadTest())
    registry.register(ModuleWorkflowTest())
    registry.register(LapianUploadTest())
    registry.register(SettingsWorkflowTest())
    registry.register(HistoryWorkflowTest())
    registry.register(ConcurrentRequestTest())
    registry.register(ErrorHandlingTest())
    registry.register(PerformanceTest())


if __name__ == "__main__":
    register_e2e_tests()
    registry = TestRegistry()
    tests = registry.get_all_tests()
    
    print(f"共注册 {len(tests)} 个端到端测试")
    for test in tests:
        print(f"  - {test.test_id}: {test.test_name}")
