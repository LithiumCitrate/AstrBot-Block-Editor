#!/usr/bin/env python3
"""
AstrBot Block Compiler CLI
将行为块JSON编译为AstrBot插件代码
"""

import argparse
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from compiler import BlockCompiler


def main():
    parser = argparse.ArgumentParser(
        description="AstrBot Block Compiler - 将行为块JSON编译为AstrBot插件代码",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 编译工作流文件到指定目录
  python compile.py -i workflow.json -o ./output
  
  # 使用自定义块定义
  python compile.py -i workflow.json -b blocks.json -o ./output

  # 验证工作流但不生成代码
  python compile.py -i workflow.json --validate
""",
    )

    parser.add_argument("-i", "--input", type=str, required=True, help="输入工作流JSON文件路径")

    parser.add_argument(
        "-o", "--output", type=str, default="./output", help="输出目录 (默认: ./output)"
    )

    parser.add_argument(
        "-b", "--blocks", type=str, default=None, help="块定义文件路径 (默认: 使用内置定义)"
    )

    parser.add_argument("--validate", action="store_true", help="仅验证工作流，不生成代码")

    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")

    args = parser.parse_args()

    # 确定块定义路径
    if args.blocks:
        blocks_path = Path(args.blocks)
    else:
        # 使用内置块定义
        blocks_path = Path(__file__).parent.parent / "schemas" / "blocks.json"

    # 初始化编译器
    compiler = BlockCompiler(blocks_path)

    # 编译
    if args.validate:
        # 仅验证
        result = compiler.compile_string(Path(args.input).read_text(encoding="utf-8"))
        print(f"验证结果: {'通过' if result['success'] else '失败'}")
    else:
        # 完整编译
        result = compiler.compile_file(args.input, args.output)

    # 输出结果
    if result["success"]:
        print("✅ 编译成功!")
        if "output_dir" in result:
            print(f"   输出目录: {result['output_dir']}")
        if "files" in result:
            print(f"   生成文件: {', '.join(result['files'])}")
    else:
        print("❌ 编译失败!")
        for error in result.get("errors", []):
            print(f"   错误: {error}")

    # 显示警告
    if args.verbose and result.get("warnings"):
        print("\n⚠️ 警告:")
        for warning in result["warnings"]:
            print(f"   {warning}")

    # 非零退出码表示失败
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
