"""
集成测试模块
测试模块之间的交互和API端点
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.system_test_framework import (
    BaseTest, TestStatus, TestType, TestPriority, TestRegistry
)


class IntegrationTestBase(BaseTest):
    def __init__(self, test_id: str, test_name: str, priority: TestPriority = TestPriority.MEDIUM):
        super().__init__(
            test_id=test_id,
            test_name=test_name,
            test_type=TestType.INTEGRATION,
            priority=priority
        )
        self.base_url = os.getenv("TEST_BASE_URL", "http://localhost:5000")
        self.timeout = 30
    
    def check_server_running(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            return response.status_code == 200
        except:
            return False


class APIHealthCheckTest(IntegrationTestBase):
    def __init__(self):
        super().__init__(
            test_id="INT_001",
            test_name="API健康检查测试",
            priority=TestPriority.CRITICAL
        )
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行，请先启动服务"
            return False
        return True
    
    def execute(self) -> bool:
        try:
            endpoints = [
                ('/', '首页'),
                ('/settings', '设置页'),
                ('/modules', '模块管理页'),
                ('/history', '历史记录页'),
                ('/lapian', '拉片分析页'),
                ('/api/modules', '模块API'),
                ('/api/progress', '进度API'),
                ('/api/check_cookies', 'Cookies检查API')
            ]
            
            results = {}
            all_passed = True
            
            for endpoint, name in endpoints:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=self.timeout)
                    results[endpoint] = {
                        'name': name,
                        'status_code': response.status_code,
                        'passed': response.status_code in [200, 302]
                    }
                    if response.status_code not in [200, 302]:
                        all_passed = False
                except Exception as e:
                    results[endpoint] = {
                        'name': name,
                        'status_code': 0,
                        'error': str(e),
                        'passed': False
                    }
                    all_passed = False
            
            self.result.details['endpoints'] = results
            return all_passed
        except Exception as e:
            self.result.error_message = f"API健康检查失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class ModulesAPITest(IntegrationTestBase):
    def __init__(self):
        super().__init__(
            test_id="INT_002",
            test_name="模块API测试",
            priority=TestPriority.HIGH
        )
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行"
            return False
        return True
    
    def execute(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/modules", timeout=self.timeout)
            if response.status_code != 200:
                self.result.error_message = f"API返回状态码: {response.status_code}"
                return False
            
            data = response.json()
            if not data.get('success'):
                self.result.error_message = "API返回失败状态"
                return False
            
            modules = data.get('modules', [])
            self.result.details['modules_count'] = len(modules)
            self.result.details['modules'] = [
                {'id': m.get('id'), 'name': m.get('name'), 'enabled': m.get('enabled')}
                for m in modules
            ]
            
            return True
        except Exception as e:
            self.result.error_message = f"模块API测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class ModuleToggleTest(IntegrationTestBase):
    def __init__(self):
        super().__init__(
            test_id="INT_003",
            test_name="模块切换测试",
            priority=TestPriority.HIGH
        )
        self.original_state = None
        self.test_module_id = None
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行"
            return False
        
        try:
            response = requests.get(f"{self.base_url}/api/modules", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                modules = data.get('modules', [])
                if modules:
                    self.test_module_id = modules[0].get('id')
                    self.original_state = modules[0].get('enabled')
                    return True
            
            self.result.error_message = "无法获取模块列表"
            return False
        except Exception as e:
            self.result.error_message = f"初始化失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        if not self.test_module_id:
            self.result.error_message = "没有可测试的模块"
            return False
        
        try:
            toggle_url = f"{self.base_url}/api/modules/{self.test_module_id}/toggle"
            response = requests.post(toggle_url, timeout=self.timeout)
            
            if response.status_code != 200:
                self.result.error_message = f"切换请求失败: {response.status_code}"
                return False
            
            data = response.json()
            if not data.get('success'):
                self.result.error_message = "切换操作失败"
                return False
            
            new_state = data.get('enabled')
            self.result.details['module_id'] = self.test_module_id
            self.result.details['original_state'] = self.original_state
            self.result.details['new_state'] = new_state
            self.result.details['state_changed'] = new_state != self.original_state
            
            return True
        except Exception as e:
            self.result.error_message = f"模块切换测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        if self.test_module_id and self.original_state is not None:
            try:
                current_response = requests.get(
                    f"{self.base_url}/api/modules", 
                    timeout=self.timeout
                )
                if current_response.status_code == 200:
                    data = current_response.json()
                    modules = data.get('modules', [])
                    for m in modules:
                        if m.get('id') == self.test_module_id:
                            if m.get('enabled') != self.original_state:
                                requests.post(
                                    f"{self.base_url}/api/modules/{self.test_module_id}/toggle",
                                    timeout=self.timeout
                                )
                            break
            except:
                pass
        return True


class ModelConfigTest(IntegrationTestBase):
    def __init__(self):
        super().__init__(
            test_id="INT_004",
            test_name="模型配置API测试",
            priority=TestPriority.HIGH
        )
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行"
            return False
        return True
    
    def execute(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/model_configs", timeout=self.timeout)
            if response.status_code != 200:
                self.result.error_message = f"API返回状态码: {response.status_code}"
                return False
            
            data = response.json()
            self.result.details['configs'] = data
            
            required_keys = ['api_key_configured', 'base_url_configured', 'model_name']
            for key in required_keys:
                if key not in data:
                    self.result.details['warning'] = f"缺少配置项: {key}"
            
            return True
        except Exception as e:
            self.result.error_message = f"模型配置测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class CookiesCheckTest(IntegrationTestBase):
    def __init__(self):
        super().__init__(
            test_id="INT_005",
            test_name="Cookies检查测试",
            priority=TestPriority.MEDIUM
        )
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行"
            return False
        return True
    
    def execute(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/api/check_cookies", 
                timeout=self.timeout
            )
            if response.status_code != 200:
                self.result.error_message = f"API返回状态码: {response.status_code}"
                return False
            
            data = response.json()
            self.result.details['cookies_exists'] = data.get('exists', False)
            self.result.details['message'] = data.get('message', '')
            
            return True
        except Exception as e:
            self.result.error_message = f"Cookies检查测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class HistoryAPITest(IntegrationTestBase):
    def __init__(self):
        super().__init__(
            test_id="INT_006",
            test_name="历史记录API测试",
            priority=TestPriority.MEDIUM
        )
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行"
            return False
        return True
    
    def execute(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/history", timeout=self.timeout)
            if response.status_code != 200:
                self.result.error_message = f"页面返回状态码: {response.status_code}"
                return False
            
            self.result.details['page_accessible'] = True
            return True
        except Exception as e:
            self.result.error_message = f"历史记录测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class LapianAPITest(IntegrationTestBase):
    def __init__(self):
        super().__init__(
            test_id="INT_007",
            test_name="拉片API测试",
            priority=TestPriority.HIGH
        )
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行"
            return False
        return True
    
    def execute(self) -> bool:
        try:
            endpoints = [
                ('/lapian', 'GET', '拉片页面'),
                ('/api/lapian/history', 'GET', '拉片历史API'),
            ]
            
            results = {}
            all_passed = True
            
            for endpoint, method, name in endpoints:
                try:
                    if method == 'GET':
                        response = requests.get(f"{self.base_url}{endpoint}", timeout=self.timeout)
                    
                    results[endpoint] = {
                        'name': name,
                        'status_code': response.status_code,
                        'passed': response.status_code == 200
                    }
                    if response.status_code != 200:
                        all_passed = False
                except Exception as e:
                    results[endpoint] = {
                        'name': name,
                        'error': str(e),
                        'passed': False
                    }
                    all_passed = False
            
            self.result.details['endpoints'] = results
            return all_passed
        except Exception as e:
            self.result.error_message = f"拉片API测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class ProgressAPITest(IntegrationTestBase):
    def __init__(self):
        super().__init__(
            test_id="INT_008",
            test_name="进度API测试",
            priority=TestPriority.MEDIUM
        )
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行"
            return False
        return True
    
    def execute(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/progress", timeout=self.timeout)
            if response.status_code != 200:
                self.result.error_message = f"API返回状态码: {response.status_code}"
                return False
            
            data = response.json()
            self.result.details['progress'] = {
                'percentage': data.get('percentage', 0),
                'status': data.get('status', ''),
                'message': data.get('message', '')
            }
            
            return True
        except Exception as e:
            self.result.error_message = f"进度API测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class DatabaseIntegrationTest(IntegrationTestBase):
    def __init__(self):
        super().__init__(
            test_id="INT_009",
            test_name="数据库集成测试",
            priority=TestPriority.HIGH
        )
    
    def setup(self) -> bool:
        try:
            from database import db, lapian_db
            self.db = db
            self.lapian_db = lapian_db
            return True
        except Exception as e:
            self.result.error_message = f"数据库初始化失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            analyses = self.db.get_all_analyses()
            lapian_records = self.lapian_db.get_all_lapian(limit=10)
            
            self.result.details['analyses_count'] = len(analyses)
            self.result.details['lapian_records_count'] = len(lapian_records)
            
            if analyses:
                analysis = analyses[0]
                if 'id' in analysis:
                    detail = self.db.get_analysis_by_id(analysis['id'])
                    self.result.details['sample_analysis'] = {
                        'id': analysis.get('id'),
                        'url': analysis.get('url', '')[:50],
                        'has_detail': detail is not None
                    }
            
            return True
        except Exception as e:
            self.result.error_message = f"数据库集成测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


def register_integration_tests():
    registry = TestRegistry()
    registry.register(APIHealthCheckTest())
    registry.register(ModulesAPITest())
    registry.register(ModuleToggleTest())
    registry.register(ModelConfigTest())
    registry.register(CookiesCheckTest())
    registry.register(HistoryAPITest())
    registry.register(LapianAPITest())
    registry.register(ProgressAPITest())
    registry.register(DatabaseIntegrationTest())


if __name__ == "__main__":
    register_integration_tests()
    registry = TestRegistry()
    tests = registry.get_all_tests()
    
    print(f"共注册 {len(tests)} 个集成测试")
    for test in tests:
        print(f"  - {test.test_id}: {test.test_name}")
