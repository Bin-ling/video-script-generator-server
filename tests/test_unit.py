"""
单元测试模块
测试各个独立组件的功能
"""

import os
import sys
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.system_test_framework import (
    BaseTest, TestStatus, TestType, TestPriority, TestRegistry, register_test
)


class ConfigManagerTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="UNIT_001",
            test_name="配置管理器测试",
            test_type=TestType.UNIT,
            priority=TestPriority.CRITICAL
        )
        self.config_manager = None
    
    def setup(self) -> bool:
        try:
            from config_manager import config_manager
            self.config_manager = config_manager
            return True
        except Exception as e:
            self.result.error_message = f"导入配置管理器失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            modules = self.config_manager.get_all_modules()
            if not modules:
                self.result.error_message = "没有找到任何模块配置"
                return False
            
            self.result.details['modules_count'] = len(modules)
            self.result.details['modules'] = list(modules.keys())
            
            for module_id, module_config in modules.items():
                if 'name' not in module_config:
                    self.result.error_message = f"模块 {module_id} 缺少 name 字段"
                    return False
            
            return True
        except Exception as e:
            self.result.error_message = f"配置管理器测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class DatabaseServiceTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="UNIT_002",
            test_name="数据库服务测试",
            test_type=TestType.UNIT,
            test_type=TestType.UNIT,
            priority=TestPriority.CRITICAL
        )
        self.db = None
    
    def setup(self) -> bool:
        try:
            from database import db
            self.db = db
            return True
        except Exception as e:
            self.result.error_message = f"导入数据库失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            analyses = self.db.get_all_analyses()
            self.result.details['analyses_count'] = len(analyses)
            self.result.details['sample'] = analyses[:3] if analyses else []
            return True
        except Exception as e:
            self.result.error_message = f"数据库查询失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class LapianDatabaseTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="UNIT_003",
            test_name="拉片数据库测试",
            test_type=TestType.UNIT,
            priority=TestPriority.HIGH
        )
        self.lapian_db = None
    
    def setup(self) -> bool:
        try:
            from database import lapian_db
            self.lapian_db = lapian_db
            return True
        except Exception as e:
            self.result.error_message = f"导入拉片数据库失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            records = self.lapian_db.get_all_lapian(limit=10)
            self.result.details['records_count'] = len(records)
            self.result.details['sample'] = records[:3] if records else []
            return True
        except Exception as e:
            self.result.error_message = f"拉片数据库查询失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class LLMServiceTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="UNIT_004",
            test_name="LLM服务测试",
            test_type=TestType.UNIT,
            priority=TestPriority.CRITICAL
        )
    
    def setup(self) -> bool:
        try:
            from llm import llm
            self.llm = llm
            return True
        except Exception as e:
            self.result.error_message = f"导入LLM服务失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            if self.llm is None:
                self.result.error_message = "LLM服务未初始化"
                return False
            
            self.result.details['llm_initialized'] = True
            return True
        except Exception as e:
            self.result.error_message = f"LLM服务测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class ModuleManagerTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="UNIT_005",
            test_name="模块管理器测试",
            test_type=TestType.UNIT,
            priority=TestPriority.HIGH
        )
    
    def setup(self) -> bool:
        try:
            from modules.analysis.modules.manager import module_manager
            self.module_manager = module_manager
            return True
        except Exception as e:
            self.result.error_message = f"导入模块管理器失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            modules = self.module_manager.get_all_modules()
            if not modules:
                self.result.error_message = "没有找到任何分析模块"
                return False
            
            self.result.details['modules_count'] = len(modules)
            self.result.details['modules'] = {}
            
            for module_id, module in modules.items():
                self.result.details['modules'][module_id] = {
                    'name': module.get_name(),
                    'type': module.get_type(),
                    'enabled': module.is_enabled()
                }
            
            return True
        except Exception as e:
            self.result.error_message = f"模块管理器测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class ProgressManagerTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="UNIT_006",
            test_name="进度管理器测试",
            test_type=TestType.UNIT,
            priority=TestPriority.MEDIUM
        )
    
    def setup(self) -> bool:
        try:
            from app.utils.progress_manager import progress
            self.progress = progress
            return True
        except Exception as e:
            self.result.error_message = f"导入进度管理器失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            self.result.details['current_progress'] = {
                'percentage': self.progress.get('percentage', 0),
                'status': self.progress.get('status', ''),
                'message': self.progress.get('message', '')
            }
            return True
        except Exception as e:
            self.result.error_message = f"进度管理器测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class TaskManagerTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="UNIT_007",
            test_name="任务管理器测试",
            test_type=TestType.UNIT,
            priority=TestPriority.MEDIUM
        )
    
    def setup(self) -> bool:
        try:
            from app.utils.task_manager import async_tasks, task_lock
            self.async_tasks = async_tasks
            self.task_lock = task_lock
            return True
        except Exception as e:
            self.result.error_message = f"导入任务管理器失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            with self.task_lock:
                self.result.details['tasks_count'] = len(self.async_tasks)
                self.result.details['task_ids'] = list(self.async_tasks.keys())[:5]
            return True
        except Exception as e:
            self.result.error_message = f"任务管理器测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class FileUtilityTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="UNIT_008",
            test_name="文件工具测试",
            test_type=TestType.UNIT,
            priority=TestPriority.MEDIUM
        )
    
    def setup(self) -> bool:
        try:
            from modules.utils.file_utils import ensure_dir, get_file_size
            self.ensure_dir = ensure_dir
            self.get_file_size = get_file_size
            return True
        except Exception as e:
            self.result.error_message = f"导入文件工具失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            test_dir = "test_temp_dir"
            self.ensure_dir(test_dir)
            
            if not os.path.exists(test_dir):
                self.result.error_message = "创建测试目录失败"
                return False
            
            test_file = os.path.join(test_dir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test content")
            
            file_size = self.get_file_size(test_file)
            self.result.details['test_dir'] = test_dir
            self.result.details['file_size'] = file_size
            
            os.remove(test_file)
            os.rmdir(test_dir)
            
            return True
        except Exception as e:
            self.result.error_message = f"文件工具测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        test_dir = "test_temp_dir"
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)
        return True


class LoggerTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="UNIT_009",
            test_name="日志系统测试",
            test_type=TestType.UNIT,
            priority=TestPriority.LOW
        )
    
    def setup(self) -> bool:
        try:
            from app.utils.logger import logger
            self.logger = logger
            return True
        except Exception as e:
            self.result.error_message = f"导入日志系统失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            self.logger.info("测试日志 - INFO级别")
            self.logger.warning("测试日志 - WARNING级别")
            self.logger.error("测试日志 - ERROR级别")
            self.result.details['logger_working'] = True
            return True
        except Exception as e:
            self.result.error_message = f"日志系统测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class VideoProcessorTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="UNIT_010",
            test_name="视频处理器测试",
            test_type=TestType.UNIT,
            priority=TestPriority.HIGH
        )
    
    def setup(self) -> bool:
        try:
            from modules.video_processor.processor import VideoProcessor
            self.VideoProcessor = VideoProcessor
            return True
        except Exception as e:
            self.result.error_message = f"导入视频处理器失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            processor = self.VideoProcessor()
            self.result.details['processor_initialized'] = True
            return True
        except Exception as e:
            self.result.error_message = f"视频处理器测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


def register_unit_tests():
    registry = TestRegistry()
    registry.register(ConfigManagerTest())
    registry.register(DatabaseServiceTest())
    registry.register(LapianDatabaseTest())
    registry.register(LLMServiceTest())
    registry.register(ModuleManagerTest())
    registry.register(ProgressManagerTest())
    registry.register(TaskManagerTest())
    registry.register(FileUtilityTest())
    registry.register(LoggerTest())
    registry.register(VideoProcessorTest())


if __name__ == "__main__":
    register_unit_tests()
    registry = TestRegistry()
    tests = registry.get_all_tests()
    
    print(f"共注册 {len(tests)} 个单元测试")
    for test in tests:
        print(f"  - {test.test_id}: {test.test_name}")
