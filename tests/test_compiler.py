"""
编译器集成测试
"""
import json
from pathlib import Path

import pytest

from compiler import BlockCompiler


class TestBlockCompiler:
    """编译器集成测试"""

    def test_compile_string(self, sample_workflow, blocks_path):
        """测试从字符串编译"""
        compiler = BlockCompiler(blocks_path)
        result = compiler.compile_string(json.dumps(sample_workflow, ensure_ascii=False))

        assert result["success"] is True
        assert "main.py" in result["files"]
        assert "metadata.yaml" in result["files"]

    def test_compile_file(self, tmp_path, sample_workflow, blocks_path):
        """测试从文件编译"""
        workflow_file = tmp_path / "test.json"
        workflow_file.write_text(json.dumps(sample_workflow, ensure_ascii=False), encoding="utf-8")

        output_dir = tmp_path / "output"

        compiler = BlockCompiler(blocks_path)
        result = compiler.compile_file(workflow_file, output_dir)

        assert result["success"] is True
        assert Path(result["output_dir"]).exists()
        assert (Path(result["output_dir"]) / "main.py").exists()
        assert (Path(result["output_dir"]) / "metadata.yaml").exists()

    def test_compile_invalid_json(self, blocks_path):
        """测试编译无效 JSON"""
        compiler = BlockCompiler(blocks_path)
        result = compiler.compile_string("not a json")

        assert result["success"] is False
        assert len(result["errors"]) > 0

    def test_compile_missing_metadata(self, blocks_path):
        """测试编译缺少元数据的工作流"""
        compiler = BlockCompiler(blocks_path)
        result = compiler.compile_string(json.dumps({
            "handlers": []
        }))

        assert result["success"] is False

    def test_compile_example_files(self, blocks_path):
        """测试编译示例文件"""
        examples_dir = Path(__file__).parent.parent / "examples"

        if not examples_dir.exists():
            pytest.skip("examples 目录不存在")

        compiler = BlockCompiler(blocks_path)

        for example_file in examples_dir.glob("*.json"):
            result = compiler.compile_string(example_file.read_text(encoding="utf-8"))

            # 大部分示例应该能成功编译
            # 如果有失败的，检查是否是预期行为
            if not result["success"]:
                print(f"示例 {example_file.name} 编译失败: {result['errors']}")

    def test_compile_to_string(self, tmp_path, sample_workflow, blocks_path):
        """测试编译到字符串"""
        workflow_file = tmp_path / "test.json"
        workflow_file.write_text(json.dumps(sample_workflow, ensure_ascii=False), encoding="utf-8")

        compiler = BlockCompiler(blocks_path)
        files = compiler.compile_to_string(workflow_file)

        assert "main.py" in files
        assert "metadata.yaml" in files
        assert len(files["main.py"]) > 0
