"""
工作流解析器 - 解析workflow.json并构建AST
"""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class BlockInstance:
    """块实例"""
    id: str
    block_type: str
    params: dict[str, Any] = field(default_factory=dict)
    inputs: dict[str, Any] = field(default_factory=dict)
    branches: dict[str, list["BlockInstance"]] = field(default_factory=dict)


@dataclass
class TriggerConfig:
    """触发器配置"""
    block_type: str
    params: dict[str, Any] = field(default_factory=dict)
    filters: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class HandlerDefinition:
    """Handler定义"""
    id: str
    name: str
    description: str
    trigger: TriggerConfig
    flow: list[BlockInstance] = field(default_factory=list)


@dataclass
class VariableDefinition:
    """变量定义"""
    name: str
    var_type: str
    default: Any = None
    persistent: bool = False
    description: str = ""


@dataclass
class ConfigItem:
    """配置项"""
    name: str
    item_type: str
    description: str
    default: Any = None
    hint: str = ""
    options: list[str] = field(default_factory=list)


@dataclass
class WorkflowMetadata:
    """工作流元数据"""
    name: str
    author: str
    description: str
    version: str
    display_name: str = ""
    repo: str = ""
    logo: str = ""


@dataclass
class WorkflowAST:
    """工作流抽象语法树"""
    metadata: WorkflowMetadata
    handlers: list[HandlerDefinition] = field(default_factory=list)
    variables: list[VariableDefinition] = field(default_factory=list)
    config_items: list[ConfigItem] = field(default_factory=list)
    imports: list[dict[str, Any]] = field(default_factory=list)
    init_code: str = ""
    terminate_code: str = ""


class WorkflowParser:
    """工作流解析器"""

    def __init__(self, block_definitions: dict[str, Any] | None = None):
        self.block_definitions = block_definitions or {}
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def load_block_definitions(self, path: str | Path) -> None:
        """加载块定义"""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            self.block_definitions = data.get("blocks", {})

    def parse_file(self, path: str | Path) -> WorkflowAST:
        """解析工作流文件"""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return self.parse(data)

    def parse(self, data: dict[str, Any]) -> WorkflowAST:
        """解析工作流数据"""
        self.errors = []
        self.warnings = []

        # 解析元数据
        metadata = self._parse_metadata(data.get("metadata", {}))

        # 解析变量
        variables = [self._parse_variable(v) for v in data.get("variables", [])]

        # 解析配置
        config_items = [self._parse_config_item(c) for c in data.get("config", {}).get("items", [])]

        # 解析Handler
        handlers = [self._parse_handler(h) for h in data.get("handlers", [])]

        # 解析导入
        imports = data.get("imports", [])

        return WorkflowAST(
            metadata=metadata,
            handlers=handlers,
            variables=variables,
            config_items=config_items,
            imports=imports,
            init_code=data.get("init_code", ""),
            terminate_code=data.get("terminate_code", "")
        )

    def _parse_metadata(self, data: dict[str, Any]) -> WorkflowMetadata:
        """解析元数据"""
        required = ["name", "author", "description", "version"]
        for field_name in required:
            if field_name not in data:
                self.errors.append(f"缺少必需的元数据字段: {field_name}")

        return WorkflowMetadata(
            name=data.get("name", "unnamed"),
            author=data.get("author", "unknown"),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            display_name=data.get("display_name", data.get("name", "")),
            repo=data.get("repo", ""),
            logo=data.get("logo", "")
        )

    def _parse_variable(self, data: dict[str, Any]) -> VariableDefinition:
        """解析变量定义"""
        return VariableDefinition(
            name=data.get("name", ""),
            var_type=data.get("type", "string"),
            default=data.get("default"),
            persistent=data.get("persistent", False),
            description=data.get("description", "")
        )

    def _parse_config_item(self, data: dict[str, Any]) -> ConfigItem:
        """解析配置项"""
        return ConfigItem(
            name=data.get("name", ""),
            item_type=data.get("type", "string"),
            description=data.get("description", ""),
            default=data.get("default"),
            hint=data.get("hint", ""),
            options=data.get("options", [])
        )

    def _parse_handler(self, data: dict[str, Any]) -> HandlerDefinition:
        """解析Handler定义"""
        handler_id = data.get("id", "")
        handler_name = data.get("name", handler_id)

        # 解析触发器
        trigger_data = data.get("trigger", {})
        trigger = TriggerConfig(
            block_type=trigger_data.get("block", ""),
            params=trigger_data.get("params", {}),
            filters=trigger_data.get("filters", [])
        )

        # 解析流程
        flow = [self._parse_block_instance(b) for b in data.get("flow", [])]

        return HandlerDefinition(
            id=handler_id,
            name=handler_name,
            description=data.get("description", ""),
            trigger=trigger,
            flow=flow
        )

    def _parse_block_instance(self, data: dict[str, Any]) -> BlockInstance:
        """解析块实例"""
        block_id = data.get("id", "")
        block_type = data.get("block", "")

        # 验证块类型
        if block_type and block_type not in self.block_definitions:
            self.warnings.append(f"未知的块类型: {block_type} (id: {block_id})")

        # 解析分支
        branches = {}
        for branch_name, branch_blocks in data.get("branches", {}).items():
            branches[branch_name] = [self._parse_block_instance(b) for b in branch_blocks]

        return BlockInstance(
            id=block_id,
            block_type=block_type,
            params=data.get("params", {}),
            inputs=data.get("inputs", {}),
            branches=branches
        )

    def validate(self, ast: WorkflowAST) -> bool:
        """验证AST"""
        valid = True

        # 验证插件名
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", ast.metadata.name):
            self.errors.append(f"无效的插件名: {ast.metadata.name}")
            valid = False

        # 验证版本号
        if not re.match(r"^\d+\.\d+\.\d+$", ast.metadata.version):
            self.warnings.append(f"版本号格式不规范: {ast.metadata.version}")

        # 验证Handler
        handler_ids = set()
        for handler in ast.handlers:
            if handler.id in handler_ids:
                self.errors.append(f"重复的Handler ID: {handler.id}")
                valid = False
            handler_ids.add(handler.id)
            
            if not handler.trigger.block_type:
                self.errors.append(f"Handler {handler.id} 缺少触发器")
                valid = False
        
        return valid and len(self.errors) == 0
