# 系统功能自查测试框架

## 概述

本测试框架用于全面验证视频分析工具的所有功能模块，确保系统在发布前或日常维护中能够快速发现潜在问题。

## 功能特性

- ✅ **功能覆盖**: 覆盖所有核心功能模块及边缘场景
- ✅ **测试类型**: 支持单元测试、集成测试和端到端测试
- ✅ **执行流程**: 自动化执行，支持单次运行和定时任务
- ✅ **结果报告**: 详细的测试报告（JSON/HTML/Markdown格式）
- ✅ **异常处理**: 完善的错误捕获机制
- ✅ **环境适配**: 兼容开发、测试和生产环境
- ✅ **可维护性**: 模块化设计，便于扩展

## 目录结构

```
tests/
├── __init__.py
├── system_test_framework.py  # 核心测试框架
├── test_unit.py              # 单元测试
├── test_integration.py       # 集成测试
├── test_e2e.py               # 端到端测试
├── test_reporter.py          # 报告生成器
├── run_tests.py              # 主测试运行器
├── test_reports/             # 测试报告输出目录
└── README.md                 # 本文档
```

## 快速开始

### 基本用法

```bash
# 运行所有测试
python tests/run_tests.py

# 快速检查模式（只运行单元测试的高优先级用例）
python tests/run_tests.py --quick

# 冒烟测试模式（只运行关键测试）
python tests/run_tests.py --smoke

# 完整测试模式
python tests/run_tests.py --full
```

### 按类型运行

```bash
# 只运行单元测试
python tests/run_tests.py --type unit

# 只运行集成测试
python tests/run_tests.py --type integration

# 只运行端到端测试
python tests/run_tests.py --type e2e

# 运行多种类型
python tests/run_tests.py --type unit --type integration
```

### 按优先级运行

```bash
# 只运行关键测试
python tests/run_tests.py --priority critical

# 只运行高优先级测试
python tests/run_tests.py --priority high

# 运行多种优先级
python tests/run_tests.py --priority critical --priority high
```

### 指定测试ID

```bash
# 运行特定测试
python tests/run_tests.py --test-id UNIT_001 --test-id UNIT_002
```

### 并行执行

```bash
# 并行执行测试（默认4个工作线程）
python tests/run_tests.py --parallel

# 指定工作线程数
python tests/run_tests.py --parallel --workers 8
```

### 报告格式

```bash
# 生成所有格式报告
python tests/run_tests.py --report all

# 只生成JSON报告
python tests/run_tests.py --report json

# 只生成HTML报告
python tests/run_tests.py --report html

# 只生成Markdown报告
python tests/run_tests.py --report markdown
```

### 定时任务

```bash
# 设置每日定时测试（默认02:00）
python tests/run_tests.py --schedule daily

# 指定每日测试时间
python tests/run_tests.py --schedule daily --schedule-time 03:00

# 设置间隔测试（默认6小时）
python tests/run_tests.py --schedule interval

# 指定间隔小时数
python tests/run_tests.py --schedule interval --schedule-interval 4
```

### 其他选项

```bash
# 列出所有测试用例
python tests/run_tests.py --list

# 指定运行环境
python tests/run_tests.py --env production
```

## 测试用例列表

### 单元测试 (UNIT)

| ID | 名称 | 优先级 | 描述 |
|----|------|--------|------|
| UNIT_001 | 配置管理器测试 | 🔴 关键 | 测试配置管理器的加载和读取功能 |
| UNIT_002 | 数据库服务测试 | 🔴 关键 | 测试数据库连接和基本操作 |
| UNIT_003 | 拉片数据库测试 | 🟠 高 | 测试拉片数据库操作 |
| UNIT_004 | LLM服务测试 | 🔴 关键 | 测试大语言模型服务初始化 |
| UNIT_005 | 模块管理器测试 | 🟠 高 | 测试分析模块管理器 |
| UNIT_006 | 进度管理器测试 | 🟡 中 | 测试进度跟踪功能 |
| UNIT_007 | 任务管理器测试 | 🟡 中 | 测试异步任务管理 |
| UNIT_008 | 文件工具测试 | 🟡 中 | 测试文件操作工具 |
| UNIT_009 | 日志系统测试 | 🟢 低 | 测试日志记录功能 |
| UNIT_010 | 视频处理器测试 | 🟠 高 | 测试视频处理核心功能 |

### 集成测试 (INT)

| ID | 名称 | 优先级 | 描述 |
|----|------|--------|------|
| INT_001 | API健康检查测试 | 🔴 关键 | 检查所有API端点的可用性 |
| INT_002 | 模块API测试 | 🟠 高 | 测试模块管理API |
| INT_003 | 模块切换测试 | 🟠 高 | 测试模块启用/禁用功能 |
| INT_004 | 模型配置API测试 | 🟠 高 | 测试模型配置API |
| INT_005 | Cookies检查测试 | 🟡 中 | 测试Cookies检查功能 |
| INT_006 | 历史记录API测试 | 🟡 中 | 测试历史记录功能 |
| INT_007 | 拉片API测试 | 🟠 高 | 测试拉片分析API |
| INT_008 | 进度API测试 | 🟡 中 | 测试进度查询API |
| INT_009 | 数据库集成测试 | 🟠 高 | 测试数据库集成功能 |

### 端到端测试 (E2E)

| ID | 名称 | 优先级 | 描述 |
|----|------|--------|------|
| E2E_001 | 完整页面加载测试 | 🔴 关键 | 测试所有页面的加载性能 |
| E2E_002 | 模块管理工作流测试 | 🟠 高 | 测试模块管理完整流程 |
| E2E_003 | 拉片上传流程测试 | 🟠 高 | 测试视频上传功能 |
| E2E_004 | 设置工作流测试 | 🟡 中 | 测试设置页面功能 |
| E2E_005 | 历史记录工作流测试 | 🟡 中 | 测试历史记录完整流程 |
| E2E_006 | 并发请求测试 | 🟡 中 | 测试系统并发处理能力 |
| E2E_007 | 错误处理测试 | 🟡 中 | 测试错误处理机制 |
| E2E_008 | 性能基准测试 | 🟢 低 | 测试系统性能基准 |

## 扩展测试用例

### 添加新的单元测试

```python
# tests/test_unit.py

class NewUnitTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="UNIT_011",
            test_name="新单元测试",
            test_type=TestType.UNIT,
            priority=TestPriority.MEDIUM
        )
    
    def setup(self) -> bool:
        # 初始化测试环境
        return True
    
    def execute(self) -> bool:
        # 执行测试逻辑
        # 返回 True 表示通过，False 表示失败
        return True
    
    def teardown(self) -> bool:
        # 清理测试环境
        return True


def register_unit_tests():
    registry = TestRegistry()
    # ... 其他注册
    registry.register(NewUnitTest())
```

### 添加新的集成测试

```python
# tests/test_integration.py

class NewIntegrationTest(IntegrationTestBase):
    def __init__(self):
        super().__init__(
            test_id="INT_010",
            test_name="新集成测试",
            priority=TestPriority.HIGH
        )
    
    def setup(self) -> bool:
        if not self.check_server_running():
            self.result.error_message = "服务器未运行"
            return False
        return True
    
    def execute(self) -> bool:
        # 使用 self.base_url 进行API测试
        response = requests.get(f"{self.base_url}/api/endpoint")
        return response.status_code == 200
    
    def teardown(self) -> bool:
        return True
```

## 测试报告

### 报告格式

测试完成后会在 `test_reports/` 目录生成以下报告：

- **JSON报告**: 机器可读，便于集成到CI/CD
- **HTML报告**: 可视化报告，便于人工查看
- **Markdown报告**: 文本格式，便于版本控制

### 报告内容

每个报告包含：

- 测试概览（总数、通过、失败、错误、跳过）
- 通过率统计
- 执行时间
- 每个测试用例的详细结果
- 错误信息和堆栈跟踪
- 系统信息（OS、Python版本、内存、磁盘等）

## 环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| TEST_BASE_URL | http://localhost:5000 | 测试服务器地址 |
| TEST_ENV | development | 测试环境 |

## 最佳实践

1. **开发前**: 运行快速检查确保基本功能正常
2. **提交前**: 运行完整测试确保没有引入回归问题
3. **部署前**: 运行所有测试并在生产环境进行冒烟测试
4. **日常维护**: 设置定时任务定期检查系统状态

## 故障排查

### 测试失败常见原因

1. **服务器未启动**: 确保Flask服务正在运行
2. **数据库连接失败**: 检查数据库文件是否存在
3. **环境变量未设置**: 检查.env文件配置
4. **依赖缺失**: 运行 `pip install -r requirements.txt`

### 调试模式

```bash
# 查看详细日志
python tests/run_tests.py --test-id UNIT_001
```

## 依赖

```
requests>=2.28.0
psutil>=5.9.0
schedule>=1.2.0
```

## 许可证

MIT License
