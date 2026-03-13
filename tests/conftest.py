"""
pytest 配置文件
"""
import sys
from pathlib import Path

import pytest

# 添加 src 目录到 Python 路径
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_workflow():
    """示例工作流 JSON"""
    return {
        "metadata": {
            "name": "test_plugin",
            "author": "test_user",
            "description": "测试插件",
            "version": "1.0.0"
        },
        "variables": [],
        "handlers": [
            {
                "id": "handler_1",
                "name": "hello_handler",
                "description": "测试处理器",
                "trigger": {
                    "block": "trigger.command",
                    "params": {"command": "hello"}
                },
                "flow": [
                    {
                        "id": "block_1",
                        "block": "action.reply_text",
                        "params": {"text": "你好！"}
                    }
                ]
            }
        ]
    }


@pytest.fixture
def complex_workflow():
    """复杂工作流 JSON（包含条件分支）"""
    return {
        "metadata": {
            "name": "complex_plugin",
            "author": "test_user",
            "description": "复杂测试插件",
            "version": "1.0.0"
        },
        "variables": [
            {"name": "counter", "type": "int", "default": 0}
        ],
        "handlers": [
            {
                "id": "handler_1",
                "name": "check_admin",
                "trigger": {
                    "block": "trigger.command",
                    "params": {"command": "check"}
                },
                "flow": [
                    {
                        "id": "block_1",
                        "block": "logic.if",
                        "params": {"condition": "{sender_id} == '123456'"},
                        "branches": {
                            "true": [
                                {"id": "b2", "block": "action.reply_text", "params": {"text": "管理员好"}}
                            ],
                            "false": [
                                {"id": "b3", "block": "action.reply_text", "params": {"text": "你好"}}
                            ]
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture
def blocks_path():
    """块定义文件路径"""
    return Path(__file__).parent.parent / "schemas" / "blocks.json"
