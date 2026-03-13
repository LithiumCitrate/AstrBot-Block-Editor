"""
BlockCompiler - 编译器主入口
"""

import json
from pathlib import Path
from typing import Any

from .analyzer import WorkflowAnalyzer
from .generator import CodeGenerator
from .parser import WorkflowParser


class BlockCompiler:
    """块编译器"""

    def __init__(self, blocks_path: str | Path | None = None):
        """
        初始化编译器

        Args:
            blocks_path: 块定义文件路径
        """
        self.parser = WorkflowParser()
        self.analyzer = WorkflowAnalyzer()
        self.generator = CodeGenerator()

        # 加载块定义
        if blocks_path:
            self.load_blocks(blocks_path)

    def load_blocks(self, path: str | Path) -> None:
        """加载块定义"""
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        blocks = data.get("blocks", {})
        self.parser.block_definitions = blocks
        self.analyzer.block_definitions = blocks
        self.generator.block_definitions = blocks

    def compile_file(self, workflow_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
        """
        编译工作流文件

        Args:
            workflow_path: 工作流JSON文件路径
            output_dir: 输出目录

        Returns:
            编译结果信息
        """
        workflow_path = Path(workflow_path)
        output_dir = Path(output_dir)

        # 1. 解析
        ast = self.parser.parse_file(workflow_path)

        # 2. 验证
        if not self.parser.validate(ast):
            return {
                "success": False,
                "errors": self.parser.errors,
                "warnings": self.parser.warnings,
            }

        # 3. 语义分析
        if not self.analyzer.analyze(ast):
            return {
                "success": False,
                "errors": self.analyzer.errors,
                "warnings": self.analyzer.warnings,
            }

        # 4. 代码生成
        files = self.generator.generate(ast)

        # 5. 写入文件
        plugin_dir = output_dir / ast.metadata.name
        plugin_dir.mkdir(parents=True, exist_ok=True)

        for filename, content in files.items():
            if content:  # 只写入非空文件
                file_path = plugin_dir / filename
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

        return {
            "success": True,
            "output_dir": str(plugin_dir),
            "files": list(files.keys()),
            "errors": self.parser.errors + self.analyzer.errors,
            "warnings": self.parser.warnings + self.analyzer.warnings,
        }

    def compile_string(self, workflow_json: str) -> dict[str, Any]:
        """
        编译工作流JSON字符串

        Args:
            workflow_json: 工作流JSON字符串

        Returns:
            编译结果信息（包含生成的代码）
        """
        data = json.loads(workflow_json)

        # 1. 解析
        ast = self.parser.parse(data)

        # 2. 验证
        validation_result = self.parser.validate(ast)

        # 3. 语义分析
        analysis_result = self.analyzer.analyze(ast)

        # 4. 代码生成
        files = self.generator.generate(ast)

        return {
            "success": validation_result and analysis_result,
            "files": files,
            "errors": self.parser.errors + self.analyzer.errors,
            "warnings": self.parser.warnings + self.analyzer.warnings,
        }

    def compile_to_string(self, workflow_path: str | Path) -> dict[str, str]:
        """
        编译工作流文件并返回代码字符串

        Args:
            workflow_path: 工作流JSON文件路径

        Returns:
            文件名到代码的映射
        """
        ast = self.parser.parse_file(Path(workflow_path))
        return self.generator.generate(ast)
