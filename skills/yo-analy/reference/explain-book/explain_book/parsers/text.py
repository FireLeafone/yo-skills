from __future__ import annotations
import sys
from pathlib import Path

# 字节顺序标记（BOM），长的在前：UTF-32 LE 的 BOM（"ff fe 00 00"）以
# UTF-16 LE 的 BOM（"ff fe"）开头，所以必须先检查 UTF-32 再检查 UTF-16。
_BOMS = (
    (b"\xef\xbb\xbf", "utf-8-sig"),
    (b"\xff\xfe\x00\x00", "utf-32"),
    (b"\x00\x00\xfe\xff", "utf-32"),
    (b"\xff\xfe", "utf-16"),
    (b"\xfe\xff", "utf-16"),
)


def read_text_file(path: str) -> str | None:
    try:
        data = Path(path).read_bytes()
    except Exception as e:
        print(f"  [warn] read_text_file failed: {type(e).__name__}: {e}", file=sys.stderr)
        return None

    # 存在 BOM 时按 BOM 解码（utf-16/utf-32 编解码器会自动剥掉 BOM 并
    # 自动选择字节序）。
    for bom, encoding in _BOMS:
        if data.startswith(bom):
            try:
                return data.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                break

    # 没有（可用的）BOM：面向中文文本的回退链 —— 先按 UTF-8 解码，失败后
    # 尝试 GB18030（覆盖 GBK/GB2312，是中文文本文件最常见的非 UTF 编码）。
    for encoding in ("utf-8", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None
