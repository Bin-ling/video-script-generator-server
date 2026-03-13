"""
分析功能测试模块
测试大模型分析、视频分析、图片分析、文字分析、拉片分析等功能
"""

import os
import sys
import json
import time
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.system_test_framework import (
    BaseTest, TestStatus, TestType, TestPriority, TestRegistry
)


class LLMServiceTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="ANALYSIS_001",
            test_name="大模型服务测试",
            test_type=TestType.UNIT,
            priority=TestPriority.CRITICAL
        )
    
    def setup(self) -> bool:
        try:
            from app.services.analysis_service import llm, init_llm
            self.llm = llm
            self.init_llm = init_llm
            return True
        except Exception as e:
            self.result.error_message = f"导入LLM服务失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            if self.llm is None:
                self.result.details['llm_status'] = '未初始化'
                self.result.details['message'] = '请检查.env文件中的API_KEY配置'
                self.result.status = TestStatus.SKIPPED
                return True
            
            self.result.details['llm_status'] = '已初始化'
            self.result.details['llm_type'] = type(self.llm).__name__
            
            return True
        except Exception as e:
            self.result.error_message = f"LLM服务测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class LLMTextAnalysisTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="ANALYSIS_002",
            test_name="大模型文本分析测试",
            test_type=TestType.INTEGRATION,
            priority=TestPriority.HIGH
        )
    
    def setup(self) -> bool:
        try:
            from app.services.analysis_service import llm
            self.llm = llm
            if self.llm is None:
                self.result.error_message = "LLM未初始化，跳过测试"
                self.result.status = TestStatus.SKIPPED
                return False
            return True
        except Exception as e:
            self.result.error_message = f"导入失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            test_text = "这是一个测试文本，用于验证大模型文本分析功能。"
            test_prompt = "请用一句话总结以下文本："
            
            start_time = time.time()
            result, saved_path = self.llm.analyze_text(test_text, test_prompt, save_result=False)
            duration = time.time() - start_time
            
            self.result.details['analysis_result'] = result[:200] if result else None
            self.result.details['duration'] = f"{duration:.2f}s"
            self.result.metrics['response_time'] = duration
            
            if result and len(result) > 0:
                return True
            else:
                self.result.error_message = "分析结果为空"
                return False
        except Exception as e:
            self.result.error_message = f"文本分析测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class LLMImageAnalysisTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="ANALYSIS_003",
            test_name="大模型图片分析测试",
            test_type=TestType.INTEGRATION,
            priority=TestPriority.HIGH
        )
        self.test_image = None
    
    def setup(self) -> bool:
        try:
            from app.services.analysis_service import llm
            self.llm = llm
            if self.llm is None:
                self.result.error_message = "LLM未初始化，跳过测试"
                self.result.status = TestStatus.SKIPPED
                return False
            
            test_frames_dir = os.path.join('output', 'test_frames')
            if os.path.exists(test_frames_dir):
                frames = [f for f in os.listdir(test_frames_dir) if f.endswith(('.jpg', '.png'))]
                if frames:
                    self.test_image = os.path.join(test_frames_dir, frames[0])
                    return True
            
            self.result.error_message = "没有找到测试图片，跳过测试"
            self.result.status = TestStatus.SKIPPED
            return False
        except Exception as e:
            self.result.error_message = f"导入失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            test_prompt = "请描述这张图片的内容："
            
            start_time = time.time()
            result, saved_path = self.llm.analyze_image(self.test_image, test_prompt, save_result=False)
            duration = time.time() - start_time
            
            self.result.details['image_path'] = self.test_image
            self.result.details['analysis_result'] = result[:200] if result else None
            self.result.details['duration'] = f"{duration:.2f}s"
            self.result.metrics['response_time'] = duration
            
            if result and len(result) > 0:
                return True
            else:
                self.result.error_message = "分析结果为空"
                return False
        except Exception as e:
            self.result.error_message = f"图片分析测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class LLMVideoAnalysisTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="ANALYSIS_004",
            test_name="大模型视频分析测试",
            test_type=TestType.INTEGRATION,
            priority=TestPriority.HIGH
        )
        self.test_video = None
    
    def setup(self) -> bool:
        try:
            from app.services.analysis_service import llm
            self.llm = llm
            if self.llm is None:
                self.result.error_message = "LLM未初始化，跳过测试"
                self.result.status = TestStatus.SKIPPED
                return False
            
            test_videos = []
            output_dir = 'output'
            if os.path.exists(output_dir):
                for root, dirs, files in os.walk(output_dir):
                    for f in files:
                        if f.endswith('.mp4'):
                            test_videos.append(os.path.join(root, f))
            
            if test_videos:
                self.test_video = test_videos[0]
                return True
            
            self.result.error_message = "没有找到测试视频，跳过测试"
            self.result.status = TestStatus.SKIPPED
            return False
        except Exception as e:
            self.result.error_message = f"导入失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            test_prompt = "请分析这个视频的内容："
            
            start_time = time.time()
            result, saved_path = self.llm.analyze_video_directly(self.test_video, test_prompt, save_result=False)
            duration = time.time() - start_time
            
            self.result.details['video_path'] = self.test_video
            self.result.details['analysis_result'] = result[:200] if result else None
            self.result.details['duration'] = f"{duration:.2f}s"
            self.result.metrics['response_time'] = duration
            
            if result and len(result) > 0:
                return True
            else:
                self.result.error_message = "分析结果为空"
                return False
        except Exception as e:
            self.result.error_message = f"视频分析测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class VideoProcessorAnalysisTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="ANALYSIS_005",
            test_name="视频处理器分析测试",
            test_type=TestType.UNIT,
            priority=TestPriority.HIGH
        )
        self.test_video = None
    
    def setup(self) -> bool:
        try:
            from modules.video_processor.processor import get_video_info, extract_frames
            self.get_video_info = get_video_info
            self.extract_frames = extract_frames
            
            test_videos = []
            output_dir = 'output'
            if os.path.exists(output_dir):
                for root, dirs, files in os.walk(output_dir):
                    for f in files:
                        if f.endswith('.mp4'):
                            test_videos.append(os.path.join(root, f))
            
            if test_videos:
                self.test_video = test_videos[0]
                return True
            
            self.result.error_message = "没有找到测试视频"
            self.result.status = TestStatus.SKIPPED
            return False
        except Exception as e:
            self.result.error_message = f"导入失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            info = self.get_video_info(self.test_video)
            
            self.result.details['video_info'] = {
                'duration': info.get('duration', 0),
                'width': info.get('width', 0),
                'height': info.get('height', 0),
                'fps': info.get('fps', 0)
            }
            
            if info.get('duration', 0) > 0:
                return True
            else:
                self.result.error_message = "无法获取视频信息"
                return False
        except Exception as e:
            self.result.error_message = f"视频处理器测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class FrameExtractionTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="ANALYSIS_006",
            test_name="关键帧提取测试",
            test_type=TestType.UNIT,
            priority=TestPriority.HIGH
        )
        self.test_video = None
        self.output_dir = None
    
    def setup(self) -> bool:
        try:
            from modules.video_processor.processor import extract_frames
            self.extract_frames = extract_frames
            
            test_videos = []
            output_dir = 'output'
            if os.path.exists(output_dir):
                for root, dirs, files in os.walk(output_dir):
                    for f in files:
                        if f.endswith('.mp4'):
                            test_videos.append(os.path.join(root, f))
            
            if test_videos:
                self.test_video = test_videos[0]
                self.output_dir = tempfile.mkdtemp()
                return True
            
            self.result.error_message = "没有找到测试视频"
            self.result.status = TestStatus.SKIPPED
            return False
        except Exception as e:
            self.result.error_message = f"导入失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            frames = self.extract_frames(
                self.test_video, 
                interval=5, 
                max_frames=5, 
                output_dir=self.output_dir
            )
            
            self.result.details['frames_count'] = len(frames)
            self.result.details['frames'] = [os.path.basename(f) for f in frames[:3]]
            
            if len(frames) > 0:
                return True
            else:
                self.result.error_message = "没有提取到关键帧"
                return False
        except Exception as e:
            self.result.error_message = f"关键帧提取测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        if self.output_dir and os.path.exists(self.output_dir):
            import shutil
            shutil.rmtree(self.output_dir, ignore_errors=True)
        return True


class LapianAnalysisTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="ANALYSIS_007",
            test_name="拉片分析测试",
            test_type=TestType.INTEGRATION,
            priority=TestPriority.HIGH
        )
    
    def setup(self) -> bool:
        try:
            from modules.lapian.main import VideoLapianTool
            self.VideoLapianTool = VideoLapianTool
            return True
        except Exception as e:
            self.result.error_message = f"导入拉片模块失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            tool = self.VideoLapianTool()
            
            self.result.details['tool_initialized'] = True
            self.result.details['tool_type'] = type(tool).__name__
            
            return True
        except Exception as e:
            self.result.error_message = f"拉片分析测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class LapianShotAnalyzerTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="ANALYSIS_008",
            test_name="拉片镜头分析器测试",
            test_type=TestType.UNIT,
            priority=TestPriority.HIGH
        )
    
    def setup(self) -> bool:
        try:
            from modules.lapian.shot_analyzer import ShotAnalyzer
            self.ShotAnalyzer = ShotAnalyzer
            return True
        except Exception as e:
            self.result.error_message = f"导入镜头分析器失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            analyzer = self.ShotAnalyzer()
            
            self.result.details['analyzer_initialized'] = True
            self.result.details['analyzer_type'] = type(analyzer).__name__
            
            return True
        except Exception as e:
            self.result.error_message = f"镜头分析器测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class LapianReportGeneratorTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="ANALYSIS_009",
            test_name="拉片报告生成器测试",
            test_type=TestType.UNIT,
            priority=TestPriority.MEDIUM
        )
    
    def setup(self) -> bool:
        try:
            from modules.lapian.report_generator import ReportGenerator
            self.ReportGenerator = ReportGenerator
            return True
        except Exception as e:
            self.result.error_message = f"导入报告生成器失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            generator = self.ReportGenerator()
            
            self.result.details['generator_initialized'] = True
            self.result.details['generator_type'] = type(generator).__name__
            
            return True
        except Exception as e:
            self.result.error_message = f"报告生成器测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class FilePathSaveTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="ANALYSIS_010",
            test_name="文件路径保存测试",
            test_type=TestType.UNIT,
            priority=TestPriority.HIGH
        )
    
    def setup(self) -> bool:
        try:
            from modules.utils.file_utils import create_output_folder
            self.create_output_folder = create_output_folder
            return True
        except Exception as e:
            self.result.error_message = f"导入文件工具失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            test_desc = "test_video_analysis"
            output_dir = self.create_output_folder(test_desc)
            
            self.result.details['output_dir'] = output_dir
            self.result.details['dir_exists'] = os.path.exists(output_dir)
            self.result.details['is_absolute'] = os.path.isabs(output_dir)
            
            if os.path.exists(output_dir):
                test_file = os.path.join(output_dir, 'test.json')
                with open(test_file, 'w', encoding='utf-8') as f:
                    json.dump({'test': 'data'}, f)
                
                if os.path.exists(test_file):
                    os.remove(test_file)
                    return True
                else:
                    self.result.error_message = "无法在输出目录创建文件"
                    return False
            else:
                self.result.error_message = "输出目录不存在"
                return False
        except Exception as e:
            self.result.error_message = f"文件路径保存测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class OutputDirectoryStructureTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="ANALYSIS_011",
            test_name="输出目录结构测试",
            test_type=TestType.UNIT,
            priority=TestPriority.MEDIUM
        )
    
    def setup(self) -> bool:
        return True
    
    def execute(self) -> bool:
        try:
            output_dir = 'output'
            if not os.path.exists(output_dir):
                self.result.details['output_exists'] = False
                self.result.details['message'] = 'output目录不存在，将在首次运行时创建'
                return True
            
            self.result.details['output_exists'] = True
            
            subdirs = []
            files_count = 0
            for item in os.listdir(output_dir):
                item_path = os.path.join(output_dir, item)
                if os.path.isdir(item_path):
                    subdirs.append(item)
                else:
                    files_count += 1
            
            self.result.details['subdirs_count'] = len(subdirs)
            self.result.details['subdirs_sample'] = subdirs[:5]
            self.result.details['files_count'] = files_count
            
            expected_subdirs = ['lapian', 'frames']
            for subdir in expected_subdirs:
                subdir_path = os.path.join(output_dir, subdir)
                self.result.details[f'{subdir}_exists'] = os.path.exists(subdir_path)
            
            return True
        except Exception as e:
            self.result.error_message = f"输出目录结构测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class AnalysisResultSaveTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="ANALYSIS_012",
            test_name="分析结果保存测试",
            test_type=TestType.INTEGRATION,
            priority=TestPriority.HIGH
        )
        self.test_dir = None
    
    def setup(self) -> bool:
        try:
            self.test_dir = tempfile.mkdtemp()
            return True
        except Exception as e:
            self.result.error_message = f"创建测试目录失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            test_files = {
                'content_analysis.json': {'result': '内容分析结果'},
                'data_analysis.json': {'result': '数据分析结果'},
                'analysis_report.json': {'modules': {}, 'metadata': {}}
            }
            
            saved_files = []
            for filename, content in test_files.items():
                filepath = os.path.join(self.test_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(content, f, ensure_ascii=False)
                saved_files.append(filename)
            
            self.result.details['saved_files'] = saved_files
            self.result.details['all_saved'] = len(saved_files) == len(test_files)
            
            for filename in test_files:
                filepath = os.path.join(self.test_dir, filename)
                if not os.path.exists(filepath):
                    self.result.error_message = f"文件保存失败: {filename}"
                    return False
            
            return True
        except Exception as e:
            self.result.error_message = f"分析结果保存测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        if self.test_dir and os.path.exists(self.test_dir):
            import shutil
            shutil.rmtree(self.test_dir, ignore_errors=True)
        return True


class ModuleAnalysisIntegrationTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="ANALYSIS_013",
            test_name="模块分析集成测试",
            test_type=TestType.INTEGRATION,
            priority=TestPriority.HIGH
        )
    
    def setup(self) -> bool:
        try:
            from modules.analysis.modules.manager import module_manager
            from app.services.analysis_service import llm
            self.module_manager = module_manager
            self.llm = llm
            return True
        except Exception as e:
            self.result.error_message = f"导入模块管理器失败: {str(e)}"
            return False
    
    def execute(self) -> bool:
        try:
            modules = self.module_manager.get_all_modules()
            
            self.result.details['modules_count'] = len(modules)
            
            enabled_modules = []
            disabled_modules = []
            
            for module_id, module in modules.items():
                if module.is_enabled():
                    enabled_modules.append(module_id)
                else:
                    disabled_modules.append(module_id)
            
            self.result.details['enabled_modules'] = enabled_modules
            self.result.details['disabled_modules'] = disabled_modules
            self.result.details['llm_available'] = self.llm is not None
            
            return True
        except Exception as e:
            self.result.error_message = f"模块分析集成测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


class DatabaseSaveTest(BaseTest):
    def __init__(self):
        super().__init__(
            test_id="ANALYSIS_014",
            test_name="数据库保存测试",
            test_type=TestType.INTEGRATION,
            priority=TestPriority.HIGH
        )
    
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
            
            if analyses:
                sample = analyses[0]
                self.result.details['sample_fields'] = list(sample.keys())
                self.result.details['has_output_dir'] = 'output_dir' in sample
            
            return True
        except Exception as e:
            self.result.error_message = f"数据库保存测试失败: {str(e)}"
            return False
    
    def teardown(self) -> bool:
        return True


def register_analysis_tests(registry=None):
    if registry is None:
        registry = TestRegistry()
    registry.register(LLMServiceTest())
    registry.register(LLMTextAnalysisTest())
    registry.register(LLMImageAnalysisTest())
    registry.register(LLMVideoAnalysisTest())
    registry.register(VideoProcessorAnalysisTest())
    registry.register(FrameExtractionTest())
    registry.register(LapianAnalysisTest())
    registry.register(LapianShotAnalyzerTest())
    registry.register(LapianReportGeneratorTest())
    registry.register(FilePathSaveTest())
    registry.register(OutputDirectoryStructureTest())
    registry.register(AnalysisResultSaveTest())
    registry.register(ModuleAnalysisIntegrationTest())
    registry.register(DatabaseSaveTest())
    return registry


if __name__ == "__main__":
    register_analysis_tests()
    registry = TestRegistry()
    tests = registry.get_all_tests()
    
    print(f"共注册 {len(tests)} 个分析功能测试")
    for test in tests:
        print(f"  - {test.test_id}: {test.test_name}")
