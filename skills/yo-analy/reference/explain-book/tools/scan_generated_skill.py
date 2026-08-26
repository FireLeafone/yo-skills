#!/usr/bin/env python3
"""Advisory scan for prompt injection and unsafe authority in generated skills."""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


MAX_SKILL_FILES = 1_000
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 20 * 1024 * 1024
SUPPORTING_FILENAMES = (
    "outline.md",
    "mental-models.md",
    "principles.md",
    "writing-style.md",
    "techniques.md",
    "anti-patterns.md",
    "glossary.md",
    # 兼容 book-to-skill 风格的目录布局，以防被扫描的 skill 来自该工具
    "patterns.md",
    "cheatsheet.md",
)
SUPPORTING_DIRS = ("chapters", "settings")

# 复用提取器的不可见码位集合，而不是在这里重复定义一份，
# 这样两道注入防线不会因各自维护而逐渐漂移不一致。历史上确实漂移过：
# 提取器没有剥离 U+2060，而本扫描器会标记它，导致生成的 skill
# 因为一个本应在提取阶段就被移除的字符而收到告警。
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from explain_book.sanitize import is_invisible_codepoint  # noqa: E402

_CONTENT_RULES = (
    (
        "prompt.ignore_previous",
        re.compile(
            r"\bignore\s+(?:(?:all|any|the)\s+)?(?:previous|prior)\s+"
            r"(?:instructions?|prompts?|rules?|messages?)\b",
            re.IGNORECASE,
        ),
        "contains an instruction-override phrase",
    ),
    (
        "prompt.disregard_system",
        re.compile(r"\bdisregard\s+(?:the\s+)?(?:system|developer)\b", re.IGNORECASE),
        "contains a system-instruction override phrase",
    ),
    (
        "prompt.role_reassignment",
        re.compile(r"\byou\s+are\s+now\b", re.IGNORECASE),
        "contains a role-reassignment phrase",
    ),
    (
        "prompt.fake_system_prefix",
        re.compile(r"^\s*(?:[-*]\s*)?(?:system|developer)\s*:", re.IGNORECASE),
        "contains a system-like message prefix",
    ),
    (
        "prompt.system_tag",
        re.compile(r"<\s*/?\s*system\b[^>]*>", re.IGNORECASE),
        "contains a system-message tag",
    ),
    (
        "prompt.chat_template_tag",
        re.compile(r"<\|\s*im_start\s*\|>|\[\s*INST\s*\]", re.IGNORECASE),
        "contains a model chat-template delimiter",
    ),
    (
        # 只匹配带分隔符的形式——即 token 本身，而非英文短语。
        # 下面列出的几个家族是真实聊天模板和工具调用协议中会出现的形式：
        #
        #   <tool_call> … </tool_call>     Hermes / Qwen 风格
        #   <|tool_call|>                  特殊 token 风格
        #   [TOOL_CALL] / [/tool_call]     方括号风格
        #   {{tool_call}}                  模板占位符
        #   "tool_call"                    JSON 键或值
        #
        # 如果改为匹配普通散文文本，那么每本讲解"什么是工具调用"的书都会
        # 触发告警——而这正是本转换器最常处理的 agent 与提示词类书籍。
        # 一个对整类内容必定误报的关卡，只会教人养成挥手放行的习惯，
        # 其代价比误报本身更高。
        "prompt.tool_call_tag",
        re.compile(
            r"""<\|?\s*/?\s*tool[_ -]?call\s*\|?>      # <tool_call>, </tool_call>, <|tool_call|>
              | \[\s*/?\s*tool[_ -]?call\s*\]          # [TOOL_CALL], [/tool_call]
              | \{\{\s*/?\s*tool[_ -]?call\s*\}\}      # {{tool_call}}
              | "\s*tool[_ -]?call\s*"                 # JSON key or value
            """,
            re.IGNORECASE | re.VERBOSE,
        ),
        "contains a tool-call control token",
    ),
)

_EXFILTRATION_TERM = re.compile(r"\bexfiltrat(?:e|es|ed|ing|ion)\b", re.IGNORECASE)
_OUTBOUND_TERM = re.compile(
    r"\b(?:curl|wget|send|post|upload|transmit)\b|https?://",
    re.IGNORECASE,
)
_SENSITIVE_TERM = re.compile(
    r"(?:\.env\b|\bbase64\b|\bsecrets?\b|\bcredentials?\b|\bapi[_ -]?keys?\b)",
    re.IGNORECASE,
)


class ScanError(RuntimeError):
    """当扫描器无法完整检查生成的 skill 时抛出。"""


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule_id: str
    message: str


def _is_invisible(codepoint: int) -> bool:
    return is_invisible_codepoint(codepoint)


def _terminal_safe(value: str) -> str:
    """打印不可信路径前，先转义其中的控制字符与非 ASCII 字符。"""
    return value.encode("unicode_escape", errors="backslashreplace").decode("ascii")


def _frontmatter_line_numbers(lines: Sequence[str]) -> set[int]:
    if not lines or lines[0].strip() != "---":
        return set()
    for index, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            return set(range(2, index))
    return set()


def _walk_markdown(directory: Path) -> list[Path]:
    """收集 ``directory`` 下任意深度的所有 ``*.md`` 文件，忽略符号链接。

    使用 ``os.walk(followlinks=False)`` 而非 ``Path.rglob``：在 Python 3.13
    之前，``rglob`` 会进入符号链接目录，这会让生成的 skill 把扫描器带到
    自身目录树之外。符号链接*文件*仍保留在列表中，稍后由
    :func:`_read_skill_files` 拒绝，这样被植入的符号链接会以错误形式报告，
    而不是被静默跳过。
    """
    found: list[Path] = []
    for walk_root, _dirnames, filenames in os.walk(directory, followlinks=False):
        for filename in filenames:
            if filename.lower().endswith(".md"):
                found.append(Path(walk_root) / filename)
    return found


def unscanned_markdown(path: Path) -> list[str]:
    """列出存在于 skill 目录中、但在扫描范围之外的 Markdown 文件。

    扫描范围被刻意限定为 explain-book 所生成的内容（SKILL.md 或
    README.md、各支持文件以及 ``chapters/``），因此目录里无关的笔记
    不会被扫描，也不可能产生误报。真正的风险在于*报告环节*：如果一边
    打印"扫描通过"，一边却有 agent 会照常读取的文件从未被打开检查，
    那就是虚假的安全感。把这些文件列出来，可以让受限的扫描范围保持诚实。
    """
    requested = path.expanduser()
    root = (
        requested.parent
        if requested.name.lower() in ("skill.md", "readme.md")
        else requested
    )
    root = root.resolve(strict=True)
    scanned = set(_collect_skill_files(requested))
    return sorted(
        candidate.relative_to(root).as_posix()
        for candidate in _walk_markdown(root)
        if candidate not in scanned
    )


def _collect_skill_files(skill_dir: Path) -> list[Path]:
    requested = skill_dir.expanduser()
    if requested.name.lower() in ("skill.md", "readme.md") and requested.is_file():
        requested = requested.parent
    if requested.is_symlink():
        raise ScanError("the generated skill directory must not be a symbolic link")
    try:
        root = requested.resolve(strict=True)
    except OSError as exc:
        raise ScanError("the generated skill directory does not exist") from exc
    if not root.is_dir():
        raise ScanError("the generated skill path is not a directory")

    master = root / "SKILL.md"
    if master.is_symlink():
        raise ScanError("SKILL.md must be a real file, not a symbolic link")
    if not master.is_file():
        # explain-book 现在输出的是普通文档集，其主文档为 README.md
        # 而非可安装的 SKILL.md；两种布局都接受。
        master = root / "README.md"
        if master.is_symlink() or not master.is_file():
            raise ScanError(
                "neither SKILL.md nor README.md found as a real file in the "
                "generated directory"
            )

    candidates = {master}
    for filename in SUPPORTING_FILENAMES:
        supporting_file = root / filename
        if supporting_file.is_symlink():
            raise ScanError(f"{filename} must be a real file, not a symbolic link")
        if supporting_file.exists():
            if not supporting_file.is_file():
                raise ScanError(f"{filename} must be a real file")
            candidates.add(supporting_file)

    for dirname in SUPPORTING_DIRS:
        subdir = root / dirname
        if subdir.exists():
            if subdir.is_symlink() or not subdir.is_dir():
                raise ScanError(f"{dirname} must be a real directory, not a symbolic link")
            candidates.update(_walk_markdown(subdir))

    files = sorted(candidates, key=lambda path: path.relative_to(root).as_posix().lower())
    if len(files) > MAX_SKILL_FILES:
        raise ScanError(
            f"generated skill has {len(files):,} Markdown files; maximum is "
            f"{MAX_SKILL_FILES:,}"
        )
    return files


def _read_skill_files(skill_dir: Path, files: Iterable[Path]) -> Iterable[tuple[str, str]]:
    total_bytes = 0
    for path in files:
        if path.is_symlink():
            raise ScanError("generated skill contains a symbolic-link Markdown file")
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            raise ScanError(
                f"{_terminal_safe(path.name)} is {size:,} bytes; maximum scanned file size is "
                f"{MAX_FILE_BYTES:,} bytes"
            )
        total_bytes += size
        if total_bytes > MAX_TOTAL_BYTES:
            raise ScanError(
                f"generated skill Markdown exceeds the {MAX_TOTAL_BYTES:,}-byte scan limit"
            )
        relative = path.relative_to(skill_dir).as_posix()
        try:
            yield relative, path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ScanError(f"{_terminal_safe(relative)} is not valid UTF-8") from exc
        except OSError as exc:
            raise ScanError(f"could not read {_terminal_safe(relative)}") from exc


def _scan_text(relative_path: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()
    frontmatter_lines = _frontmatter_line_numbers(lines)

    for line_number, line in enumerate(lines, start=1):
        invisible = sorted({ord(char) for char in line if _is_invisible(ord(char))})
        if invisible:
            codepoints = ", ".join(f"U+{value:04X}" for value in invisible)
            findings.append(
                Finding(
                    relative_path,
                    line_number,
                    "unicode.invisible",
                    f"contains invisible Unicode code point(s): {codepoints}",
                )
            )

        for rule_id, pattern, message in _CONTENT_RULES:
            if pattern.search(line):
                findings.append(Finding(relative_path, line_number, rule_id, message))

        if _EXFILTRATION_TERM.search(line) or (
            _OUTBOUND_TERM.search(line) and _SENSITIVE_TERM.search(line)
        ):
            findings.append(
                Finding(
                    relative_path,
                    line_number,
                    "tool.exfiltration_shape",
                    "contains exfiltration-shaped tool or sensitive-data language",
                )
            )

        if line_number in frontmatter_lines:
            if re.match(r"^\s*allowed-tools\s*:", line, re.IGNORECASE):
                findings.append(
                    Finding(
                        relative_path,
                        line_number,
                        "frontmatter.allowed_tools",
                        "generated frontmatter declares or widens tool authority",
                    )
                )
            if re.match(
                r"^\s*disable-model-invocation\s*:\s*"
                r"[\"']?(?:false|no|0)[\"']?\s*(?:#.*)?$",
                line,
                re.IGNORECASE,
            ):
                findings.append(
                    Finding(
                        relative_path,
                        line_number,
                        "frontmatter.model_invocation_enabled",
                        "generated frontmatter explicitly enables model invocation",
                    )
                )

    return findings


def scan_generated_skill(path: Path) -> list[Finding]:
    requested = path.expanduser()
    skill_dir = requested.parent if requested.name.lower() == "skill.md" else requested
    files = _collect_skill_files(requested)
    root = skill_dir.resolve(strict=True)
    findings: list[Finding] = []
    for relative_path, text in _read_skill_files(root, files):
        findings.extend(_scan_text(relative_path, text))
    return sorted(findings, key=lambda item: (item.path.lower(), item.line, item.rule_id))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Generated skill directory or its SKILL.md")
    args = parser.parse_args(argv)

    try:
        findings = scan_generated_skill(Path(args.path))
        skipped = unscanned_markdown(Path(args.path))
    except ScanError as exc:
        print(f"ERROR generated-skill scan incomplete: {exc}", file=sys.stderr)
        return 2

    if skipped:
        # 仅作提示，且刻意不作为 Finding：受限的扫描范围是有意设计，
        # 因此这些文件不得改变退出码。但必须让用户知道，
        # 下方的"passed"一行并不覆盖这些文件。
        print(
            f"Note: {len(skipped)} Markdown file(s) in the skill directory are "
            "outside the generated-skill scope and were NOT scanned:"
        )
        for relative in skipped:
            print(f"  SKIP {_terminal_safe(relative)}")
        print(
            "  Scope is SKILL.md, glossary/patterns/cheatsheet, and chapters/. "
            "Move generated content there to have it scanned."
        )

    if findings:
        print(f"Generated-skill scan found {len(findings)} advisory finding(s):")
        for finding in findings:
            print(
                f"  WARN {_terminal_safe(finding.path)}:{finding.line} "
                f"[{finding.rule_id}] {finding.message}"
            )
        print("Review the generated files before loading, installing, or publishing them.")
        print(
            "Rules are intentionally broad and may match legitimate AI/LLM or "
            "systems-topic text; review each finding in context."
        )
        print("No files were modified by this scan.")
        return 1

    scope = " in the scanned scope" if skipped else ""
    print(
        f"Generated-skill scan passed: no known injection or authority patterns "
        f"found{scope}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
