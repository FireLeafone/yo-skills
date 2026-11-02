#!/usr/bin/env python3
"""章节文字检查脚本：字数区间、对话密度、破折号与 AI 套话。

用法：
    python3 presets/check_dialogue_density.py                          # 递归扫描 chapters/ 下所有章节
    python3 presets/check_dialogue_density.py chapters/volume-01/021_章节名.md ...
    python3 presets/check_dialogue_density.py --min 3000 --max 4000 chapters/volume-01/

判定口径（与 checked.md 一致）：
    字数：CJK 字符 + 英文单词（同 count_words.py）
    对话密度：中文引号 "" / 「」内的 CJK 字符数 ÷ 全文 CJK 字符数，要求 50%–80%
    禁用：破折号 "——"
    提醒：AI 套话（显然、众所周知、不得不说）
"""

import argparse
import re
import sys
from pathlib import Path

DIALOGUE_RE = re.compile(r'"([^"]*)"|「([^」]*)」')
CJK_RE = re.compile(r"[一-鿿]")
WORD_RE = re.compile(r"[a-zA-Z]+")
AI_PHRASES = ["显然", "众所周知", "不得不说"]
DIALOGUE_MIN, DIALOGUE_MAX = 50.0, 80.0


def cjk_len(text: str) -> int:
    return len(CJK_RE.findall(text))


def check_file(path: Path, min_words: int, max_words: int) -> bool:
    text = path.read_text(encoding="utf-8")
    total = cjk_len(text) + len(WORD_RE.findall(text))
    cjk = cjk_len(text)
    dialogue = sum(cjk_len(m.group(1) or m.group(2) or "") for m in DIALOGUE_RE.finditer(text))
    ratio = dialogue / cjk * 100 if cjk else 0.0
    dashes = text.count("——")
    phrases = {p: text.count(p) for p in AI_PHRASES if p in text}

    problems = []
    if not (min_words <= total <= max_words):
        problems.append(f"字数 {total} 不在 {min_words}-{max_words}")
    if not (DIALOGUE_MIN <= ratio <= DIALOGUE_MAX):
        problems.append(f"对话密度 {ratio:.1f}% 不在 {DIALOGUE_MIN:.0f}%-{DIALOGUE_MAX:.0f}%")
    if dashes:
        problems.append(f"含破折号「——」{dashes} 处")

    status = "PASS" if not problems else "FAIL"
    print(f"[{status}] {path}")
    print(f"       字数 {total}（CJK {cjk}）｜对话密度 {ratio:.1f}%（{dialogue} 字）｜破折号 {dashes}")
    if phrases:
        print(f"       AI 套话提醒: {', '.join(f'{k}×{v}' for k, v in phrases.items())}")
    for p in problems:
        print(f"       ✗ {p}")
    return not problems


def collect(paths: list[str]) -> list[Path]:
    files = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            files.extend(f for f in sorted(p.rglob("*.md")) if re.match(r"\d{3}_", f.name))
        elif p.is_file():
            files.append(p)
        else:
            print(f"路径不存在，跳过: {raw}", file=sys.stderr)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description="章节字数与对话密度检查")
    parser.add_argument("paths", nargs="*", help="章节文件或目录（默认递归扫描 chapters/）")
    parser.add_argument("--min", type=int, default=3000, help="单章字数下限（默认 3000）")
    parser.add_argument("--max", type=int, default=5000, help="单章字数上限（默认 5000）")
    args = parser.parse_args()

    files = collect(args.paths or ["chapters"])
    if not files:
        print("未找到任何章节文件。", file=sys.stderr)
        return 2

    results = [check_file(f, args.min, args.max) for f in files]
    print(f"\n共检查 {len(results)} 章：PASS {sum(results)}，FAIL {len(results) - sum(results)}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
