"""
代码生成器 - 将AST转换为Python代码
"""

import re
from typing import Any

from .parser import (
    BlockInstance,
    HandlerDefinition,
    WorkflowAST,
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

        # 2. @register装饰器
        lines.append(f'@register("{ast.metadata.name}", "{ast.metadata.author}", "{ast.metadata.description}", "{ast.metadata.version}", "{ast.metadata.repo or ""}")')
        # 3. 插件类
        lines.append(f"class {self._to_class_name(ast.metadata.name)}(star.Star):")
        lines.append(f'    """{ast.metadata.description}"""')
        lines.append("")

        # 4. __init__方法
        lines.extend(self._generate_init(ast))
        lines.append("")

        # 5. Handler方法
        for handler in ast.handlers:
            lines.extend(self._generate_handler(handler, ast))
            lines.append("")

        # 6. terminate方法
        lines.extend(self._generate_terminate(ast))

        return "\n".join(lines)

    def _generate_imports(self, ast: WorkflowAST) -> list[str]:
        """生成导入语句"""
        imports = [
            "from astrbot.api import star",
            "from astrbot.api.event import AstrMessageEvent, filter",
            "from astrbot.api import logger",
            "from astrbot.api.star import register",
            "from astrbot.api.provider import ProviderRequest",
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
        elif block.block_type in ["action.reply_face", "trigger.file_received"]:
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
        lines.append(f"{self.indent}{self.indent}super().__init__(context)")
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
        trigger_type = handler.trigger.block_type
        
        if trigger_type == "trigger.on_loaded":
            lines.append(f"{self.indent}async def {method_name}(self):")
        elif trigger_type == "trigger.on_llm_request":
            lines.append(f"{self.indent}async def {method_name}(self, event: AstrMessageEvent, req: ProviderRequest):")
        else:
            lines.append(f"{self.indent}async def {method_name}(self, event: AstrMessageEvent):")

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
            return (
                f"@filter.permission_type(filter.PermissionType.{perm}, raise_error={raise_error})"
            )

        elif block_type == "trigger.on_loaded":
            return "@filter.on_astrbot_loaded()"

        elif block_type == "trigger.on_llm_request":
            return "@filter.on_llm_request()"

        elif block_type == "trigger.keyword":
            # 关键词触发使用event_message_type + 内部判断
            return "@filter.event_message_type(filter.EventMessageType.ALL)"

        elif block_type == "trigger.start_with":
            # 开头匹配触发使用event_message_type + 内部判断
            return "@filter.event_message_type(filter.EventMessageType.ALL)"

        elif block_type == "trigger.end_with":
            # 结尾匹配触发使用event_message_type + 内部判断
            return "@filter.event_message_type(filter.EventMessageType.ALL)"

        elif block_type == "trigger.random_chance":
            # 随机概率触发使用event_message_type + 内部判断
            return "@filter.event_message_type(filter.EventMessageType.ALL)"

        elif block_type == "trigger.nth_time":
            # 第N次触发使用event_message_type + 内部判断
            return "@filter.event_message_type(filter.EventMessageType.ALL)"

        elif block_type == "trigger.file_received":
            # 文件接收触发使用event_message_type + 内部判断
            return "@filter.event_message_type(filter.EventMessageType.ALL)"

        # 以下触发器在AstrBot API中不存在，返回空字符串标记为不支持
        elif block_type in ["trigger.user_join", "trigger.user_leave", 
                           "trigger.file_upload", "trigger.reaction", "trigger.schedule"]:
            # 不支持的触发器类型，将在handler body中生成警告注释
            return f"# WARNING: {block_type} is not supported in current AstrBot API"

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

        # 特殊处理开头匹配触发
        elif handler.trigger.block_type == "trigger.start_with":
            lines.extend(self._generate_start_with_check(handler.trigger.params))

        # 特殊处理结尾匹配触发
        elif handler.trigger.block_type == "trigger.end_with":
            lines.extend(self._generate_end_with_check(handler.trigger.params))

        # 特殊处理随机概率触发
        elif handler.trigger.block_type == "trigger.random_chance":
            lines.extend(self._generate_random_chance_check(handler.trigger.params))

        # 特殊处理第N次触发
        elif handler.trigger.block_type == "trigger.nth_time":
            lines.extend(self._generate_nth_time_check(handler.trigger.params))

        # 特殊处理文件接收触发
        elif handler.trigger.block_type == "trigger.file_received":
            lines.extend(self._generate_file_received_check(handler.trigger.params))

        # 不支持的触发器类型
        elif handler.trigger.block_type in ["trigger.user_join", "trigger.user_leave", 
                                            "trigger.file_upload", "trigger.reaction", "trigger.schedule"]:
            lines.append(f"{indent}# WARNING: {handler.trigger.block_type} is not supported in current AstrBot API")
            lines.append(f"{indent}raise NotImplementedError(\"{handler.trigger.block_type} is not supported\")")

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

    def _generate_file_received_check(self, params: dict) -> list[str]:
        """生成文件接收检查代码"""
        file_types = params.get("file_types", [])
        max_size = params.get("max_size", 0)  # KB

        lines = []
        indent = self.indent * 2

        # 检查消息中是否有文件组件
        lines.append(f"{indent}_has_file = any(isinstance(c, Comp.File) for c in event.get_messages())")
        lines.append(f"{indent}if not _has_file:")
        lines.append(f"{indent}    return")
        
        # 获取文件信息
        lines.append(f"{indent}_file_comp = next((c for c in event.get_messages() if isinstance(c, Comp.File)), None)")
        lines.append(f"{indent}if _file_comp:")
        lines.append(f"{indent}    file_name = _file_comp.name if hasattr(_file_comp, 'name') else \"\"")
        lines.append(f"{indent}    file_url = _file_comp.url if hasattr(_file_comp, 'url') else \"\"")
        lines.append(f"{indent}    file_size = _file_comp.size if hasattr(_file_comp, 'size') else 0")
        
        # 文件类型过滤
        if file_types:
            lines.append(f"{indent}    _allowed = any(file_name.endswith(ft) for ft in {file_types})")
            lines.append(f"{indent}    if not _allowed:")
            lines.append(f"{indent}        return")
        
        # 文件大小限制
        if max_size > 0:
            lines.append(f"{indent}    if file_size > {max_size} * 1024:")
            lines.append(f"{indent}        return")

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

    def _generate_start_with_check(self, params: dict) -> list[str]:
        """生成开头匹配检查代码"""
        prefix = params.get("prefix", "")
        case_sensitive = params.get("case_sensitive", False)

        lines = []
        indent = self.indent * 2  # 方法内二级缩进

        lines.append(f"{indent}msg = event.message_str")
        
        if not case_sensitive:
            lines.append(f'{indent}prefix = "{prefix}".lower()')
            lines.append(f"{indent}if msg.lower().startswith(prefix):")
            lines.append(f"{indent}    remaining = msg[len(prefix):].lstrip()")
            lines.append(f"{indent}else:")
            lines.append(f"{indent}    return")
        else:
            lines.append(f'{indent}prefix = "{prefix}"')
            lines.append(f"{indent}if msg.startswith(prefix):")
            lines.append(f"{indent}    remaining = msg[len(prefix):].lstrip()")
            lines.append(f"{indent}else:")
            lines.append(f"{indent}    return")

        return lines

    def _generate_end_with_check(self, params: dict) -> list[str]:
        """生成结尾匹配检查代码"""
        suffix = params.get("suffix", "")
        case_sensitive = params.get("case_sensitive", False)

        lines = []
        indent = self.indent * 2  # 方法内二级缩进

        lines.append(f"{indent}msg = event.message_str")
        
        if not case_sensitive:
            lines.append(f'{indent}suffix = "{suffix}".lower()')
            lines.append(f"{indent}if msg.lower().endswith(suffix):")
            lines.append(f"{indent}    remaining = msg[:-len(suffix)].rstrip()")
            lines.append(f"{indent}else:")
            lines.append(f"{indent}    return")
        else:
            lines.append(f'{indent}suffix = "{suffix}"')
            lines.append(f"{indent}if msg.endswith(suffix):")
            lines.append(f"{indent}    remaining = msg[:-len(suffix)].rstrip()")
            lines.append(f"{indent}else:")
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
                    lines.append(f'{base_indent}    Comp.Plain(text="{content}"),')
                elif comp_type == "image":
                    lines.append(f'{base_indent}    Comp.Image.fromURL("{content}"),')
                elif comp_type == "at":
                    lines.append(f'{base_indent}    Comp.At(qq="{content}"),')
                elif comp_type == "at_all":
                    lines.append(f"{base_indent}    Comp.AtAll(),")
                elif comp_type == "face":
                    lines.append(f"{base_indent}    Comp.Face(id={content}),")
            lines.append(f"{base_indent}]")
            lines.append(f"{base_indent}yield event.chain_result(chain)")

        elif block_type == "action.send_message":
            target_type = params.get("target_type", "current")
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
            lines.append(
                f"{base_indent}    async with session.{method.lower()}({url}, headers={headers}, timeout={timeout}) as resp:"
            )
            lines.append(f"{base_indent}        {save_to}_status = resp.status")
            lines.append(f"{base_indent}        {save_to}_body = await resp.text()")

        elif block_type == "action.delay":
            seconds = params.get("seconds", 1)
            lines.append(f"{base_indent}await asyncio.sleep({seconds})")

        elif block_type == "action.call_llm":
            prompt = self._render_template(params.get("prompt", ""), self.class_vars)
            system_prompt = params.get("system_prompt", "")
            save_to = params.get("save_to", "llm_response")

            lines.append(
                f"{base_indent}prov = self.context.get_using_provider(umo=event.unified_msg_origin)"
            )
            lines.append(f"{base_indent}if prov:")
            lines.append(f"{base_indent}    {save_to} = await prov.text_chat(")
            lines.append(f"{base_indent}        prompt={prompt},")
            lines.append(f'{base_indent}        system_prompt="{system_prompt}"')
            lines.append(f"{base_indent}    )")
            lines.append(f"{base_indent}    {save_to}_text = {save_to}.completion_text")

        elif block_type == "action.stop_event":
            lines.append(f"{base_indent}event.stop_event()")

        elif block_type == "action.reply_card":
            # Card组件在AstrBot API中不存在，生成警告
            lines.append(f"{base_indent}# WARNING: Card component is not supported in AstrBot API")
            lines.append(f"{base_indent}raise NotImplementedError(\"action.reply_card is not supported\")")

        elif block_type == "action.goto":
            # Python不支持goto，无法实现
            label = params.get("label", "")
            lines.append(f"{base_indent}# WARNING: goto is not supported in Python")
            lines.append(f"{base_indent}# Label '{label}' cannot be jumped to")
            lines.append(f"{base_indent}raise NotImplementedError(\"action.goto is not supported - use loops or conditionals instead\")")

        elif block_type == "action.label":
            # 标签无实际功能，仅作为注释
            label = params.get("label", "")
            lines.append(f"{base_indent}# Label: {label}")

        elif block_type == "action.reply_face":
            face_id = params.get("face_id", "")
            lines.append(f"{base_indent}yield event.chain_result([Comp.Face(id={face_id})])")

        elif block_type == "action.delete_msg":
            message_id = self._render_template(params.get("message_id", ""), self.class_vars)
            if params.get("message_id"):
                lines.append(f"{base_indent}await event.delete_message({message_id})")
            else:
                lines.append(f"{base_indent}await event.delete_message(event.message_id)")

        elif block_type == "action.set_group_card":
            user_id = self._render_template(params.get("user_id", ""), self.class_vars)
            card = self._render_template(params.get("card", ""), self.class_vars)
            lines.append(f"{base_indent}group = await event.get_group()")
            if params.get("user_id"):
                lines.append(f"{base_indent}user_id = {user_id}")
            else:
                lines.append(f"{base_indent}user_id = event.get_sender_id()")
            lines.append(f"{base_indent}if group:")
            lines.append(f"{base_indent}    await group.set_member_card(user_id, {card})")

        elif block_type == "action.kick_member":
            user_id = self._render_template(params.get("user_id", ""), self.class_vars)
            reject = params.get("reject_add_request", False)
            lines.append(f"{base_indent}group = await event.get_group()")
            lines.append(f"{base_indent}if group:")
            lines.append(
                f"{base_indent}    await group.kick_member({user_id}, reject_add_request={reject})"
            )

        elif block_type == "action.mute_member":
            user_id = self._render_template(params.get("user_id", ""), self.class_vars)
            duration = params.get("duration", 60)
            lines.append(f"{base_indent}group = await event.get_group()")
            lines.append(f"{base_indent}if group:")
            lines.append(
                f"{base_indent}    await group.mute_member({user_id}, duration={duration})"
            )

        elif block_type == "action.unmute_member":
            user_id = self._render_template(params.get("user_id", ""), self.class_vars)
            lines.append(f"{base_indent}group = await event.get_group()")
            lines.append(f"{base_indent}if group:")
            lines.append(f"{base_indent}    await group.mute_member({user_id}, duration=0)")

        elif block_type == "action.set_admin":
            user_id = self._render_template(params.get("user_id", ""), self.class_vars)
            is_admin = params.get("is_admin", True)
            lines.append(f"{base_indent}group = await event.get_group()")
            lines.append(f"{base_indent}if group:")
            lines.append(
                f"{base_indent}    await group.set_member_admin({user_id}, is_admin={is_admin})"
            )

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
                gather_calls = ", ".join([f"{t}()" for t in task_names])
                lines.append(f"{base_indent}await asyncio.gather({gather_calls})")
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

        elif block_type == "logic.switch":
            value = self._render_template(params.get("value", ""), self.class_vars)
            cases = params.get("cases", [])
            default_flow_id = params.get("default_flow_id", "")

            lines.append(f"{base_indent}_switch_val = {value}")

            for i, case in enumerate(cases):
                match_val = case.get("match", "")
                flow_id = case.get("flow_id", "")
                branch_blocks = block.branches.get(flow_id, [])

                if i == 0:
                    lines.append(f'{base_indent}if _switch_val == "{match_val}":')
                else:
                    lines.append(f'{base_indent}elif _switch_val == "{match_val}":')

                if branch_blocks:
                    for b in branch_blocks:
                        for line in self._generate_block_code(b, indent_level + 1):
                            lines.append(line)
                else:
                    lines.append(f"{base_indent}    pass")

            if default_flow_id:
                default_blocks = block.branches.get(default_flow_id, [])
                lines.append(f"{base_indent}else:")
                if default_blocks:
                    for b in default_blocks:
                        for line in self._generate_block_code(b, indent_level + 1):
                            lines.append(line)
                else:
                    lines.append(f"{base_indent}    pass")

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
            elif info_type == "avatar":
                var = save_to or "_sender_avatar"
                lines.append(f'{base_indent}{var} = event.get_sender_avatar_url() or ""')
            elif info_type == "is_admin":
                var = save_to or "_is_admin"
                lines.append(f"{base_indent}{var} = event.is_admin()")
            elif info_type == "is_owner":
                var = save_to or "_is_owner"
                lines.append(
                    f"{base_indent}{var} = event.is_owner() if hasattr(event, 'is_owner') else False"
                )

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
                elif info_type == "description":
                    lines.append(
                        f'{base_indent}{var} = group.group_desc if group and hasattr(group, "group_desc") else ""'
                    )

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
                lines.append(
                    f"{base_indent}{var} = any(isinstance(c, Comp.Image) for c in event.get_messages())"
                )

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
            value_raw = params.get("value", "")

            if operation == "set":
                # 跟踪动态创建的类成员变量
                self.class_vars.add(name)
                # 检查是否是列表/字典字面量
                value_stripped = value_raw.strip()
                if value_stripped.startswith("[") or value_stripped.startswith("{"):
                    # 直接使用原始值作为Python字面量
                    lines.append(f"{base_indent}self.{name} = {value_raw}")
                elif value_stripped.lstrip("-").replace(".", "", 1).isdigit():
                    # 数值字面量，直接使用
                    lines.append(f"{base_indent}self.{name} = {value_raw}")
                else:
                    value = self._render_template(value_raw, self.class_vars)
                    lines.append(f"{base_indent}self.{name} = {value}")
            elif operation == "get":
                lines.append(f"{base_indent}_var_{name} = self.{name}")
            elif operation == "increment":
                lines.append(f"{base_indent}self.{name} = self.{name} + 1")
            elif operation == "decrement":
                lines.append(f"{base_indent}self.{name} = self.{name} - 1")
            elif operation == "append":
                value_stripped = value_raw.strip()
                if value_stripped.lstrip("-").replace(".", "", 1).isdigit():
                    # 数值字面量
                    lines.append(f"{base_indent}self.{name}.append({value_raw})")
                else:
                    value = self._render_template(value_raw, self.class_vars)
                    lines.append(f"{base_indent}self.{name}.append({value})")
            elif operation == "add":
                # 数值加法
                lines.append(f"{base_indent}self.{name} = self.{name} + {value_raw}")
            elif operation == "subtract":
                lines.append(f"{base_indent}self.{name} = self.{name} - {value_raw}")
            elif operation == "multiply":
                lines.append(f"{base_indent}self.{name} = self.{name} * {value_raw}")
            elif operation == "divide":
                lines.append(f"{base_indent}self.{name} = self.{name} / {value_raw}")

        elif block_type == "util.log":
            level = params.get("level", "info")
            message = self._render_template(params.get("message", ""), self.class_vars)
            lines.append(f"{base_indent}logger.{level}({message})")

        elif block_type == "util.data_store":
            operation = params.get("operation", "save")
            key = self._render_template(params.get("key", ""), self.class_vars)
            value = self._render_template(params.get("value", ""), self.class_vars)
            save_to = params.get("save_to", "_loaded_data")
            file_name = params.get("file_name", "plugin_data.json")

            lines.append(f"{base_indent}import json")
            lines.append(f"{base_indent}from pathlib import Path")
            lines.append(f'{base_indent}_data_file = Path(__file__).parent / "{file_name}"')

            if operation == "save":
                lines.append(f"{base_indent}if not _data_file.exists():")
                lines.append(f"{base_indent}    _data_store = {{}}")
                lines.append(f"{base_indent}else:")
                lines.append(
                    f'{base_indent}    with open(_data_file, "r", encoding="utf-8") as _f:'
                )
                lines.append(f"{base_indent}        _data_store = json.load(_f)")
                lines.append(f"{base_indent}_data_store[{key}] = {value}")
                lines.append(f'{base_indent}with open(_data_file, "w", encoding="utf-8") as _f:')
                lines.append(
                    f"{base_indent}    json.dump(_data_store, _f, ensure_ascii=False, indent=2)"
                )
            elif operation == "load":
                lines.append(f"{base_indent}if _data_file.exists():")
                lines.append(
                    f'{base_indent}    with open(_data_file, "r", encoding="utf-8") as _f:'
                )
                lines.append(f"{base_indent}        _data_store = json.load(_f)")
                lines.append(f"{base_indent}    {save_to} = _data_store.get({key})")
                lines.append(f"{base_indent}else:")
                lines.append(f"{base_indent}    {save_to} = None")
            elif operation == "delete":
                lines.append(f"{base_indent}if _data_file.exists():")
                lines.append(
                    f'{base_indent}    with open(_data_file, "r", encoding="utf-8") as _f:'
                )
                lines.append(f"{base_indent}        _data_store = json.load(_f)")
                lines.append(f"{base_indent}    if {key} in _data_store:")
                lines.append(f"{base_indent}        del _data_store[{key}]")
                lines.append(
                    f'{base_indent}        with open(_data_file, "w", encoding="utf-8") as _f:'
                )
                lines.append(
                    f"{base_indent}            json.dump(_data_store, _f, ensure_ascii=False, indent=2)"
                )
            elif operation == "exists":
                lines.append(f"{base_indent}_exists_result = False")
                lines.append(f"{base_indent}if _data_file.exists():")
                lines.append(
                    f'{base_indent}    with open(_data_file, "r", encoding="utf-8") as _f:'
                )
                lines.append(f"{base_indent}        _data_store = json.load(_f)")
                lines.append(f"{base_indent}    _exists_result = {key} in _data_store")

        elif block_type == "util.format_string":
            template = self._render_template(params.get("template", ""), self.class_vars)
            save_to = params.get("save_to", "formatted_str")
            lines.append(f"{base_indent}{save_to} = {template}")

        elif block_type == "util.json_parse":
            operation = params.get("operation", "parse")
            json_string_raw = params.get("json_string", "")
            path = params.get("path", "")
            save_to = params.get("save_to", "json_result")

            # JSON字符串需要特殊处理，避免f-string冲突
            if json_string_raw.startswith('"') or json_string_raw.startswith("'"):
                # 已经是引号包围的字符串
                json_string = json_string_raw
            else:
                # 作为原始字符串处理
                json_string = f'"""{json_string_raw}"""'

            if operation == "parse":
                lines.append(f"{base_indent}import json")
                lines.append(f"{base_indent}{save_to} = json.loads({json_string})")
            elif operation == "get":
                lines.append(f"{base_indent}import json")
                lines.append(f"{base_indent}_json_obj = json.loads({json_string})")
                # 简化路径解析
                path_parts = path.replace("[", ".").replace("]", "").split(".")
                for part in path_parts:
                    if part:
                        if part.isdigit():
                            lines.append(f"{base_indent}_json_obj = _json_obj[{part}]")
                        else:
                            lines.append(f'{base_indent}_json_obj = _json_obj["{part}"]')
                lines.append(f"{base_indent}{save_to} = _json_obj")
            elif operation == "stringify":
                lines.append(f"{base_indent}import json")
                lines.append(
                    f"{base_indent}{save_to} = json.dumps({json_string}, ensure_ascii=False, indent=2)"
                )

        elif block_type == "util.debug_log":
            variables = params.get("variables", [])
            message = params.get("message", "")
            lines.append(f'{base_indent}logger.debug("=== Debug Log ===")')
            if message:
                lines.append(f'{base_indent}logger.debug("Message: " + {repr(message)})')
            for var in variables:
                # 如果是类成员变量，添加self.前缀
                var_ref = f"self.{var}" if var in self.class_vars else var
                lines.append(f'{base_indent}logger.debug("{var} = " + str({var_ref}))')
            lines.append(f'{base_indent}logger.debug("=================")')

        elif block_type == "util.http_build":
            http_params = params.get("params", {})
            save_to = params.get("save_to", "http_params")
            lines.append(f"{base_indent}from urllib.parse import urlencode")
            lines.append(f"{base_indent}{save_to} = urlencode({http_params})")

        elif block_type == "util.string_operation":
            operation = params.get("operation", "strip")
            string = self._render_template(params.get("string", ""), self.class_vars)
            save_to = params.get("save_to", "str_result")

            if operation == "upper":
                lines.append(f"{base_indent}{save_to} = {string}.upper()")
            elif operation == "lower":
                lines.append(f"{base_indent}{save_to} = {string}.lower()")
            elif operation == "strip":
                lines.append(f"{base_indent}{save_to} = {string}.strip()")
            elif operation == "split":
                separator = params.get("separator", " ")
                lines.append(f'{base_indent}{save_to} = {string}.split("{separator}")')
            elif operation == "join":
                separator = params.get("separator", " ")
                items = params.get("items", "[]")
                lines.append(f'{base_indent}{save_to} = "{separator}".join({items})')
            elif operation == "replace":
                old = params.get("old", "")
                new = params.get("new", "")
                lines.append(f'{base_indent}{save_to} = {string}.replace("{old}", "{new}")')
            elif operation == "substring":
                start = params.get("start", 0)
                end = params.get("end", -1)
                if end == -1:
                    lines.append(f"{base_indent}{save_to} = {string}[{start}:]")
                else:
                    lines.append(f"{base_indent}{save_to} = {string}[{start}:{end}]")
            elif operation == "length":
                lines.append(f"{base_indent}{save_to} = len({string})")
            elif operation == "contains":
                search = params.get("search", "")
                lines.append(f'{base_indent}{save_to} = "{search}" in {string}')

        elif block_type == "util.file_operation":
            operation = params.get("operation", "read")
            path = self._render_template(params.get("path", ""), self.class_vars)
            content = self._render_template(params.get("content", ""), self.class_vars)
            encoding = params.get("encoding", "utf-8")
            save_to = params.get("save_to", "file_content")

            lines.append(f"{base_indent}from pathlib import Path")
            lines.append(f"{base_indent}_file_path = Path(__file__).parent / {path}")

            if operation == "read":
                lines.append(f"{base_indent}if _file_path.exists():")
                lines.append(
                    f'{base_indent}    with open(_file_path, "r", encoding="{encoding}") as _f:'
                )
                lines.append(f"{base_indent}        {save_to} = _f.read()")
                lines.append(f"{base_indent}else:")
                lines.append(f"{base_indent}    {save_to} = None")
            elif operation == "write":
                lines.append(
                    f'{base_indent}with open(_file_path, "w", encoding="{encoding}") as _f:'
                )
                lines.append(f"{base_indent}    _f.write({content})")
            elif operation == "append":
                lines.append(
                    f'{base_indent}with open(_file_path, "a", encoding="{encoding}") as _f:'
                )
                lines.append(f"{base_indent}    _f.write({content})")
            elif operation == "exists":
                lines.append(f"{base_indent}_exists_result = _file_path.exists()")
            elif operation == "delete":
                lines.append(f"{base_indent}if _file_path.exists():")
                lines.append(f"{base_indent}    _file_path.unlink()")
            elif operation == "list_dir":
                lines.append(f"{base_indent}if _file_path.exists() and _file_path.is_dir():")
                lines.append(f"{base_indent}    {save_to} = [f.name for f in _file_path.iterdir()]")
                lines.append(f"{base_indent}else:")
                lines.append(f"{base_indent}    {save_to} = []")

        elif block_type == "util.regex_extract":
            operation = params.get("operation", "search")
            pattern = params.get("pattern", "")
            text = self._render_template(params.get("text", ""), self.class_vars)
            replacement = params.get("replacement", "")
            save_to = params.get("save_to", "regex_result")

            lines.append(f"{base_indent}import re")
            if operation == "match":
                lines.append(f'{base_indent}_match = re.match(r"{pattern}", {text})')
                lines.append(f"{base_indent}{save_to} = _match.groups() if _match else None")
            elif operation == "search":
                lines.append(f'{base_indent}_match = re.search(r"{pattern}", {text})')
                lines.append(f"{base_indent}{save_to} = _match.groups() if _match else None")
            elif operation == "findall":
                lines.append(f'{base_indent}{save_to} = re.findall(r"{pattern}", {text})')
            elif operation == "split":
                lines.append(f'{base_indent}{save_to} = re.split(r"{pattern}", {text})')
            elif operation == "sub":
                lines.append(
                    f'{base_indent}{save_to} = re.sub(r"{pattern}", "{replacement}", {text})'
                )

        elif block_type == "util.array_operation":
            operation = params.get("operation", "append")
            array = params.get("array", "")
            index = params.get("index", 0)
            value_raw = params.get("value", "")
            value_stripped = value_raw.strip()
            # 检查是否是数值字面量
            if value_stripped.lstrip("-").replace(".", "", 1).isdigit():
                value = value_raw
            else:
                value = self._render_template(value_raw, self.class_vars)
            start = params.get("start", 0)
            end = params.get("end", -1)
            separator = params.get("separator", ",")
            save_to = params.get("save_to", "result")

            # 如果数组是类成员变量，添加self.前缀
            array_ref = f"self.{array}" if array in self.class_vars else array

            if operation == "get":
                lines.append(f"{base_indent}{save_to} = {array_ref}[{index}]")
            elif operation == "set":
                lines.append(f"{base_indent}{array_ref}[{index}] = {value}")
            elif operation == "append":
                lines.append(f"{base_indent}{array_ref}.append({value})")
            elif operation == "insert":
                lines.append(f"{base_indent}{array_ref}.insert({index}, {value})")
            elif operation == "remove":
                lines.append(f"{base_indent}{array_ref}.remove({value})")
            elif operation == "pop":
                lines.append(f"{base_indent}{save_to} = {array_ref}.pop({index})")
            elif operation == "length":
                lines.append(f"{base_indent}{save_to} = len({array_ref})")
            elif operation == "contains":
                lines.append(f"{base_indent}{save_to} = {value} in {array_ref}")
            elif operation == "index":
                lines.append(
                    f"{base_indent}{save_to} = {array_ref}.index({value}) if {value} in {array_ref} else -1"
                )
            elif operation == "slice":
                if end == -1:
                    lines.append(f"{base_indent}{save_to} = {array_ref}[{start}:]")
                else:
                    lines.append(f"{base_indent}{save_to} = {array_ref}[{start}:{end}]")
            elif operation == "sort":
                lines.append(f"{base_indent}{array_ref}.sort()")
            elif operation == "reverse":
                lines.append(f"{base_indent}{array_ref}.reverse()")
            elif operation == "join":
                lines.append(
                    f'{base_indent}{save_to} = "{separator}".join(str(x) for x in {array_ref})'
                )
            elif operation == "unique":
                lines.append(f"{base_indent}{save_to} = list(set({array_ref}))")
            elif operation == "extend":
                lines.append(f"{base_indent}{array_ref}.extend({value})")

        elif block_type == "util.type_convert":
            operation = params.get("operation", "to_str")
            value = self._render_template(params.get("value", ""), self.class_vars)
            default_value = params.get("default_value", "")
            save_to = params.get("save_to", "converted")

            # 跟踪转换后的变量作为类成员
            self.class_vars.add(save_to)

            if operation == "to_int":
                lines.append(f"{base_indent}try:")
                lines.append(f"{base_indent}    self.{save_to} = int({value})")
                lines.append(f"{base_indent}except:")
                lines.append(f"{base_indent}    self.{save_to} = {default_value or 0}")
            elif operation == "to_float":
                lines.append(f"{base_indent}try:")
                lines.append(f"{base_indent}    self.{save_to} = float({value})")
                lines.append(f"{base_indent}except:")
                lines.append(f"{base_indent}    self.{save_to} = {default_value or 0.0}")
            elif operation == "to_str":
                lines.append(f"{base_indent}self.{save_to} = str({value})")
            elif operation == "to_bool":
                lines.append(f"{base_indent}self.{save_to} = bool({value})")
            elif operation == "to_list":
                lines.append(f"{base_indent}import json")
                lines.append(f"{base_indent}try:")
                lines.append(
                    f"{base_indent}    self.{save_to} = json.loads({value}) if isinstance({value}, str) else list({value})"
                )
                lines.append(f"{base_indent}except:")
                lines.append(f"{base_indent}    self.{save_to} = []")
            elif operation == "to_dict":
                lines.append(f"{base_indent}import json")
                lines.append(f"{base_indent}try:")
                lines.append(f"{base_indent}    self.{save_to} = json.loads({value})")
                lines.append(f"{base_indent}except:")
                lines.append(f"{base_indent}    self.{save_to} = {{}}")

        elif block_type == "action.send_private":
            user_id = params.get("user_id", "")
            content = self._render_template(params.get("content", ""), self.class_vars)
            lines.append(f"{base_indent}from astrbot.api.event import MessageChain")
            lines.append(f'{base_indent}_target_user = "{user_id}"')
            lines.append(f"{base_indent}_chain = MessageChain().message({content})")
            lines.append(
                f"{base_indent}await self.context.send_private_message(_target_user, _chain)"
            )

        elif block_type == "action.get_member_list":
            save_to = params.get("save_to", "member_list")
            lines.append(f"{base_indent}group = await event.get_group()")
            lines.append(f"{base_indent}if group:")
            lines.append(f"{base_indent}    {save_to} = await group.get_member_list()")
            lines.append(f"{base_indent}    _member_count = len({save_to})")
            lines.append(f"{base_indent}else:")
            lines.append(f"{base_indent}    {save_to} = []")
            lines.append(f"{base_indent}    _member_count = 0")

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
