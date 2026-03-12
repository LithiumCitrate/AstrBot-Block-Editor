# AstrBot 行为块编译器设计文档

## 1. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    用户交互层 (未来)                          │
│              可视化拖拽编辑器 / JSON编辑器                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    块定义层 (Schema)                         │
│         blocks.json - 定义所有块的参数和连接规则               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    工作流定义层                              │
│         workflow.json - 用户组合的块结构                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    编译器核心                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ 解析器       │→│ 语义分析     │→│ 代码生成     │       │
│  │ Parser      │  │ Analyzer    │  │ Generator   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    输出层                                     │
│    main.py + metadata.yaml + _conf_schema.json              │
└─────────────────────────────────────────────────────────────┘
```

## 2. 块分类与映射

### 2.1 触发块 (Trigger Blocks) → Handler装饰器

| 块类型 | AstrBot映射 | 说明 |
|--------|-------------|------|
| `trigger.command` | `@filter.command("cmd")` | 指令触发 |
| `trigger.regex` | `@filter.regex(r"pattern")` | 正则匹配 |
| `trigger.keyword` | 自定义Handler内判断 | 关键词包含 |
| `trigger.event_message_type` | `@filter.event_message_type()` | 群聊/私聊 |
| `trigger.platform` | `@filter.platform_adapter_type()` | 平台过滤 |
| `trigger.permission` | `@filter.permission_type()` | 权限过滤 |
| `trigger.on_loaded` | `@filter.on_astrbot_loaded()` | Bot加载完成 |
| `trigger.on_llm_request` | `@filter.on_llm_request()` | LLM请求钩子 |
| `trigger.schedule` | 需要定时任务库 | 定时触发 |

### 2.2 动作块 (Action Blocks) → Event方法调用

| 块类型 | AstrBot映射 | 说明 |
|--------|-------------|------|
| `action.reply_text` | `yield event.plain_result("text")` | 回复文本 |
| `action.reply_image` | `yield event.image_result("url")` | 回复图片 |
| `action.reply_chain` | `yield event.chain_result([...])` | 回复消息链 |
| `action.send_message` | `await self.context.send_message(umo, chain)` | 主动发送 |
| `action.http_request` | `aiohttp` 异步请求 | HTTP调用 |
| `action.delay` | `await asyncio.sleep(seconds)` | 延时 |
| `action.call_llm` | `provider.text_chat()` | 调用LLM |
| `action.stop_event` | `event.stop_event()` | 停止传播 |

### 2.3 逻辑块 (Logic Blocks) → Python控制流

| 块类型 | Python映射 | 说明 |
|--------|------------|------|
| `logic.if` | `if condition: ... else: ...` | 条件判断 |
| `logic.switch` | `if/elif/else` 链 | 多分支 |
| `logic.for_each` | `for item in items: ...` | 循环遍历 |
| `logic.while` | `while condition: ...` | 条件循环 |
| `logic.try_catch` | `try: ... except: ...` | 异常处理 |

### 2.4 工具块 (Utility Blocks) → 数据获取

| 块类型 | AstrBot映射 | 说明 |
|--------|-------------|------|
| `util.get_sender_info` | `event.get_sender_id/name()` | 发送者信息 |
| `util.get_group_info` | `event.get_group_id()` | 群信息 |
| `util.get_message` | `event.message_str` | 消息内容 |
| `util.random` | `random.randint/choice()` | 随机数 |
| `util.time_now` | `datetime.now()` | 当前时间 |
| `util.variable` | `self.vars[key]` | 变量存取 |

## 3. 数据结构设计

### 3.1 块定义 Schema (blocks.json)

```json
{
  "blocks": {
    "trigger.command": {
      "type": "trigger",
      "category": "trigger",
      "display_name": "指令触发",
      "description": "当用户发送指定指令时触发",
      "icon": "terminal",
      "params": {
        "command": {
          "type": "string",
          "required": true,
          "default": "",
          "description": "指令名称（不含/前缀）"
        },
        "alias": {
          "type": "array",
          "items": "string",
          "required": false,
          "default": [],
          "description": "指令别名"
        }
      },
      "outputs": {
        "triggered": {
          "type": "flow",
          "description": "触发后执行的流程"
        },
        "event": {
          "type": "event",
          "description": "事件对象"
        },
        "message_str": {
          "type": "string",
          "description": "消息文本"
        },
        "sender_id": {
          "type": "string",
          "description": "发送者ID"
        }
      }
    },
    "action.reply_text": {
      "type": "action",
      "category": "action",
      "display_name": "回复文本",
      "description": "回复一条纯文本消息",
      "params": {
        "text": {
          "type": "string",
          "required": true,
          "default": "",
          "description": "回复的文本内容",
          "supports_template": true
        }
      },
      "inputs": {
        "flow": {
          "type": "flow",
          "required": true
        }
      },
      "outputs": {
        "next": {
          "type": "flow",
          "description": "继续执行的流程"
        }
      }
    }
  }
}
```

### 3.2 工作流定义 Schema (workflow.json)

```json
{
  "metadata": {
    "name": "my_plugin",
    "author": "user",
    "description": "我的插件",
    "version": "1.0.0"
  },
  "variables": [
    {
      "name": "counter",
      "type": "int",
      "default": 0,
      "persistent": true
    }
  ],
  "handlers": [
    {
      "id": "handler_1",
      "name": "hello_handler",
      "trigger": {
        "block": "trigger.command",
        "params": {
          "command": "hello"
        }
      },
      "flow": [
        {
          "id": "block_1",
          "block": "action.reply_text",
          "params": {
            "text": "你好，{sender_name}！"
          },
          "inputs": {
            "flow": "@handler_1.trigger"
          }
        }
      ]
    }
  ]
}
```

## 4. 编译器逻辑

### 4.1 编译流程

```
1. 解析阶段 (Parser)
   ├─ 解析 workflow.json
   ├─ 验证块类型存在性
   ├─ 解析块参数和连接
   └─ 构建AST (抽象语法树)

2. 语义分析 (Analyzer)
   ├─ 类型检查
   ├─ 变量引用检查
   ├─ 流程连接验证
   ├─ 循环依赖检测
   └─ 生成符号表

3. 代码生成 (Generator)
   ├─ 生成插件类结构
   ├─ 生成Handler方法
   ├─ 生成装饰器链
   ├─ 生成方法体代码
   └─ 生成辅助文件
```

### 4.2 代码生成模板

**输入工作流：**
```json
{
  "handlers": [{
    "id": "h1",
    "trigger": {"block": "trigger.command", "params": {"command": "hello"}},
    "flow": [
      {"id": "b1", "block": "action.reply_text", "params": {"text": "你好！"}}
    ]
  }]
}
```

**输出代码：**
```python
from astrbot.api import star
from astrbot.api.event import AstrMessageEvent, filter

class MyPlugin(star.Star):
    def __init__(self, context: star.Context) -> None:
        self.context = context
    
    @filter.command("hello")
    async def handler_h1(self, event: AstrMessageEvent):
        '''hello指令处理器'''
        yield event.plain_result("你好！")
    
    async def terminate(self):
        pass
```

### 4.3 复杂流程编译

**条件分支：**
```json
{
  "flow": [
    {"id": "b1", "block": "logic.if", "params": {"condition": "{sender_id} == '123456'"},
     "branches": {
       "true": [{"id": "b2", "block": "action.reply_text", "params": {"text": "管理员好"}}],
       "false": [{"id": "b3", "block": "action.reply_text", "params": {"text": "你好"}}]
     }
    }
  ]
}
```

**编译结果：**
```python
if event.get_sender_id() == '123456':
    yield event.plain_result("管理员好")
else:
    yield event.plain_result("你好")
```

## 5. 变量系统

### 5.1 内置变量

| 变量名 | 来源 | 说明 |
|--------|------|------|
| `{message_str}` | event | 消息文本 |
| `{sender_id}` | event | 发送者ID |
| `{sender_name}` | event | 发送者昵称 |
| `{group_id}` | event | 群ID |
| `{self_id}` | event | 机器人ID |
| `{platform}` | event | 平台名称 |

### 5.2 自定义变量

```json
{
  "variables": [
    {"name": "user_points", "type": "dict", "persistent": true}
  ]
}
```

编译后：
```python
class MyPlugin(star.Star):
    def __init__(self, context: star.Context) -> None:
        self.context = context
        self.user_points = {}  # 持久化需要额外处理
```

## 6. 错误处理

### 6.1 编译时错误

- 块类型不存在
- 参数类型不匹配
- 流程连接断裂
- 循环依赖

### 6.2 运行时错误处理

自动生成的try-catch包装：
```python
async def handler_xxx(self, event: AstrMessageEvent):
    try:
        # 用户定义的逻辑
    except Exception as e:
        logger.error(f"Handler error: {e}")
        yield event.plain_result("处理出错，请稍后重试")
```

## 7. 扩展机制

### 7.1 自定义块

用户可定义新块类型：
```json
{
  "custom_blocks": {
    "my_custom_block": {
      "template": "custom_block.py.jinja2",
      "params": {...}
    }
  }
}
```

### 7.2 块组合（宏）

将常用块序列保存为可复用组件：
```json
{
  "macros": {
    "welcome_user": {
      "blocks": [
        {"block": "action.reply_text", "params": {"text": "欢迎！"}},
        {"block": "action.reply_image", "params": {"url": "welcome.jpg"}}
      ]
    }
  }
}
```

## 8. 输出文件结构

```
output/
├── my_plugin/
│   ├── main.py              # 主插件代码
│   ├── metadata.yaml        # 插件元数据
│   ├── _conf_schema.json    # 配置Schema（可选）
│   └── requirements.txt     # 依赖（可选）
```
