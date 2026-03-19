"""
解析器测试
"""
import json

from compiler import WorkflowParser


class TestWorkflowParser:
    """工作流解析器测试"""

    def test_parse_metadata(self, sample_workflow):
        """测试元数据解析"""
        parser = WorkflowParser()
        ast = parser.parse(sample_workflow)

        assert ast.metadata.name == "test_plugin"
        assert ast.metadata.author == "test_user"
        assert ast.metadata.version == "1.0.0"
        assert ast.metadata.description == "测试插件"

    def test_parse_handlers(self, sample_workflow):
        """测试 Handler 解析"""
        parser = WorkflowParser()
        ast = parser.parse(sample_workflow)

        assert len(ast.handlers) == 1
        handler = ast.handlers[0]

        assert handler.id == "handler_1"
        assert handler.name == "hello_handler"
        assert handler.trigger.block_type == "trigger.command"
        assert handler.trigger.params["command"] == "hello"
        assert len(handler.flow) == 1

    def test_parse_flow_blocks(self, sample_workflow):
        """测试流程块解析"""
        parser = WorkflowParser()
        ast = parser.parse(sample_workflow)

        block = ast.handlers[0].flow[0]
        assert block.id == "block_1"
        assert block.block_type == "action.reply_text"
        assert block.params["text"] == "你好！"

    def test_parse_variables(self, complex_workflow):
        """测试变量解析"""
        parser = WorkflowParser()
        ast = parser.parse(complex_workflow)

        assert len(ast.variables) == 1
        var = ast.variables[0]
        assert var.name == "counter"
        assert var.var_type == "int"
        assert var.default == 0

    def test_parse_branches(self, complex_workflow):
        """测试分支解析"""
        parser = WorkflowParser()
        ast = parser.parse(complex_workflow)

        block = ast.handlers[0].flow[0]
        assert block.block_type == "logic.if"
        assert "true" in block.branches
        assert "false" in block.branches
        assert len(block.branches["true"]) == 1
        assert len(block.branches["false"]) == 1

    def test_validate_valid_workflow(self, sample_workflow):
        """测试有效工作流验证"""
        parser = WorkflowParser()
        ast = parser.parse(sample_workflow)
        assert parser.validate(ast) is True
        assert len(parser.errors) == 0

    def test_validate_invalid_plugin_name(self):
        """测试无效插件名验证"""
        parser = WorkflowParser()
        ast = parser.parse({
            "metadata": {
                "name": "123-invalid",  # 以数字开头
                "author": "test",
                "description": "",
                "version": "1.0.0"
            },
            "handlers": []
        })
        assert parser.validate(ast) is False
        assert any("无效的插件名" in e for e in parser.errors)

    def test_validate_missing_trigger(self):
        """测试缺少触发器"""
        parser = WorkflowParser()
        ast = parser.parse({
            "metadata": {
                "name": "test",
                "author": "test",
                "description": "",
                "version": "1.0.0"
            },
            "handlers": [
                {"id": "h1", "name": "test", "trigger": {}, "flow": []}
            ]
        })
        assert parser.validate(ast) is False

    def test_load_block_definitions(self, blocks_path):
        """测试加载块定义"""
        parser = WorkflowParser()
        parser.load_block_definitions(blocks_path)

        assert len(parser.block_definitions) > 0
        assert "trigger.command" in parser.block_definitions
        assert "action.reply_text" in parser.block_definitions

    def test_parse_file(self, tmp_path, sample_workflow):
        """测试从文件解析"""
        workflow_file = tmp_path / "test.json"
        workflow_file.write_text(json.dumps(sample_workflow, ensure_ascii=False), encoding="utf-8")

        parser = WorkflowParser()
        ast = parser.parse_file(workflow_file)

        assert ast.metadata.name == "test_plugin"
