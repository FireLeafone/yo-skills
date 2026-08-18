import sys
from explain_book.utils import main as utils_main

def main():
    # 强制 stdout/stderr 使用 UTF-8，避免 Windows 控制台报 UnicodeEncodeError
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            # 流不支持 reconfigure 时忽略（例如测试期间的 mock 流）
            pass
    utils_main()

# 导出 main，供打包后的 console scripts 入口点使用
if __name__ == "__main__":
    main()
