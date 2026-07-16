#!/usr/bin/env python3
"""安全地更新小说 progress.md 进度文件。

读取现有 progress.md，按 JSON spec 增量更新标准区块，保留所有未知区块和备注。
只修改 spec 中显式提到的字段，不推断、不脑补。
"""

import argparse
import json
import re
import sys
from copy import deepcopy
from pathlib import Path


KNOWN_SECTIONS = {
    "元信息",
    "总体进度",
    "章节进度",
    "人物进度",
    "剧情伏笔跟踪",
    "时间线进度",
}


def parse_sections(text: str) -> list[tuple[str | None, list[str]]]:
    """把 markdown 按 ## 一级标题切分成 (标题, 正文行) 列表。

    第一个区块标题为 None，表示文件最开头到第一个 ## 之前的内容。
    """
    sections: list[tuple[str | None, list[str]]] = []
    current_title: str | None = None
    current_body: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        m = re.match(r"^##\s+(.+)$", line)
        if m:
            sections.append((current_title, current_body))
            current_title = m.group(1).strip()
            current_body = []
        else:
            current_body.append(line)

    sections.append((current_title, current_body))
    return sections


def render_sections(sections: list[tuple[str | None, list[str]]]) -> str:
    lines: list[str] = []
    for idx, (title, body) in enumerate(sections):
        if title is not None:
            lines.append(f"## {title}")
        # 去掉末尾空行，但保留区块间一个空行
        trimmed = list(body)
        while trimmed and trimmed[-1] == "":
            trimmed.pop()
        lines.extend(trimmed)
        if title is not None and idx < len(sections) - 1:
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def find_section_index(sections: list[tuple[str | None, list[str]]], title: str) -> int:
    for i, (t, _) in enumerate(sections):
        if t == title:
            return i
    return -1


def ensure_section(sections: list[tuple[str | None, list[str]]], title: str, default_body: list[str]) -> int:
    idx = find_section_index(sections, title)
    if idx >= 0:
        return idx
    sections.append((title, deepcopy(default_body)))
    return len(sections) - 1


def update_meta_info(body: list[str], meta: dict) -> list[str]:
    if not meta:
        return body
    new_body: list[str] = []
    for line in body:
        if meta.get("novel_name") and line.startswith("- 小说名："):
            line = f"- 小说名：{meta['novel_name']}"
        elif meta.get("genre") and line.startswith("- 类型："):
            line = f"- 类型：{meta['genre']}"
        elif meta.get("created_date") and line.startswith("- 创建日期："):
            line = f"- 创建日期：{meta['created_date']}"
        elif meta.get("current_chapter") and line.startswith("- 当前章节进度："):
            line = f"- 当前章节进度：{meta['current_chapter']}章"
        new_body.append(line)
    return new_body


def update_checkbox_section(body: list[str], updates: dict[str, bool]) -> list[str]:
    """更新复选框列表。updates 的 key 是条目中的关键词，value 为是否勾选。"""
    if not updates:
        return body
    new_body: list[str] = []
    for line in body:
        new_line = line
        if re.match(r"^-\s*\[[ xX]\]", line):
            for key, checked in updates.items():
                if key in line:
                    marker = "x" if checked else " "
                    new_line = re.sub(r"^(-\s*\[)[ xX](\])", rf"\g<1>{marker}\g<2>", line)
                    break
        new_body.append(new_line)
    return new_body


def parse_table(body: list[str]) -> tuple[list[str], list[str], list[list[str]]]:
    """解析 markdown 表格，返回 (header_lines, separator_lines, data_rows)。"""
    header: list[str] = []
    separator: list[str] = []
    rows: list[list[str]] = []
    stage = "before"
    for line in body:
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c]
        if not cells:
            continue
        if stage == "before":
            header.append(line)
            stage = "sep"
        elif stage == "sep":
            separator.append(line)
            stage = "rows"
        else:
            rows.append(cells)
    return header, separator, rows


def render_table(header: list[str], separator: list[str], rows: list[list[str]]) -> list[str]:
    if not header:
        return []
    return header + separator + ["| " + " | ".join(cells) + " |" for cells in rows]


def update_chapter_section(body: list[str], chapters: dict[str, dict]) -> list[str]:
    if not chapters:
        return body
    header, separator, rows = parse_table(body)
    if not header:
        return body

    row_by_id: dict[str, list[str]] = {}
    for r in rows:
        if r:
            row_by_id[r[0]] = r

    for chap_id, updates in chapters.items():
        if chap_id in row_by_id:
            r = row_by_id[chap_id]
            # 补齐到 6 列
            while len(r) < 6:
                r.append("-")
            if updates.get("title"):
                r[1] = updates["title"]
            if updates.get("status"):
                r[2] = updates["status"]
            if "word_count" in updates:
                r[3] = str(updates["word_count"])
            if updates.get("characters"):
                r[4] = updates["characters"]
            if "summary" in updates:
                r[5] = updates["summary"] if updates["summary"] else "-"
        else:
            new_row = [
                chap_id,
                updates.get("title", "待命名"),
                updates.get("status", "未开始"),
                str(updates.get("word_count", 0)),
                updates.get("characters", "-"),
                updates.get("summary", "-"),
            ]
            row_by_id[chap_id] = new_row

    # 按序号排序：先尝试数字排序，否则按原顺序
    def sort_key(item):
        key = item[0]
        try:
            return (0, int(key))
        except ValueError:
            return (1, key)

    sorted_rows = [r for _, r in sorted(row_by_id.items(), key=lambda x: sort_key(x))]
    table_lines = render_table(header, separator, sorted_rows)

    # 把表格替换回原 body 中表格所在区域
    table_start = None
    table_end = None
    for i, line in enumerate(body):
        if line.strip().startswith("|"):
            if table_start is None:
                table_start = i
            table_end = i
    if table_start is None:
        return body
    return body[:table_start] + table_lines + body[table_end + 1 :]


def update_foreshadowing_section(body: list[str], fs_spec: dict) -> list[str]:
    if not fs_spec:
        return body
    header, separator, rows = parse_table(body)
    if not header:
        return body

    row_by_name: dict[str, list[str]] = {}
    for r in rows:
        if len(r) >= 2:
            row_by_name[r[1]] = r

    # 新增伏笔
    for add in fs_spec.get("add", []):
        name = add["name"]
        if name in row_by_name:
            continue
        next_id = 1
        for r in rows:
            try:
                next_id = max(next_id, int(r[0]) + 1)
            except (ValueError, IndexError):
                pass
        new_row = [
            f"{next_id:03d}",
            name,
            add.get("status", "未回收"),
            add.get("bury_chapter", "-"),
            add.get("resolve_chapter", "-"),
            add.get("summary", "-"),
        ]
        row_by_name[name] = new_row

    # 回收伏笔
    for resolve in fs_spec.get("resolve", []):
        name = resolve["name"]
        if name in row_by_name:
            r = row_by_name[name]
            r[2] = "已回收"
            if resolve.get("resolve_chapter"):
                r[4] = resolve["resolve_chapter"]

    sorted_rows = sorted(row_by_name.values(), key=lambda r: int(r[0]) if r[0].isdigit() else 9999)
    table_lines = render_table(header, separator, sorted_rows)

    table_start = None
    table_end = None
    for i, line in enumerate(body):
        if line.strip().startswith("|"):
            if table_start is None:
                table_start = i
            table_end = i
    if table_start is None:
        return body
    return body[:table_start] + table_lines + body[table_end + 1 :]


def apply_spec(text: str, spec: dict) -> str:
    sections = parse_sections(text)

    # 元信息
    meta = spec.get("meta_info", {})
    if meta:
        idx = find_section_index(sections, "元信息")
        if idx >= 0:
            sections[idx] = ("元信息", update_meta_info(sections[idx][1], meta))

    # 总体进度
    overall = spec.get("overall_progress", {})
    if overall:
        idx = ensure_section(sections, "总体进度", ["- [ ] 大纲完成", "- [ ] 第 1 章完成"])
        sections[idx] = ("总体进度", update_checkbox_section(sections[idx][1], overall))

    # 章节进度
    chapters = spec.get("chapters", {})
    if chapters:
        idx = find_section_index(sections, "章节进度")
        if idx >= 0:
            sections[idx] = ("章节进度", update_chapter_section(sections[idx][1], chapters))

    # 人物进度
    characters = spec.get("character_progress", {})
    if characters:
        idx = ensure_section(
            sections,
            "人物进度",
            [
                "- [ ] 主角设定、等级（职位）、技能、结局等进度",
                "- [ ] 主要配角设定、等级（职位）、技能、结局等进度",
                "- [ ] 反派设定、等级（职位）、技能、结局等进度",
            ],
        )
        sections[idx] = ("人物进度", update_checkbox_section(sections[idx][1], characters))

    # 剧情伏笔跟踪
    fs_spec = spec.get("foreshadowing", {})
    if fs_spec:
        idx = find_section_index(sections, "剧情伏笔跟踪")
        if idx >= 0:
            sections[idx] = ("剧情伏笔跟踪", update_foreshadowing_section(sections[idx][1], fs_spec))

    # 时间线进度
    timeline = spec.get("timeline_progress", {})
    if timeline:
        idx = ensure_section(
            sections,
            "时间线进度",
            ["- [ ] 主线时间线梳理", "- [ ] 支线时间线梳理"],
        )
        sections[idx] = ("时间线进度", update_checkbox_section(sections[idx][1], timeline))

    return render_sections(sections)


def build_summary(spec: dict) -> dict:
    summary: dict = {
        "updated_meta": bool(spec.get("meta_info")),
        "overall_items": list(spec.get("overall_progress", {}).keys()),
        "chapters": list(spec.get("chapters", {}).keys()),
        "character_items": list(spec.get("character_progress", {}).keys()),
        "added_foreshadowing": [a["name"] for a in spec.get("foreshadowing", {}).get("add", [])],
        "resolved_foreshadowing": [r["name"] for r in spec.get("foreshadowing", {}).get("resolve", [])],
        "timeline_items": list(spec.get("timeline_progress", {}).keys()),
    }
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="安全更新小说 progress.md")
    parser.add_argument("--input", "-i", required=True, type=Path, help="输入 progress.md 路径")
    parser.add_argument("--spec", "-s", required=True, type=Path, help="JSON 更新规则文件路径")
    parser.add_argument("--output", "-o", type=Path, help="输出路径（默认覆盖输入）")
    parser.add_argument("--summary", type=Path, help="可选：将变更摘要写入该 JSON 文件")
    args = parser.parse_args()

    input_path: Path = args.input
    if not input_path.exists():
        print(f"错误：输入文件不存在：{input_path}", file=sys.stderr)
        return 1

    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"错误：spec JSON 解析失败：{e}", file=sys.stderr)
        return 1

    original_text = input_path.read_text(encoding="utf-8")
    new_text = apply_spec(original_text, spec)

    output_path = args.output or input_path
    output_path.write_text(new_text, encoding="utf-8")

    summary = build_summary(spec)
    summary_json = json.dumps(summary, ensure_ascii=False, indent=2)
    sys.stdout.buffer.write(summary_json.encode("utf-8"))
    sys.stdout.buffer.write(b"\n")

    if args.summary:
        args.summary.write_text(summary_json, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
