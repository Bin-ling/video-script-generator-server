import unittest
import os
import tempfile
from config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    """测试配置管理器"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时配置文件
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        self.temp_file.close()
        self.config_manager = ConfigManager(self.temp_file.name)
    
    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)
    
    def test_load_default_config(self):
        """测试加载默认配置"""
        config = self.config_manager.config
        self.assertIn('analysis_modules', config)
        self.assertIn('multimodal_settings', config)
        self.assertIn('system_settings', config)
    
    def test_get_module_config(self):
        """测试获取模块配置"""
        content_config = self.config_manager.get_module_config('content_analysis')
        self.assertEqual(content_config['name'], '内容分析')
        self.assertEqual(content_config['analysis_type'], 'video_analysis')
    
    def test_get_all_modules(self):
        """测试获取所有模块"""
        modules = self.config_manager.get_all_modules()
        self.assertIsInstance(modules, dict)
        self.assertIn('content_analysis', modules)
        self.assertIn('data_analysis', modules)
    
    def test_get_multimodal_settings(self):
        """测试获取多模态设置"""
        settings = self.config_manager.get_multimodal_settings()
        self.assertIsInstance(settings, dict)
        self.assertIn('frame_interval', settings)
        self.assertIn('max_frames', settings)
    
    def test_get_system_settings(self):
        """测试获取系统设置"""
        settings = self.config_manager.get_system_settings()
        self.assertIsInstance(settings, dict)
        self.assertIn('max_file_size', settings)
        self.assertIn('thread_pool_size', settings)
    
    def test_add_module(self):
        """测试添加模块"""
        new_module = {
            "name": "测试模块",
            "analysis_type": "text_analysis",
            "input_keywords": ["测试"],
            "output_keywords": ["测试结果"],
            "use_multimodal": False
        }
        self.config_manager.add_module('test_module', new_module)
        test_config = self.config_manager.get_module_config('test_module')
        self.assertEqual(test_config['name'], '测试模块')
    
    def test_remove_module(self):
        """测试移除模块"""
        # 先添加一个测试模块
        new_module = {
            "name": "测试模块",
            "analysis_type": "text_analysis",
            "input_keywords": ["测试"],
            "output_keywords": ["测试结果"],
            "use_multimodal": False
        }
        self.config_manager.add_module('test_module', new_module)
        # 确认模块存在
        test_config = self.config_manager.get_module_config('test_module')
        self.assertEqual(test_config['name'], '测试模块')
        # 移除模块
        self.config_manager.remove_module('test_module')
        # 确认模块不存在
        test_config = self.config_manager.get_module_config('test_module')
        self.assertEqual(test_config, {})

if __name__ == '__main__':
    unittest.main()
