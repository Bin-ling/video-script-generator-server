"""
系统模块功能自查测试框架
用于全面验证工具所有功能的正常运行状态

功能特性:
1. 功能覆盖：覆盖所有核心功能模块及边缘场景
2. 测试类型：单元测试、集成测试和端到端测试
3. 执行流程：支持单次运行和定时任务两种模式
4. 结果报告：详细的测试报告，包含通过/失败状态、错误信息、执行时间等
5. 异常处理：完善的错误捕获机制
6. 环境适配：兼容开发、测试和生产环境
7. 可维护性：模块化设计，便于扩展
"""

import os
import sys
import json
import time
import traceback
import unittest
import threading
import subprocess
import psutil
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib
import inspect


class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"


class TestPriority(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class TestResult:
    test_id: str
    test_name: str
    test_type: TestType
    status: TestStatus
    start_time: datetime = None
    end_time: datetime = None
    duration: float = 0.0
    error_message: str = ""
    error_traceback: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'test_id': self.test_id,
            'test_name': self.test_name,
            'test_type': self.test_type.value,
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'error_message': self.error_message,
            'error_traceback': self.error_traceback,
            'details': self.details,
            'metrics': self.metrics
        }


@dataclass
class TestReport:
    report_id: str
    start_time: datetime
    end_time: datetime = None
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    results: List[TestResult] = field(default_factory=list)
    system_info: Dict[str, Any] = field(default_factory=dict)
    environment: str = "development"
    
    def to_dict(self) -> Dict:
        return {
            'report_id': self.report_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_tests': self.total_tests,
            'passed': self.passed,
            'failed': self.failed,
            'skipped': self.skipped,
            'errors': self.errors,
            'pass_rate': f"{(self.passed / self.total_tests * 100):.2f}%" if self.total_tests > 0 else "0%",
            'duration': (self.end_time - self.start_time).total_seconds() if self.end_time else 0,
            'results': [r.to_dict() for r in self.results],
            'system_info': self.system_info,
            'environment': self.environment
        }


class BaseTest(ABC):
    def __init__(self, test_id: str, test_name: str, test_type: TestType, 
                 priority: TestPriority = TestPriority.MEDIUM):
        self.test_id = test_id
        self.test_name = test_name
        self.test_type = test_type
        self.priority = priority
        self.result = TestResult(
            test_id=test_id,
            test_name=test_name,
            test_type=test_type,
            status=TestStatus.PENDING
        )
    
    @abstractmethod
    def setup(self) -> bool:
        pass
    
    @abstractmethod
    def execute(self) -> bool:
        pass
    
    @abstractmethod
    def teardown(self) -> bool:
        pass
    
    def run(self) -> TestResult:
        self.result.start_time = datetime.now()
        self.result.status = TestStatus.RUNNING
        
        try:
            if not self.setup():
                self.result.status = TestStatus.ERROR
                self.result.error_message = "Setup failed"
                return self.result
            
            success = self.execute()
            self.result.status = TestStatus.PASSED if success else TestStatus.FAILED
            
        except Exception as e:
            self.result.status = TestStatus.ERROR
            self.result.error_message = str(e)
            self.result.error_traceback = traceback.format_exc()
        finally:
            try:
                self.teardown()
            except Exception as e:
                if self.result.status == TestStatus.PASSED:
                    self.result.status = TestStatus.ERROR
                    self.result.error_message = f"Teardown failed: {str(e)}"
            
            self.result.end_time = datetime.now()
            self.result.duration = (self.result.end_time - self.result.start_time).total_seconds()
        
        return self.result


class TestRegistry:
    _instance = None
    _tests: Dict[str, BaseTest] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, test: BaseTest):
        self._tests[test.test_id] = test
    
    def get_test(self, test_id: str) -> Optional[BaseTest]:
        return self._tests.get(test_id)
    
    def get_all_tests(self) -> List[BaseTest]:
        return list(self._tests.values())
    
    def get_tests_by_type(self, test_type: TestType) -> List[BaseTest]:
        return [t for t in self._tests.values() if t.test_type == test_type]
    
    def get_tests_by_priority(self, priority: TestPriority) -> List[BaseTest]:
        return [t for t in self._tests.values() if t.priority == priority]
    
    def clear(self):
        self._tests.clear()


def register_test(test_id: str, test_name: str, test_type: TestType, 
                  priority: TestPriority = TestPriority.MEDIUM):
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            BaseTest.__init__(self, test_id, test_name, test_type, priority)
            if original_init:
                original_init(self, *args, **kwargs)
        
        cls.__init__ = new_init
        cls.test_id = test_id
        cls.test_name = test_name
        cls.test_type = test_type
        cls.priority = priority
        
        return cls
    return decorator
