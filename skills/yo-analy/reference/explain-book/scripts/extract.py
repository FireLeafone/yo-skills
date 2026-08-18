#!/usr/bin/env python3
"""
从文档中提取文本，供 explain-book 处理。
保持向后兼容的入口包装脚本。
"""

import os
import sys

# 强制 stdout/stderr 使用 UTF-8，使提取出的文本、署名行中的分隔符
# 以及依赖检查符号（✓ / ✗）不会在默认使用遗留代码页
# （如 GBK / cp936）的 Windows 控制台上抛出 UnicodeEncodeError。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# 确保项目根目录（'explain_book' 包所在目录）在 sys.path 中，
# 这样无论当前工作目录是什么，都能可靠地导入这个模块化包。
sys.path.insert(0, str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from explain_book.cli import main

if __name__ == "__main__":
    main()
