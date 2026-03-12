import unittest
import os
import tempfile
import json

class TestConfigManager(unittest.TestCase):
    
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
        self.temp_file.close()
        self.test_config_content = {
            "modules": {
                "content_analysis": {
                    "id": "content_analysis",
                    "name": "内容分析",
                    "type": "video_analysis",
                    "enabled": True,
                    "config": {
                        "input_prompt_template": "测试模板",
                        "output_keywords": ["关键词1", "关键词2"]
                    }
                }
            }
        }
        with open(self.temp_file.name, 'w', encoding='utf-8') as f:
            json.dump(self.test_config_content, f)
        
        from config_manager import ConfigManager
        self.config_manager = ConfigManager(self.temp_file.name)
    
    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)
    
    def test_get_module_config(self):
        config = self.config_manager.get_module_config('content_analysis')
        self.assertIsInstance(config, dict)
    
    def test_get_all_modules(self):
        modules = self.config_manager.get_all_modules()
        self.assertIsInstance(modules, dict)
        self.assertIn('content_analysis', modules)
    
    def test_get_analysis_module(self):
        module = self.config_manager.get_analysis_module('content_analysis')
        self.assertIsInstance(module, dict)
        self.assertEqual(module['name'], '内容分析')
    
    def test_update_analysis_module(self):
        new_config = {
            "id": "content_analysis",
            "name": "内容分析(更新)",
            "type": "video_analysis",
            "enabled": True,
            "config": {}
        }
        self.config_manager.update_analysis_module('content_analysis', new_config)
        module = self.config_manager.get_analysis_module('content_analysis')
        self.assertEqual(module['name'], '内容分析(更新)')
    
    def test_add_analysis_module(self):
        new_module = {
            "id": "test_module",
            "name": "测试模块",
            "type": "text_analysis",
            "enabled": True,
            "config": {}
        }
        self.config_manager.add_analysis_module('test_module', new_module)
        module = self.config_manager.get_analysis_module('test_module')
        self.assertEqual(module['name'], '测试模块')
    
    def test_remove_analysis_module(self):
        self.config_manager.remove_analysis_module('content_analysis')
        module = self.config_manager.get_analysis_module('content_analysis')
        self.assertEqual(module, {})
    
    def test_get_system_settings(self):
        settings = self.config_manager.get_system_settings()
        self.assertIsInstance(settings, dict)

class TestDatabase(unittest.TestCase):
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        from database import Database
        self.db = Database(self.temp_db.name)
    
    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)
    
    def test_insert_analysis(self):
        data = {
            'url': 'https://example.com/video',
            'title': '测试视频',
            'output_dir': 'output/test',
            'info': {'duration': 120},
            'stats': {'play': 1000},
            'content_ana': '测试分析结果'
        }
        record_id = self.db.insert_analysis(data)
        self.assertIsInstance(record_id, int)
    
    def test_get_all_analyses(self):
        analyses = self.db.get_all_analyses()
        self.assertIsInstance(analyses, list)
    
    def test_get_analysis_by_id(self):
        data = {
            'url': 'https://example.com/video',
            'title': '测试视频',
            'output_dir': 'output/test',
            'info': {'duration': 120},
            'stats': {'play': 1000}
        }
        record_id = self.db.insert_analysis(data)
        analysis = self.db.get_analysis_by_id(record_id)
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis['title'], '测试视频')

class TestLLM(unittest.TestCase):
    
    def test_chat_function(self):
        from llm import chat
        prompt = "你好，请回复'测试成功'"
        result = chat(prompt)
        self.assertIsInstance(result, str)

if __name__ == '__main__':
    unittest.main()
