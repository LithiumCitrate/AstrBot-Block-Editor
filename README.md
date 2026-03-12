# AstrBot Block Editor

<div align="center">

![AstrBot Block Editor](https://img.shields.io/badge/AstrBot-Block%20Editor-6366f1?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**可视化 AstrBot 插件开发工具**

通过拖拽行为块，零代码构建 AstrBot 插件

[English](#english) | 简体中文

</div>

---

## ✨ 特性

- 🎨 **现代化可视化编辑器** - 毛玻璃效果、流畅动画、深色主题
- 🧩 **行为块系统** - 20+ 预定义块，覆盖触发、动作、逻辑、工具四大类
- 🔗 **智能连接** - 自动吸附、多分支流程、可视化数据流
- ⚡ **实时编译** - 一键生成完整 AstrBot 插件代码
- 📦 **一键导出** - 直接导出可部署的插件目录

## 📸 截图

```
┌─────────────────────────────────────────────────────────────────────┐
│  🧩 Block Editor          [新建] [打开] [保存] [编译] [导出]          │
├────────────┬────────────────────────────────┬───────────────────────┤
│ 行为块库    │        工作区                   │   属性面板            │
│            │                                │                       │
│ ▶ 触发器    │  ┌──────────────┐              │  类型: trigger.command│
│   指令触发   │  │ ⚡ 指令触发    │              │  ID: block_1         │
│   正则触发   │  │ command: hello│             │  ───────────────     │
│   关键词    │  └──────┬───────┘              │  指令名: [hello    ]  │
│            │         │                       │  别名:   [hi, hey  ]  │
│ 💬 动作     │         ▼                       │                       │
│   回复文本   │  ┌──────────────┐              │  [🗑️ 删除此块]        │
│   回复图片   │  │ 💬 回复文本    │              ├───────────────────────┤
│   延迟      │  │ text: 你好！   │              │   💻 代码预览         │
│            │  └──────────────┘              │   ───────────────     │
│ 🔀 逻辑     │                                │   class MyPlugin...   │
│   条件判断   │                                │   @filter.command...  │
│   循环      │                                │                       │
└────────────┴────────────────────────────────┴───────────────────────┘
```

## 🚀 快速开始

### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/your-username/AstrBot-BlockCompiler.git
cd AstrBot-BlockCompiler

# 安装编译器依赖
pip install -r src/requirements.txt

# 安装 GUI 依赖
pip install PyQt5 PyQtWebEngine
```

### 启动编辑器

```bash
cd gui
python app.py
```

### 命令行编译

```bash
cd src
python compile.py -i ../examples/hello_plugin.json -o ../output
```

## 📖 使用指南

### 1. 创建工作流

在可视化编辑器中：

1. 从左侧**行为块库**拖拽块到工作区
2. 块会自动吸附对齐，形成流程链
3. 点击块在右侧**属性面板**配置参数
4. 点击**编译预览**查看生成的代码
5. 点击**导出插件**保存完整插件目录

### 2. 支持的行为块

| 分类 | 块类型 | 说明 |
|------|--------|------|
| **触发器** | `trigger.command` | 指令触发 `/hello` |
| | `trigger.regex` | 正则匹配 |
| | `trigger.keyword` | 关键词触发 |
| | `trigger.permission` | 权限过滤 |
| **动作** | `action.reply_text` | 回复文本消息 |
| | `action.reply_image` | 回复图片 |
| | `action.delay` | 延迟执行 |
| | `action.http_request` | HTTP 请求 |
| **逻辑** | `logic.if` | 条件判断（支持多分支） |
| | `logic.for_each` | 循环遍历 |
| | `logic.try_catch` | 异常处理 |
| **工具** | `util.get_sender_info` | 获取发送者信息 |
| | `util.random` | 生成随机数 |
| | `util.variable` | 变量操作 |
| | `util.log` | 日志输出 |

### 3. 模板变量

在文本参数中使用 `{变量名}` 引用动态值：

```
你好，{sender_name}！
你的ID是：{sender_id}
消息内容：{message_str}
```

### 4. 多分支流程

逻辑块支持多个输出分支，用不同颜色连线区分：

```
[条件判断] ──(绿色 true)──→ [回复: 欢迎管理员]
    │
    └──(红色 false)──→ [回复: 你好]
```

## 📁 项目结构

```
AstrBot-BlockCompiler/
├── DESIGN.md              # 系统设计文档
├── README.md              # 本文件
├── examples/              # 示例工作流
│   ├── hello_plugin.json
│   ├── test_all_blocks.json
│   └── complex_test.json
├── schemas/               # JSON Schema 定义
│   ├── blocks.json        # 行为块定义
│   └── workflow.json      # 工作流格式
├── src/                   # 编译器核心
│   ├── compile.py         # CLI 入口
│   └── compiler/          # 编译器模块
│       ├── parser.py      # 解析器
│       ├── analyzer.py    # 语义分析
│       └── generator.py   # 代码生成
├── gui/                   # 可视化编辑器
│   ├── app.py             # PyQt5 桌面应用
│   ├── requirements.txt
│   └── web/               # Web 界面
│       ├── index.html
│       ├── blocks.js
│       └── editor.js
└── output/                # 编译输出目录
```

## 🔧 工作流 JSON 格式

```json
{
  "metadata": {
    "name": "my_plugin",
    "author": "user",
    "description": "我的插件",
    "version": "1.0.0"
  },
  "handlers": [
    {
      "id": "handler_1",
      "trigger": {
        "block": "trigger.command",
        "params": { "command": "hello" }
      },
      "flow": [
        {
          "id": "block_1",
          "block": "action.reply_text",
          "params": { "text": "你好，{sender_name}！" }
        }
      ]
    }
  ]
}
```

## 📤 输出文件

编译后生成的插件目录结构：

```
my_plugin/
├── main.py              # 主插件代码
├── metadata.yaml        # 插件元数据
└── _conf_schema.json    # 配置 Schema（可选）
```

将此目录放入 AstrBot 的 `addons/plugins/` 即可使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request


## 🙏 致谢

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) - 强大的聊天机器人框架
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - 跨平台 GUI 框架

---

<div align="center">

**[⬆ 返回顶部](#astrbot-block-editor)**

Made with ❤️ for AstrBot Developers

</div>

---

<a name="english"></a>

## English

A visual plugin development tool for [AstrBot](https://github.com/AstrBotDevs/AstrBot). Build plugins by dragging and connecting behavior blocks - no coding required.

### Features

- 🎨 Modern visual editor with glassmorphism effects
- 🧩 20+ pre-defined blocks covering triggers, actions, logic, and utilities
- 🔗 Smart connections with auto-snap and multi-branch flow support
- ⚡ Real-time compilation to complete AstrBot plugin code
- 📦 One-click export to deployable plugin directory

### Quick Start

```bash
# Install dependencies
pip install PyQt5 PyQtWebEngine

# Launch editor
cd gui && python app.py
```
