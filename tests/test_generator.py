"""
代码生成器测试
"""
import pytest

from compiler import WorkflowParser, WorkflowAnalyzer, CodeGenerator


class TestCodeGenerator:
    """代码生成器测试"""
    
    def test_generate_main_py(self, sample_workflow, blocks_path):
        """测试生成 main.py"""
        parser = WorkflowParser()
        parser.load_block_definitions(blocks_path)
        ast = parser.parse(sample_workflow)
        
        generator = CodeGenerator(parser.block_definitions)
        files = generator.generate(ast)
        
        assert "main.py" in files
        assert files["main.py"] != ""
    
    def test_generate_metadata_yaml(self, sample_workflow, blocks_path):
        """测试生成 metadata.yaml"""
        parser = WorkflowParser()
        parser.load_block_definitions(blocks_path)
        ast = parser.parse(sample_workflow)
        
        generator = CodeGenerator(parser.block_definitions)
        files = generator.generate(ast)
        
        assert "metadata.yaml" in files
        assert "name: test_plugin" in files["metadata.yaml"]
        assert "author: test_user" in files["metadata.yaml"]
        assert "version: 1.0.0" in files["metadata.yaml"]
    
    def test_generate_imports(self, sample_workflow, blocks_path):
        """测试生成导入语句"""
        parser = WorkflowParser()
        parser.load_block_definitions(blocks_path)
        ast = parser.parse(sample_workflow)
        
        generator = CodeGenerator(parser.block_definitions)
        files = generator.generate(ast)
        
        main_py = files["main.py"]
        assert "from astrbot.api import star" in main_py
        assert "from astrbot.api.event import AstrMessageEvent, filter" in main_py
    
    def test_generate_handler_decorator(self, sample_workflow, blocks_path):
        """测试生成 Handler 装饰器"""
        parser = WorkflowParser()
        parser.load_block_definitions(blocks_path)
        ast = parser.parse(sample_workflow)
        
        generator = CodeGenerator(parser.block_definitions)
        files = generator.generate(ast)
        
        main_py = files["main.py"]
        assert '@filter.command("hello")' in main_py
    
    def test_generate_reply_text(self, sample_workflow, blocks_path):
        """测试生成回复文本代码"""
        parser = WorkflowParser()
        parser.load_block_definitions(blocks_path)
        ast = parser.parse(sample_workflow)
        
        generator = CodeGenerator(parser.block_definitions)
        files = generator.generate(ast)
        
        main_py = files["main.py"]
        assert 'yield event.plain_result("你好！")' in main_py
    
    def test_generate_condition_branch(self, complex_workflow, blocks_path):
        """测试生成条件分支代码"""
        parser = WorkflowParser()
        parser.load_block_definitions(blocks_path)
        ast = parser.parse(complex_workflow)
        
        generator = CodeGenerator(parser.block_definitions)
        files = generator.generate(ast)
        
        main_py = files["main.py"]
        assert "if event.get_sender_id() == '123456':" in main_py
        assert "else:" in main_py
    
    def test_generate_class_name(self):
        """测试类名转换"""
        generator = CodeGenerator()
        
        assert generator._to_class_name("test_plugin") == "TestPlugin"
        assert generator._to_class_name("my_awesome_plugin") == "MyAwesomePlugin"
        assert generator._to_class_name("simple") == "Simple"
    
    def test_generate_template_string(self):
        """测试模板字符串渲染"""
        generator = CodeGenerator()
        
        # 无变量
        result = generator._render_template("Hello")
        assert result == '"Hello"'
        
        # 包含内置变量
        result = generator._render_template("Hello, {sender_name}!")
        assert "f\"" in result
        assert "event.get_sender_name()" in result
    
    def test_generate_variables_init(self, complex_workflow, blocks_path):
        """测试变量初始化"""
        parser = WorkflowParser()
        parser.load_block_definitions(blocks_path)
        ast = parser.parse(complex_workflow)
        
        generator = CodeGenerator(parser.block_definitions)
        files = generator.generate(ast)
        
        main_py = files["main.py"]
        assert "self.counter = 0" in main_py
    
    def test_generate_http_request(self, blocks_path):
        """测试生成 HTTP 请求代码"""
        parser = WorkflowParser()
        parser.load_block_definitions(blocks_path)
        ast = parser.parse({
            "metadata": {"name": "test", "author": "test", "description": "", "version": "1.0.0"},
            "handlers": [{
                "id": "h1",
                "name": "test",
                "trigger": {"block": "trigger.command", "params": {"command": "test"}},
                "flow": [{
                    "id": "b1",
                    "block": "action.http_request",
                    "params": {
                        "method": "GET",
                        "url": "https://api.example.com/data",
                        "save_to": "response"
                    }
                }]
            }]
        })
        
        generator = CodeGenerator(parser.block_definitions)
        files = generator.generate(ast)
        
        main_py = files["main.py"]
        assert "import aiohttp" in main_py
        assert "aiohttp.ClientSession()" in main_py
    
    def test_generate_delay(self, blocks_path):
        """测试生成延迟代码"""
        parser = WorkflowParser()
        parser.load_block_definitions(blocks_path)
        ast = parser.parse({
            "metadata": {"name": "test", "author": "test", "description": "", "version": "1.0.0"},
            "handlers": [{
                "id": "h1",
                "name": "test",
                "trigger": {"block": "trigger.command", "params": {"command": "test"}},
                "flow": [{
                    "id": "b1",
                    "block": "action.delay",
                    "params": {"seconds": 5}
                }]
            }]
        })
        
        generator = CodeGenerator(parser.block_definitions)
        files = generator.generate(ast)
        
        main_py = files["main.py"]
        assert "await asyncio.sleep(5)" in main_py
