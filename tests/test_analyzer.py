"""
语义分析器测试
"""

from compiler import WorkflowAnalyzer, WorkflowParser


class TestWorkflowAnalyzer:
    """工作流语义分析器测试"""

    def test_analyze_valid_workflow(self, sample_workflow, blocks_path):
        """测试有效工作流分析"""
        parser = WorkflowParser()
        parser.load_block_definitions(blocks_path)
        ast = parser.parse(sample_workflow)

        analyzer = WorkflowAnalyzer(parser.block_definitions)
        assert analyzer.analyze(ast) is True
        assert len(analyzer.errors) == 0

    def test_builtin_variables_registered(self, sample_workflow, blocks_path):
        """测试内置变量注册"""
        parser = WorkflowParser()
        parser.load_block_definitions(blocks_path)
        ast = parser.parse(sample_workflow)

        analyzer = WorkflowAnalyzer(parser.block_definitions)
        analyzer.analyze(ast)

        # 检查内置变量
        assert analyzer.symbol_table.lookup("sender_id") is not None
        assert analyzer.symbol_table.lookup("sender_name") is not None
        assert analyzer.symbol_table.lookup("message_str") is not None

    def test_template_variable_check(self, blocks_path):
        """测试模板变量检查"""
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
                    "block": "action.reply_text",
                    "params": {"text": "你好，{sender_name}！"}
                }]
            }]
        })

        analyzer = WorkflowAnalyzer(parser.block_definitions)
        analyzer.analyze(ast)

        # sender_name 是内置变量，不应有警告
        assert not any("sender_name" in w for w in analyzer.warnings)

    def test_undefined_variable_warning(self, blocks_path):
        """测试未定义变量警告"""
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
                    "block": "action.reply_text",
                    "params": {"text": "值: {undefined_var}"}
                }]
            }]
        })

        analyzer = WorkflowAnalyzer(parser.block_definitions)
        analyzer.analyze(ast)

        # 应该有未定义变量的警告
        assert any("undefined_var" in w for w in analyzer.warnings)

    def test_custom_variable_registration(self, blocks_path):
        """测试自定义变量注册"""
        parser = WorkflowParser()
        parser.load_block_definitions(blocks_path)
        ast = parser.parse({
            "metadata": {"name": "test", "author": "test", "description": "", "version": "1.0.0"},
            "variables": [{"name": "my_var", "type": "string", "default": ""}],
            "handlers": [{
                "id": "h1",
                "name": "test",
                "trigger": {"block": "trigger.command", "params": {"command": "test"}},
                "flow": []
            }]
        })

        analyzer = WorkflowAnalyzer(parser.block_definitions)
        analyzer.analyze(ast)

        sym = analyzer.symbol_table.lookup("my_var")
        assert sym is not None
        assert sym.symbol_type == "variable"
