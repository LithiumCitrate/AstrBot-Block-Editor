"""
代码生成器 - 将AST转换为Python代码
"""
import re
from typing import Any
from pathlib import Path

from .parser import (
    WorkflowAST,
    HandlerDefinition,
    BlockInstance,
    VariableDefinition,
    ConfigItem,
)


class CodeGenerator:
    """代码生成器"""
    
    def __init__(self, block_definitions: dict[str, Any] | None = None):
        self.block_definitions = block_definitions or {}
        self.indent = "    "  # 4空格缩进
        self.indent_level = 0
        self.class_vars: set[str] = set()  # 类成员变量名集合
    
    def generate(self, ast: WorkflowAST) -> dict[str, str]:
        """生成所有文件"""
        return {
            "main.py": self._generate_main_py(ast),
            "metadata.yaml": self._generate_metadata_yaml(ast),
            "_conf_schema.json": self._generate_conf_schema(ast) if ast.config_items else "",
        }
    
    def _generate_main_py(self, ast: WorkflowAST) -> str:
        """生成main.py"""
        lines = []
        
        # 收集类成员变量
        self.class_vars = {var.name for var in ast.variables}
        
        # 1. 导入语句
        lines.extend(self._generate_imports(ast))
        lines.append("")
        
        # 2. 插件类
        lines.append(f"class {self._to_class_name(ast.metadata.name)}(star.Star):")
        lines.append(f'    """{ast.metadata.description}"""')
        lines.append("")
        
        # 3. __init__方法
        lines.extend(self._generate_init(ast))
        lines.append("")
        
        # 4. Handler方法
        for handler in ast.handlers:
            lines.extend(self._generate_handler(handler, ast))
            lines.append("")
        
        # 5. terminate方法
        lines.extend(self._generate_terminate(ast))
        
        return "\n".join(lines)
    
    def _generate_imports(self, ast: WorkflowAST) -> list[str]:
        """生成导入语句"""
        imports = [
            "from astrbot.api import star",
            "from astrbot.api.event import AstrMessageEvent, filter",
            "from astrbot.api import logger",
            "import asyncio",
            "import random",
            "from datetime import datetime",
        ]
        
        # 添加额外导入
        for imp in ast.imports:
            module = imp.get("module", "")
            items = imp.get("items", [])
            if items:
                imports.append(f"from {module} import {', '.join(items)}")
            elif module:
                imports.append(f"import {module}")
        
        # 检查是否需要额外导入
        for handler in ast.handlers:
            for block in handler.flow:
                self._check_imports_for_block(block, imports)
        
        return list(set(imports))  # 去重
    
    def _check_imports_for_block(self, block: BlockInstance, imports: list[str]) -> None:
        """检查块需要的导入"""
        if block.block_type == "action.http_request":
            if "import aiohttp" not in imports:
                imports.append("import aiohttp")
        elif block.block_type == "action.reply_chain":
            if "import astrbot.api.message_components as Comp" not in imports:
                imports.append("import astrbot.api.message_components as Comp")
        
        # 检查分支
        for branch_blocks in block.branches.values():
            for branch_block in branch_blocks:
                self._check_imports_for_block(branch_block, imports)
    
    def _generate_init(self, ast: WorkflowAST) -> list[str]:
        """生成__init__方法"""
        lines = []
        lines.append(f"{self.indent}def __init__(self, context: star.Context) -> None:")
        lines.append(f"{self.indent}{self.indent}self.context = context")
        
        # 初始化变量
        for var in ast.variables:
            default = self._format_default_value(var.default, var.var_type)
            lines.append(f"{self.indent}{self.indent}self.{var.name} = {default}")
        
        # 用户自定义初始化代码
        if ast.init_code:
            for line in ast.init_code.split("\n"):
                lines.append(f"{self.indent}{self.indent}{line}")
        
        return lines
    
    def _generate_handler(self, handler: HandlerDefinition, ast: WorkflowAST) -> list[str]:
        """生成Handler方法"""
        lines = []
        
        # 生成装饰器
        decorators = self._generate_decorators(handler)
        lines.extend(decorators)
        
        # 方法签名
        method_name = handler.name or f"handler_{handler.id}"
        has_event_param = handler.trigger.block_type not in ["trigger.on_loaded"]
        
        if has_event_param:
            lines.append(f"{self.indent}async def {method_name}(self, event: AstrMessageEvent):")
        else:
            lines.append(f"{self.indent}async def {method_name}(self):")
        
        # Docstring
        desc = handler.description or f"{handler.trigger.block_type} 处理器"
        lines.append(f'{self.indent}{self.indent}"""{desc}"""')
        
        # 方法体
        body_lines = self._generate_handler_body(handler, ast)
        lines.extend(body_lines)
        
        return lines
    
    def _generate_decorators(self, handler: HandlerDefinition) -> list[str]:
        """生成装饰器"""
        decorators = []
        trigger = handler.trigger
        
        # 主触发器装饰器
        decorator = self._trigger_to_decorator(trigger)
        if decorator:
            decorators.append(f"{self.indent}{decorator}")
        
        # 额外过滤器装饰器
        for f in trigger.filters:
            filter_decorator = self._filter_to_decorator(f)
            if filter_decorator:
                decorators.append(f"{self.indent}{filter_decorator}")
        
        return decorators
    
    def _trigger_to_decorator(self, trigger: Any) -> str:
        """将触发器转换为装饰器"""
        block_type = trigger.block_type
        params = trigger.params
        
        if block_type == "trigger.command":
            cmd = params.get("command", "")
            alias = params.get("alias", [])
            if alias:
                alias_str = "{" + ", ".join(f"'{a}'" for a in alias) + "}"
                return f'@filter.command("{cmd}", alias={alias_str})'
            return f'@filter.command("{cmd}")'
        
        elif block_type == "trigger.regex":
            pattern = params.get("pattern", "")
            return f'@filter.regex(r"{pattern}")'
        
        elif block_type == "trigger.event_message_type":
            msg_type = params.get("message_type", "ALL")
            return f"@filter.event_message_type(filter.EventMessageType.{msg_type})"
        
        elif block_type == "trigger.platform":
            platforms = params.get("platforms", ["ALL"])
            platform_strs = [f"filter.PlatformAdapterType.{p}" for p in platforms]
            return f"@filter.platform_adapter_type({' | '.join(platform_strs)})"
        
        elif block_type == "trigger.permission":
            perm = params.get("permission", "ADMIN")
            raise_error = params.get("raise_error", True)
            return f"@filter.permission_type(filter.PermissionType.{perm}, raise_error={raise_error})"
        
        elif block_type == "trigger.on_loaded":
            return "@filter.on_astrbot_loaded()"
        
        elif block_type == "trigger.on_llm_request":
            return "@filter.on_llm_request()"
        
        elif block_type == "trigger.keyword":
            # 关键词触发使用event_message_type + 内部判断
            return "@filter.event_message_type(filter.EventMessageType.ALL)"
        
        elif block_type == "trigger.user_join":
            return "@filter.on_user_join()"
        
        elif block_type == "trigger.user_leave":
            return "@filter.on_user_leave()"
        
        elif block_type == "trigger.file_upload":
            return "@filter.on_file_upload()"
        
        elif block_type == "trigger.reaction":
            return "@filter.on_reaction()"
        
        elif block_type == "trigger.schedule":
            schedule_type = params.get("schedule_type", "interval")
            if schedule_type == "interval":
                interval = params.get("interval_seconds", 60)
                return f"@filter.on_schedule(schedule_type=\"interval\", interval={interval})"
            elif schedule_type == "daily":
                time = params.get("time", "09:00")
                return f'@filter.on_schedule(schedule_type="daily", time="{time}")'
            elif schedule_type == "weekly":
                time = params.get("time", "09:00")
                day = params.get("day_of_week", 1)
                return f'@filter.on_schedule(schedule_type="weekly", time="{time}", day={day})'
            else:  # cron
                cron = params.get("cron_expression", "0 9 * * *")
                return f'@filter.on_schedule(schedule_type="cron", cron="{cron}")'
        
        elif block_type == "trigger.random_chance":
            # 随机概率触发使用event_message_type + 内部判断
            return "@filter.event_message_type(filter.EventMessageType.ALL)"
        
        elif block_type == "trigger.nth_time":
            # 第N次触发使用event_message_type + 内部判断
            return "@filter.event_message_type(filter.EventMessageType.ALL)"
        
        return ""
    
    def _filter_to_decorator(self, f: dict) -> str:
        """将过滤器转换为装饰器"""
        block_type = f.get("block", "")
        params = f.get("params", {})
        
        if block_type == "trigger.event_message_type":
            msg_type = params.get("message_type", "ALL")
            return f"@filter.event_message_type(filter.EventMessageType.{msg_type})"
        elif block_type == "trigger.platform":
            platforms = params.get("platforms", ["ALL"])
            platform_strs = [f"filter.PlatformAdapterType.{p}" for p in platforms]
            return f"@filter.platform_adapter_type({' | '.join(platform_strs)})"
        elif block_type == "trigger.permission":
            perm = params.get("permission", "ADMIN")
            return f"@filter.permission_type(filter.PermissionType.{perm})"
        
        return ""
    
    def _generate_handler_body(self, handler: HandlerDefinition, ast: WorkflowAST) -> list[str]:
        """生成Handler方法体"""
        lines = []
        indent = self.indent * 2  # 方法内二级缩进
        
        # 特殊处理关键词触发
        if handler.trigger.block_type == "trigger.keyword":
            lines.extend(self._generate_keyword_check(handler.trigger.params))
        
        # 特殊处理随机概率触发
        elif handler.trigger.block_type == "trigger.random_chance":
            lines.extend(self._generate_random_chance_check(handler.trigger.params))
        
        # 特殊处理第N次触发
        elif handler.trigger.block_type == "trigger.nth_time":
            lines.extend(self._generate_nth_time_check(handler.trigger.params))
        
        # 生成流程块代码
        for block in handler.flow:
            block_lines = self._generate_block_code(block, indent_level=2)
            lines.extend(block_lines)
        
        # 如果没有生成任何代码，添加pass
        if not lines:
            lines.append(f"{indent}pass")
        
        return lines
    
    def _generate_random_chance_check(self, params: dict) -> list[str]:
        """生成随机概率检查代码"""
        probability = params.get("probability", 50)
        
        lines = []
        indent = self.indent * 2
        
        lines.append(f"{indent}import random")
        lines.append(f"{indent}rolled = random.randint(1, 100)")
        lines.append(f"{indent}if rolled > {probability}:")
        lines.append(f"{indent}    return")
        
        return lines
    
    def _generate_nth_time_check(self, params: dict) -> list[str]:
        """生成第N次触发检查代码"""
        n = params.get("n", 5)
        counter_key = params.get("counter_key", "global")
        
        lines = []
        indent = self.indent * 2
        
        lines.append(f'{indent}counter_key = "{counter_key}"')
        lines.append(f"{indent}if not hasattr(self, '_nth_counter'):")
        lines.append(f"{indent}    self._nth_counter = {{}}")
        lines.append(f"{indent}if counter_key not in self._nth_counter:")
        lines.append(f"{indent}    self._nth_counter[counter_key] = 0")
        lines.append(f"{indent}self._nth_counter[counter_key] += 1")
        lines.append(f"{indent}if self._nth_counter[counter_key] % {n} != 0:")
        lines.append(f"{indent}    return")
        
        return lines
    
    def _generate_keyword_check(self, params: dict) -> list[str]:
        """生成关键词检查代码"""
        keywords = params.get("keywords", [])
        match_all = params.get("match_all", False)
        case_sensitive = params.get("case_sensitive", False)
        
        lines = []
        indent = self.indent * 2  # 方法内二级缩进
        
        if not case_sensitive:
            lines.append(f"{indent}msg = event.message_str.lower()")
            keywords_str = str([k.lower() for k in keywords])
        else:
            lines.append(f"{indent}msg = event.message_str")
            keywords_str = str(keywords)
        
        lines.append(f"{indent}keywords = {keywords_str}")
        
        if match_all:
            lines.append(f"{indent}if not all(kw in msg for kw in keywords):")
            lines.append(f"{indent}    return")
        else:
            lines.append(f"{indent}matched = None")
            lines.append(f"{indent}for kw in keywords:")
            lines.append(f"{indent}    if kw in msg:")
            lines.append(f"{indent}        matched = kw")
            lines.append(f"{indent}        break")
            lines.append(f"{indent}if not matched:")
            lines.append(f"{indent}    return")
        
        return lines
    
    def _generate_block_code(self, block: BlockInstance, indent_level: int = 2) -> list[str]:
        """生成块代码"""
        base_indent = self.indent * indent_level
        lines = []
        
        block_type = block.block_type
        params = block.params
        
        # 根据块类型生成代码
        if block_type == "action.reply_text":
            text = self._render_template(params.get("text", ""), self.class_vars)
            lines.append(f"{base_indent}yield event.plain_result({text})")
        
        elif block_type == "action.reply_image":
            source_type = params.get("source_type", "url")
            if source_type == "url":
                url = self._render_template(params.get("url", ""), self.class_vars)
                lines.append(f"{base_indent}yield event.image_result({url})")
            elif source_type == "file":
                path = self._render_template(params.get("file_path", ""), self.class_vars)
                lines.append(f"{base_indent}yield event.image_result({path})")
            else:
                var = params.get("variable", "")
                lines.append(f"{base_indent}yield event.image_result(self.{var})")
        
        elif block_type == "action.reply_chain":
            lines.append(f"{base_indent}chain = [")
            for comp in params.get("components", []):
                comp_type = comp.get("type", "text")
                content = comp.get("content", "")
                if comp_type == "text":
                    lines.append(f'{base_indent}    Comp.Plain("{content}"),')
                elif comp_type == "image":
                    lines.append(f'{base_indent}    Comp.Image.fromURL("{content}"),')
                elif comp_type == "at":
                    lines.append(f'{base_indent}    Comp.At(qq="{content}"),')
                elif comp_type == "at_all":
                    lines.append(f'{base_indent}    Comp.AtAll(),')
                elif comp_type == "face":
                    lines.append(f'{base_indent}    Comp.Face(id={content}),')
            lines.append(f"{base_indent}]")
            lines.append(f"{base_indent}yield event.chain_result(chain)")
        
        elif block_type == "action.send_message":
            target_type = params.get("target_type", "current")
            msg_type = params.get("message_type", "text")
            content = self._render_template(params.get("content", ""), self.class_vars)
            
            if target_type == "current":
                lines.append(f"{base_indent}umo = event.unified_msg_origin")
            elif target_type == "saved":
                var = params.get("umo_variable", "")
                lines.append(f"{base_indent}umo = self.{var}")
            else:
                umo = params.get("umo", "")
                lines.append(f'{base_indent}umo = "{umo}"')
            
            lines.append(f"{base_indent}from astrbot.api.event import MessageChain")
            lines.append(f"{base_indent}chain = MessageChain().message({content})")
            lines.append(f"{base_indent}await self.context.send_message(umo, chain)")
        
        elif block_type == "action.http_request":
            method = params.get("method", "GET")
            url = self._render_template(params.get("url", ""), self.class_vars)
            headers = params.get("headers", {})
            timeout = params.get("timeout", 30)
            save_to = params.get("save_to", "_http_resp")
            
            lines.append(f"{base_indent}import aiohttp")
            lines.append(f"{base_indent}async with aiohttp.ClientSession() as session:")
            lines.append(f'{base_indent}    async with session.{method.lower()}({url}, headers={headers}, timeout={timeout}) as resp:')
            lines.append(f"{base_indent}        {save_to}_status = resp.status")
            lines.append(f"{base_indent}        {save_to}_body = await resp.text()")
        
        elif block_type == "action.delay":
            seconds = params.get("seconds", 1)
            lines.append(f"{base_indent}await asyncio.sleep({seconds})")
        
        elif block_type == "action.call_llm":
            prompt = self._render_template(params.get("prompt", ""), self.class_vars)
            system_prompt = params.get("system_prompt", "")
            save_to = params.get("save_to", "llm_response")
            
            lines.append(f"{base_indent}prov = self.context.get_using_provider(umo=event.unified_msg_origin)")
            lines.append(f"{base_indent}if prov:")
            lines.append(f"{base_indent}    {save_to} = await prov.text_chat(")
            lines.append(f"{base_indent}        prompt={prompt},")
            lines.append(f'{base_indent}        system_prompt="{system_prompt}"')
            lines.append(f"{base_indent}    )")
            lines.append(f"{base_indent}    {save_to}_text = {save_to}.completion_text")
        
        elif block_type == "action.stop_event":
            lines.append(f"{base_indent}event.stop_event()")
        
        elif block_type == "action.store_umo":
            var = params.get("variable", "")
            lines.append(f"{base_indent}self.{var} = event.unified_msg_origin")
        
        elif block_type == "action.parallel":
            branches = params.get("branches", [])
            wait_all = params.get("wait_all", True)
            
            # 生成并行任务函数
            for i, branch in enumerate(branches):
                branch_id = branch.get("branch_id", f"branch_{i}")
                branch_blocks = block.branches.get(branch_id, [])
                
                lines.append(f"{base_indent}async def _parallel_task_{i}():")
                if branch_blocks:
                    for b in branch_blocks:
                        for line in self._generate_block_code(b, indent_level + 1):
                            lines.append(line)
                else:
                    lines.append(f"{base_indent}    pass")
            
            # 生成并行执行代码
            task_names = [f"_parallel_task_{i}" for i in range(len(branches))]
            if wait_all:
                lines.append(f"{base_indent}await asyncio.gather({', '.join(task_names)})")
            else:
                for task in task_names:
                    lines.append(f"{base_indent}asyncio.create_task({task}())")
        
        elif block_type == "logic.if":
            condition = self._render_condition(params.get("condition", ""))
            lines.append(f"{base_indent}if {condition}:")
            
            true_blocks = block.branches.get("true", [])
            if true_blocks:
                for b in true_blocks:
                    for line in self._generate_block_code(b, indent_level + 1):
                        lines.append(line)
            else:
                lines.append(f"{base_indent}    pass")
            
            false_blocks = block.branches.get("false", [])
            if false_blocks:
                lines.append(f"{base_indent}else:")
                for b in false_blocks:
                    for line in self._generate_block_code(b, indent_level + 1):
                        lines.append(line)
        
        elif block_type == "logic.for_each":
            items = params.get("items", "[]")
            item_var = params.get("item_var", "item")
            
            lines.append(f"{base_indent}for {item_var}_idx, {item_var} in enumerate({items}):")
            
            loop_blocks = block.branches.get("loop", [])
            if loop_blocks:
                for b in loop_blocks:
                    for line in self._generate_block_code(b, indent_level + 1):
                        lines.append(line)
            else:
                lines.append(f"{base_indent}    pass")
        
        elif block_type == "logic.while":
            condition = self._render_condition(params.get("condition", ""))
            max_iter = params.get("max_iterations", 100)
            
            lines.append(f"{base_indent}_while_iter = 0")
            lines.append(f"{base_indent}while {condition} and _while_iter < {max_iter}:")
            lines.append(f"{base_indent}    _while_iter += 1")
            
            loop_blocks = block.branches.get("loop", [])
            if loop_blocks:
                for b in loop_blocks:
                    for line in self._generate_block_code(b, indent_level + 1):
                        lines.append(line)
            else:
                lines.append(f"{base_indent}    pass")
        
        elif block_type == "logic.try_catch":
            lines.append(f"{base_indent}try:")
            
            try_blocks = block.branches.get("try", [])
            if try_blocks:
                for b in try_blocks:
                    for line in self._generate_block_code(b, indent_level + 1):
                        lines.append(line)
            else:
                lines.append(f"{base_indent}    pass")
            
            lines.append(f"{base_indent}except Exception as e:")
            lines.append(f'{base_indent}    logger.error(f"Error: {{e}}")')
            
            catch_blocks = block.branches.get("catch", [])
            if catch_blocks:
                for b in catch_blocks:
                    for line in self._generate_block_code(b, indent_level + 1):
                        lines.append(line)
            else:
                lines.append(f"{base_indent}    pass")
        
        elif block_type == "util.get_sender_info":
            info_type = params.get("info_type", "id")
            save_to = params.get("save_to", "")
            
            if info_type == "id":
                var = save_to or "_sender_id"
                lines.append(f"{base_indent}{var} = event.get_sender_id()")
            elif info_type == "name":
                var = save_to or "_sender_name"
                lines.append(f"{base_indent}{var} = event.get_sender_name()")
            elif info_type == "role":
                var = save_to or "_sender_role"
                lines.append(f"{base_indent}{var} = event.role")
        
        elif block_type == "util.get_group_info":
            info_type = params.get("info_type", "id")
            save_to = params.get("save_to", "")
            
            if info_type == "id":
                var = save_to or "_group_id"
                lines.append(f"{base_indent}{var} = event.get_group_id()")
            else:
                var = save_to or "_group_info"
                lines.append(f"{base_indent}group = await event.get_group()")
                if info_type == "name":
                    lines.append(f'{base_indent}{var} = group.group_name if group else ""')
                elif info_type == "member_count":
                    lines.append(f"{base_indent}{var} = group.member_count if group else 0")
        
        elif block_type == "util.get_message":
            info_type = params.get("info_type", "text")
            save_to = params.get("save_to", "")
            
            if info_type == "text":
                var = save_to or "_msg_text"
                lines.append(f"{base_indent}{var} = event.message_str")
            elif info_type == "outline":
                var = save_to or "_msg_outline"
                lines.append(f"{base_indent}{var} = event.get_message_outline()")
            elif info_type == "type":
                var = save_to or "_msg_type"
                lines.append(f"{base_indent}{var} = event.get_message_type()")
            elif info_type == "has_image":
                var = save_to or "_has_image"
                lines.append(f"{base_indent}{var} = any(isinstance(c, Comp.Image) for c in event.get_messages())")
        
        elif block_type == "util.random":
            mode = params.get("mode", "int")
            min_val = params.get("min", 0)
            max_val = params.get("max", 100)
            choices = params.get("choices", [])
            save_to = params.get("save_to", "")
            
            var = save_to or "_random"
            if mode == "int":
                lines.append(f"{base_indent}{var} = random.randint({min_val}, {max_val})")
            elif mode == "float":
                lines.append(f"{base_indent}{var} = random.uniform({min_val}, {max_val})")
            elif mode == "choice":
                lines.append(f"{base_indent}{var} = random.choice({choices})")
        
        elif block_type == "util.time_now":
            fmt = params.get("format", "%Y-%m-%d %H:%M:%S")
            save_to = params.get("save_to", "")
            
            var = save_to or "_time"
            lines.append(f'{base_indent}{var} = datetime.now().strftime("{fmt}")')
            lines.append(f"{base_indent}{var}_ts = int(datetime.now().timestamp())")
        
        elif block_type == "util.variable":
            operation = params.get("operation", "set")
            name = params.get("name", "")
            value = self._render_template(params.get("value", ""), self.class_vars)
            
            if operation == "set":
                # 跟踪动态创建的类成员变量
                self.class_vars.add(name)
                lines.append(f"{base_indent}self.{name} = {value}")
            elif operation == "get":
                lines.append(f"{base_indent}_var_{name} = self.{name}")
            elif operation == "increment":
                lines.append(f"{base_indent}self.{name} = self.{name} + 1")
            elif operation == "decrement":
                lines.append(f"{base_indent}self.{name} = self.{name} - 1")
            elif operation == "append":
                lines.append(f"{base_indent}self.{name}.append({value})")
        
        elif block_type == "util.log":
            level = params.get("level", "info")
            message = self._render_template(params.get("message", ""), self.class_vars)
            lines.append(f"{base_indent}logger.{level}({message})")
        
        else:
            lines.append(f"{base_indent}# Unknown block type: {block_type}")
        
        return lines
    
    def _render_template(self, text: str, class_vars: set = None) -> str:
        """渲染模板字符串
        
        Args:
            text: 模板文本
            class_vars: 类成员变量名集合（需要self.前缀）
        """
        if not text:
            return '""'
        
        class_vars = class_vars or set()
        
        # 内置变量直接替换为代码
        builtin_vars = {
            "message_str": "event.message_str",
            "sender_id": "event.get_sender_id()",
            "sender_name": "event.get_sender_name()",
            "group_id": "event.get_group_id()",
            "self_id": "event.get_self_id()",
            "platform": "event.get_platform_name()",
            "is_private": "event.is_private_chat()",
            "is_admin": "event.is_admin()",
        }
        
        result = text
        
        # 替换内置变量 {var} -> {code}
        for var_name, code in builtin_vars.items():
            placeholder = "{" + var_name + "}"
            if placeholder in result:
                result = result.replace(placeholder, "{" + code + "}")
        
        # 替换其他变量
        pattern = r"\{(\w+)\}"
        def replace_var(match):
            var_name = match.group(1)
            # 如果不是内置变量名
            if var_name not in builtin_vars:
                # 如果是类成员变量，加self.前缀
                if var_name in class_vars:
                    return "{self." + var_name + "}"
                # 否则是局部变量，保持原样
                return "{" + var_name + "}"
            return match.group(0)
        
        result = re.sub(pattern, replace_var, result)
        
        # 检查是否包含任何变量引用
        if "{" in result and "}" in result:
            return f'f"{result}"'
        
        return f'"{result}"'
    
    def _render_condition(self, condition: str) -> str:
        """渲染条件表达式"""
        # 替换内置变量
        condition = condition.replace("{sender_id}", "event.get_sender_id()")
        condition = condition.replace("{sender_name}", "event.get_sender_name()")
        condition = condition.replace("{group_id}", "event.get_group_id()")
        condition = condition.replace("{message_str}", "event.message_str")
        
        # 替换自定义变量
        pattern = r"\{(\w+)\}"
        condition = re.sub(pattern, r"self.\1", condition)
        
        return condition
    
    def _generate_terminate(self, ast: WorkflowAST) -> list[str]:
        """生成terminate方法"""
        lines = []
        lines.append(f"{self.indent}async def terminate(self):")
        lines.append(f'{self.indent}{self.indent}"""插件终止时的清理操作"""')
        
        if ast.terminate_code:
            for line in ast.terminate_code.split("\n"):
                lines.append(f"{self.indent}{self.indent}{line}")
        else:
            lines.append(f"{self.indent}{self.indent}pass")
        
        return lines
    
    def _generate_metadata_yaml(self, ast: WorkflowAST) -> str:
        """生成metadata.yaml"""
        lines = [
            f"name: {ast.metadata.display_name or ast.metadata.name}",
            f"author: {ast.metadata.author}",
            f"description: {ast.metadata.description}",
            f"version: {ast.metadata.version}",
        ]
        
        if ast.metadata.repo:
            lines.append(f"repo: {ast.metadata.repo}")
        if ast.metadata.logo:
            lines.append(f"logo: {ast.metadata.logo}")
        
        return "\n".join(lines)
    
    def _generate_conf_schema(self, ast: WorkflowAST) -> str:
        """生成_conf_schema.json"""
        import json
        schema = {}
        
        for item in ast.config_items:
            schema[item.name] = {
                "description": item.description,
                "type": item.item_type,
                "default": item.default,
            }
            if item.hint:
                schema[item.name]["hint"] = item.hint
            if item.options:
                schema[item.name]["options"] = item.options
        
        return json.dumps(schema, ensure_ascii=False, indent=2)
    
    def _to_class_name(self, name: str) -> str:
        """转换为类名"""
        # 转换为PascalCase
        parts = name.split("_")
        return "".join(p.capitalize() for p in parts)
    
    def _format_default_value(self, value: Any, var_type: str) -> str:
        """格式化默认值"""
        if value is None:
            type_defaults = {
                "string": '""',
                "int": "0",
                "float": "0.0",
                "bool": "False",
                "list": "[]",
                "dict": "{}",
            }
            return type_defaults.get(var_type, "None")
        
        if var_type == "string":
            return f'"{value}"'
        elif var_type in ("int", "float"):
            return str(value)
        elif var_type == "bool":
            return "True" if value else "False"
        elif var_type == "list":
            return str(value)
        elif var_type == "dict":
            return str(value)
        
        return str(value)
