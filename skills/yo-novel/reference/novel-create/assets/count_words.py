#!/usr/bin/env python3
"""统计小说项目总字数与各章节字数."""

import os
import re
from pathlib import Path


CHAPTERS_DIR = Path("chapters")
PRESETS_DIR = Path("presets")


def count_chinese_and_words(text: str) -> int:
    """粗略统计中文字符与英文单词数."""
    chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
    words = len(re.findall(r"[a-zA-Z]+", text))
    return chinese + words


def read_markdown_files(directory: Path) -> dict[str, int]:
    counts = {}
    if not directory.exists():
        return counts
    for path in sorted(directory.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        counts[path.name] = count_chinese_and_words(text)
    return counts


def main():
    chapter_counts = read_markdown_files(CHAPTERS_DIR)
    preset_counts = read_markdown_files(PRESETS_DIR)

    total = sum(chapter_counts.values()) + sum(preset_counts.values())

    print("=" * 40)
    print(f"小说总字数（粗略）: {total}")
    print("=" * 40)

    if chapter_counts:
        print("\n各章节字数:")
        for name, count in chapter_counts.items():
            print(f"  {name}: {count}")

    if preset_counts:
        print("\n设定文档字数:")
        for name, count in preset_counts.items():
            print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
