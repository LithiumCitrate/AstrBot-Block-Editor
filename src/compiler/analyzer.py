"""
语义分析器 - 类型检查、变量引用检查、流程连接验证
"""
from dataclasses import dataclass
from typing import Any

from .parser import (
    WorkflowAST,
    HandlerDefinition,
    BlockInstance,
    VariableDefinition,
)


@dataclass
class Symbol:
    """符号表条目"""
    name: str
    symbol_type: str  # "variable", "param", "builtin"
    data_type: str
    scope: str  # "global", "handler", "block"
    source: str  # 定义来源


class SymbolTable:
    """符号表"""
    
    def __init__(self):
        self.symbols: dict[str, list[Symbol]] = {}
    
    def add(self, symbol: Symbol) -> None:
        if symbol.name not in self.symbols:
            self.symbols[symbol.name] = []
        self.symbols[symbol.name].append(symbol)
    
    def lookup(self, name: str, scope: str | None = None) -> Symbol | None:
        if name not in self.symbols:
            return None
        for sym in self.symbols[name]:
            if scope is None or sym.scope == scope or sym.scope == "global":
                return sym
        return self.symbols[name][0]  # 返回第一个匹配
    
    def get_all_in_scope(self, scope: str) -> list[Symbol]:
        result = []
        for syms in self.symbols.values():
            for sym in syms:
                if sym.scope == scope or sym.scope == "global":
                    result.append(sym)
        return result


class WorkflowAnalyzer:
    """工作流语义分析器"""
    
    # 内置变量映射
    BUILTIN_VARIABLES = {
        "message_str": ("string", "event.message_str"),
        "sender_id": ("string", "event.get_sender_id()"),
        "sender_name": ("string", "event.get_sender_name()"),
        "group_id": ("string", "event.get_group_id()"),
        "self_id": ("string", "event.get_self_id()"),
        "platform": ("string", "event.get_platform_name()"),
        "is_private": ("bool", "event.is_private_chat()"),
        "is_admin": ("bool", "event.is_admin()"),
    }
    
    def __init__(self, block_definitions: dict[str, Any] | None = None):
        self.block_definitions = block_definitions or {}
        self.symbol_table = SymbolTable()
        self.errors: list[str] = []
        self.warnings: list[str] = []
    
    def analyze(self, ast: WorkflowAST) -> bool:
        """分析AST"""
        self.errors = []
        self.warnings = []
        self.symbol_table = SymbolTable()
        
        # 1. 注册内置符号
        self._register_builtins()
        
        # 2. 注册全局变量
        for var in ast.variables:
            self._register_variable(var, "global")
        
        # 3. 分析每个Handler
        for handler in ast.handlers:
            self._analyze_handler(handler)
        
        return len(self.errors) == 0
    
    def _register_builtins(self) -> None:
        """注册内置符号"""
        for name, (data_type, source) in self.BUILTIN_VARIABLES.items():
            self.symbol_table.add(Symbol(
                name=name,
                symbol_type="builtin",
                data_type=data_type,
                scope="global",
                source=source
            ))
    
    def _register_variable(self, var: VariableDefinition, scope: str) -> None:
        """注册变量符号"""
        self.symbol_table.add(Symbol(
            name=var.name,
            symbol_type="variable",
            data_type=var.var_type,
            scope=scope,
            source=f"self.{var.name}"
        ))
    
    def _analyze_handler(self, handler: HandlerDefinition) -> None:
        """分析Handler"""
        handler_scope = f"handler_{handler.id}"
        
        # 分析触发器
        self._analyze_trigger(handler.trigger, handler_scope)
        
        # 分析流程块
        for block in handler.flow:
            self._analyze_block(block, handler_scope)
    
    def _analyze_trigger(self, trigger: Any, scope: str) -> None:
        """分析触发器"""
        block_def = self.block_definitions.get(trigger.block_type, {})
        params_def = block_def.get("params", {})
        
        # 检查必需参数
        for param_name, param_def in params_def.items():
            if param_def.get("required", False) and param_name not in trigger.params:
                self.errors.append(f"触发器 {trigger.block_type} 缺少必需参数: {param_name}")
        
        # 检查参数类型
        for param_name, param_value in trigger.params.items():
            if param_name in params_def:
                expected_type = params_def[param_name].get("type")
                if not self._check_type(param_value, expected_type):
                    self.warnings.append(
                        f"触发器 {trigger.block_type} 参数 {param_name} 类型不匹配: "
                        f"期望 {expected_type}, 实际 {type(param_value).__name__}"
                    )
    
    def _analyze_block(self, block: BlockInstance, scope: str) -> None:
        """分析块实例"""
        block_def = self.block_definitions.get(block.block_type, {})
        params_def = block_def.get("params", {})
        
        # 检查必需参数
        for param_name, param_def in params_def.items():
            if param_def.get("required", False) and param_name not in block.params:
                if param_def.get("default") is None:
                    self.errors.append(f"块 {block.block_type} (id: {block.id}) 缺少必需参数: {param_name}")
        
        # 检查模板变量引用
        for param_name, param_value in block.params.items():
            if isinstance(param_value, str):
                self._check_template_variables(param_value, scope, block.id)
        
        # 分析分支
        for branch_name, branch_blocks in block.branches.items():
            for branch_block in branch_blocks:
                self._analyze_block(branch_block, scope)
    
    def _check_template_variables(self, template: str, scope: str, block_id: str) -> None:
        """检查模板中的变量引用"""
        import re
        # 匹配 {variable} 格式
        pattern = r"\{(\w+)\}"
        matches = re.findall(pattern, template)
        
        for var_name in matches:
            sym = self.symbol_table.lookup(var_name, scope)
            if sym is None:
                self.warnings.append(
                    f"块 {block_id} 引用了未定义的变量: {var_name}"
                )
    
    def _check_type(self, value: Any, expected_type: str | None) -> bool:
        """检查类型匹配"""
        if expected_type is None:
            return True
        
        type_map = {
            "string": str,
            "number": (int, float),
            "int": int,
            "float": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        
        expected = type_map.get(expected_type)
        if expected is None:
            return True  # 未知类型，跳过检查
        
        return isinstance(value, expected)
    
    def get_codegen_context(self) -> dict[str, Any]:
        """获取代码生成所需的上下文"""
        return {
            "symbol_table": self.symbol_table,
            "builtin_variables": self.BUILTIN_VARIABLES,
        }
