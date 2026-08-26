from __future__ import annotations

import glob
import json
import os
import re
import statistics
import sys
import shutil
import zipfile
from pathlib import Path

from explain_book.exceptions import ExtractionError

from explain_book.config import (
    OUTPUT_DIR,
    OUTPUT_TEXT,
    OUTPUT_META,
    WORDS_PER_TOKEN,
    CJK_CHARS_PER_TOKEN,
    SUPPORTED_EXTENSIONS,
    TEXT_EXTENSIONS,
    HTML_EXTENSIONS,
    supported_formats_message,
)
from explain_book.dependencies import (
    normalize_install_mode,
    prepare_dependencies,
    run_dependency_check,
)
from explain_book.parsers.text import read_text_file
from explain_book.parsers.html import extract_html_file
from explain_book.parsers.docx import extract_docx
from explain_book.parsers.rtf import extract_rtf
from explain_book.parsers.pdf import (
    extract_with_docling,
    extract_with_pdftotext,
    extract_with_pypdf,
    extract_with_pdfminer,
    looks_image_only,
    count_pages,
)
from explain_book.sanitize import sanitize_extracted_text


# CJK 码位：表意文字及其扩展、假名、谚文、CJK 标点和全角形式。
# 这些文字不以空白分隔，所以对一本中文书按"单词"计数会把整本书压缩成
# 寥寥几个 token；必须直接按字符计数。
#
# 最后一段范围是第 2、3 平面（U+20000-U+3FFFF），即表意文字补充平面，
# 整体端到端取用而不是逐块枚举，这样将来出现新扩展时不会像扩展 H
# （U+31350-U+323AF）曾经那样静默漏掉。这个范围里没有任何非表意文字：
# emoji、数学字母数字符号和区域指示符都在第 1 平面，本范围不触及。
# 文言文、粤语、港台地名/人名用字都取自该平面。缺了它，这些字符会掉进
# 按空白分词的分支：一段无空格的连续字符只算一个"词"——这正是 #103
# 在基本多文种平面（BMP）上修掉的约 1000 倍少计问题，只是位置高了一个
# 平面。
_CJK_RE = re.compile(
    r"[　-〿぀-ヿ㐀-䶿一-鿿"
    r"가-힣豈-﫿＀-￯"
    r"\U00020000-\U0003FFFF]"
)


def estimate_tokens(text: str) -> int:
    """用确定性的启发式方法估算 ``text`` 的 token 数量。

    拉丁字母/以空白分隔的文本按词计数（``词数 / WORDS_PER_TOKEN`` ——
    项目长期沿用的比例），CJK 字符直接按 ``CJK_CHARS_PER_TOKEN`` 计数，
    因为这类文字之间几乎没有空白；不做此区分的话，一本无空格的中文书
    只会估算出几个 token，成本预检会少报约 1000 倍。中文书里也常夹杂
    英文单词，因此始终使用两者相加的混合公式，对纯中文、混排、纯英文
    文本都能得到正确结果。刻意不引入任何依赖，保证同一本书每次算出
    相同的数字。
    """
    if not text:
        return 0
    cjk = len(_CJK_RE.findall(text))
    latin_words = len(_CJK_RE.sub(" ", text).split())
    return int(latin_words / WORDS_PER_TOKEN + cjk / CJK_CHARS_PER_TOKEN)


# 可选的 Markdown / AsciiDoc 标题前缀（"## 第一章"、"== 某节"）。
# 在 _chapter_number() 中作为第二遍匹配时剥离重试，中文匹配器本身已能
# 容忍行内的该前缀，无需改动。(Issue #91)
_MD_HEADING_PREFIX = re.compile(r"^(#{1,6}|={1,6})\s+")

# 中文章节标题。两种常见形式：
#   1. 显式的 "第N章" / "第 3 回" / "第十二节" / "第一讲" —— 第 + 数词 +
#      章节量词（章回卷节篇讲）；
#   2. 以中文序数加分隔符开头的 Markdown 标题，如 "## 一 · 缘起" 或
#      "## 第一讲" —— 在中文电子书和讲义中很常见。
# 只匹配中文数词，所以 "## 5 Setup" 这类纯阿拉伯数字标题不会在这里被
# 误判为章节。detect_structure() 按章节号去重，所以 "##" 标题和重复的
# "###" 子序号会合并为同一章。
_CN_NUM_VALUES = {
    "〇": 0, "零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9,
}
_CN_NUM_UNITS = {"十": 10, "百": 100, "千": 1000}
_CN_NUM_CLASS = "〇零一二两三四五六七八九十百千"
# 全角阿拉伯数字（U+FF10–U+FF19）在中文电子书排版中也常见，如 "第１章"。
# int() 本身就能解析它们（str.isdigit() 为 True），所以只需让正则的
# 字符类接受它们。
_FW_DIGITS = "０-９"
_CN_CHAPTER = re.compile(rf"^\s*第\s*([0-9{_FW_DIGITS}{_CN_NUM_CLASS}]+)\s*[章回卷节篇讲]")
_MD_CN_HEADING = re.compile(rf"^#{{1,6}}\s+第?\s*([{_FW_DIGITS}{_CN_NUM_CLASS}]+)\s*[·、.:：章回卷节篇讲]")

# 目录标题行（仅中文）："目录"、"目  录"、"目錄"、"目次"。
# 锚定整行（^\s*X\s*$），正文里行内出现的"目录"二字不会命中。
_TOC_CJK_PATTERN = r"目[ \t\u3000]*(?:录|錄|次)"
_TOC_PATTERN = re.compile(rf"^\s*{_TOC_CJK_PATTERN}\s*$", re.MULTILINE)

# ATX 风格标题："# 标题"、"## 小节"，以及 AsciiDoc 的 "= 标题"、"== 小节"。
# 标记后必须跟一个空格，借此把 AsciiDoc 的 "== X" 和 reStructuredText 的
# 下划线 "====="（无空格）区分开 —— 后者被有意忽略（RST 下划线标题不在
# 支持范围内）。
_ATX_HEADING = re.compile(r"^(#{1,6}|={1,6})\s+(.+?)\s*#*$")
# Setext/RST 下划线：一整行 "="（一级）或 "-"（二级），长度 >= 2。
# 把它正上方的一行标记为标题。
_SETEXT_UNDERLINE = re.compile(r"^(={2,}|-{2,})$")


# 围栏代码块的起始/结束行：三个及以上反引号或波浪号。
# 捕获到的标记用于把结束围栏与它的开始围栏配对。
_CODE_FENCE = re.compile(r"^(`{3,}|~{3,})")


def _closed_fence_line_numbers(lines: list[str]) -> set[int]:
    """返回处于"确实闭合"的围栏代码块内部的行号集合。

    从未闭合的围栏按普通文本处理，而不是吞掉它之后的所有内容。文本提取
    经常会弄丢结束围栏，一本讲 Markdown 的书也可能直接散落着一个孤立的
    围栏 —— 旧的"遇围栏即翻转状态"的扫描方式会把从那一点到文档末尾的
    所有标题全部丢掉。把几行代码误当正文，代价远小于丢掉一本书的大半
    结构。

    按 CommonMark 规范，结束围栏必须使用与开始围栏相同的字符，所以
    "```" 开始的代码块不再会被一个不相干的 "~~~" 行终止。
    """
    inside: set[int] = set()
    opener: tuple[str, int] | None = None
    for index, line in enumerate(lines):
        match = _CODE_FENCE.match(line.strip())
        if not match:
            continue
        marker = match.group(1)
        if opener is None:
            opener = (marker[0], index)
        elif marker[0] == opener[0]:
            # 两条围栏标记行本身也计入内部。
            inside.update(range(opener[1], index + 1))
            opener = None
    return inside


# 数字开头的标题在"编号成体系"且"各节携带一章应有的文本量"时才算章节。
# 两个条件缺一不可，因为单靠任何一个都分不开两种形态：三步教程同样成
# 体系、同样从 1 递增；而单个长小节并不构成编号体系。
# 实测的每节正文中位数：教程步骤约 20 字符，文档小节约 500，论文章节
# 约 2,000，真正的书籍章节约 5,000。下限取在见过的最小真实章节之下
# 一个数量级、最大教程步骤之上一个数量级的位置。
_MIN_NUMBERED_TITLES = 3
_MIN_NUMBERED_BODY_CHARS = 200


def _numbered_titles_are_structural(
    entries: list[tuple[str, int]], heading_lines: list[int], lines: list[str]
) -> bool:
    """判断同一层级的数字开头标题是章节还是列表项。

    刻意不依据数字本身判断。从 1 开始的递增序列既能准确描述
    "Step 1 / Step 2 / Step 3"，也能准确描述论文的章节；如果要求序列
    必须连续不断，那么当提取过程丢掉一个标题、章节列表从 0 开始、或
    多来源语料里编号重新开始时，整本书都会被误判丢弃。
    """
    if len(entries) < _MIN_NUMBERED_TITLES:
        return False
    ordered = sorted(heading_lines)
    bodies = []
    for _, index in entries:
        after = [ln for ln in ordered if ln > index]
        end = after[0] if after else len(lines)
        bodies.append(sum(len(ln) for ln in lines[index + 1:end]))
    return statistics.median(bodies) >= _MIN_NUMBERED_BODY_CHARS


def _structural_chapter_count(text: str) -> int:
    """统计 Markdown/AsciiDoc/RST 文本中像章节的结构性标题数量。

    识别 ATX 标题（"# 标题"、"== 小节"）和 setext/RST 下划线标题
    （标题行正下方紧挨一行 "=" 或 "-"）。将（大小写归一化后的）不重复
    标题按层级分组，返回具有 >= 2 个不重复标题的最浅层级的标题数 ——
    在常见的 "# 书名 / ## 章节" 版式中，最浅层只出现一次，这样能选中
    真正的章节层级。

    防误报措施：跳过围栏代码块里的标题；拒绝以裸数字开头的 ATX 标题
    （"## 5 Setup"）和纯标点组成的标题（"=====" 表格边框）；setext
    下划线只有在正上方紧贴一个非空、且不短于该下划线的标题行时才算数
    （这样分隔线、表格边框和卷首的 "---" 都不会命中）。
    """
    lines = text.splitlines()
    levels: dict[int, set[str]] = {}
    # 数字开头的标题先暂扣，最后按层级统一裁决（见
    # _numbered_titles_are_structural）："## 1. 引言" 和 "## 5 Setup"
    # 字符串形态相同，单凭一行无法区分。
    numbered: dict[int, list[tuple[str, int]]] = {}
    heading_lines: list[int] = []
    fenced = _closed_fence_line_numbers(lines)
    prev = ""  # 上一条非围栏行（已去空白）；setext 标题的候选行
    for index, line in enumerate(lines):
        if index in fenced:
            prev = ""
            continue
        s = line.strip()
        # Setext/RST 下划线："="（一级）或 "-"（二级），直接位于一个
        # 不短于该下划线的标题行之下。
        if (
            _SETEXT_UNDERLINE.match(s)
            and prev
            and not _SETEXT_UNDERLINE.match(prev)
            and len(s) >= len(prev)
        ):
            depth = 1 if s[0] == "=" else 2
            levels.setdefault(depth, set()).add(prev.lower())
            heading_lines.append(index)
            prev = ""
            continue
        # ATX 标题（"# 标题"、"== 小节"）。
        m = _ATX_HEADING.match(s)
        if m:
            title = m.group(2).strip().lower()
            depth = len(m.group(1))
            # 拒绝空标题和纯标点标题（"=====" 表格边框）。
            if title and re.search(r"\w", title):
                heading_lines.append(index)
                if title[0].isdigit():
                    numbered.setdefault(depth, []).append((title, index))
                else:
                    levels.setdefault(depth, set()).add(title)
            # ATX 标题行不能充当下一行的 setext 标题。
            prev = ""
            continue
        prev = s
    for depth, entries in numbered.items():
        if _numbered_titles_are_structural(entries, heading_lines, lines):
            levels.setdefault(depth, set()).update(title for title, _ in entries)
    if not levels:
        return 0
    for depth in sorted(levels):
        if len(levels[depth]) >= 2:
            return len(levels[depth])
    # 没有任何层级拥有 >= 2 个不重复标题：说明是薄文档（比如每层只有
    # 一个标题）。全部计入 —— 这条路径只在数字章节检测已经一无所获时
    # 作为兜底运行，不会夸大真实书籍的章节数。
    return sum(len(titles) for titles in levels.values())


def _cn_numeral_to_int(s: str) -> int | None:
    """把中文（或 ASCII 数字）章节数词解析为 int（1..999）。"""
    if s.isdigit():
        n = int(s)
        return n if 1 <= n <= 999 else None
    section = current = 0
    for ch in s:
        if ch in _CN_NUM_VALUES:
            current = _CN_NUM_VALUES[ch]
        elif ch in _CN_NUM_UNITS:
            section += (current or 1) * _CN_NUM_UNITS[ch]
            current = 0
        else:
            return None
    total = section + current
    return total if 1 <= total <= 999 else None


def _match_chapter_number(line: str) -> int | None:
    """若该行是真正的中文章节标题则返回章节号。

    调用方需先剥离 Markdown/AsciiDoc 标题前缀。
    """
    s = line.strip()
    if len(s) > 80:
        return None
    cm = _CN_CHAPTER.match(s) or _MD_CN_HEADING.match(s)
    if cm:
        return _cn_numeral_to_int(cm.group(1))
    return None


def _chapter_number(line: str) -> int | None:
    """若该行是真正的中文章节标题则返回章节号。

    支持 "第三章 …"、"## 一 · 缘起"、"## 第一讲"、"第5章" 等中文标题
    样式 —— 标题前可选地带一个 Markdown/AsciiDoc 标题标记（"## 第一章"
    和 "第一章" 一样是章节标题）。
    """
    match = _match_chapter_number(line)
    if match is not None:
        return match
    # 第二遍：Markdown/AsciiDoc 标题前缀（"## 第一章"、"== 某节"）会让
    # 上面的匹配器看不到标题本体。剥离前缀后重试，使 --mode technical
    # （Docling 会把标题输出为 Markdown）能检测到与纯文本提取相同的
    # 章节。(Issue #91)
    s = line.strip()
    md = _MD_HEADING_PREFIX.match(s)
    if md:
        return _match_chapter_number(s[md.end():])
    return None


def detect_structure(text: str) -> dict:
    """检测章节数量和目录是否存在。

    扫描全文（而不仅是开头），从显式的 "第N章" 等中文章节标题中统计
    不重复的章节号，拒绝正文里的交叉引用和编号列表项。按不重复章节号
    统计意味着目录条目和它对应的正文标题不会被重复计数。
    """
    lines = text.splitlines()

    headings = []
    numbers = set()
    for line in lines:
        num = _chapter_number(line)
        if num is not None:
            numbers.add(num)
            headings.append(line.strip())
    numeric_count = len(numbers)
    # 只有在没有找到任何数字编号的 "第N章" 标题时，才回退到结构性
    # （Markdown/AsciiDoc）标题，这样有真实章节的书不受影响。
    #
    # 最终是哪条分支给出的答案会随数量一起上报。两条分支经常不一致，
    # 而错误的数量在它产出的结果里并不可见：它会变成第 3 步的拆解计划
    # 和生成的技能里的章节文件。本项目的每个解析器都会声明自己用了哪种
    # 方法（"Trying python-docx... OK"）；这个决策形态相同，却曾是唯一
    # 沉默的一个。
    if numeric_count > 0:
        chapters_detected = numeric_count
        chapters_method = "numeric"
    else:
        chapters_detected = _structural_chapter_count(text)
        chapters_method = "structural" if chapters_detected else "none"

    # 在前 ~30k 字符内寻找目录标志（见 _TOC_PATTERN）
    has_toc = bool(_TOC_PATTERN.search(text[:30000]))

    return {
        "chapters_detected": chapters_detected,
        "chapters_method": chapters_method,
        "chapter_headings_sample": headings[:10],
        "has_toc": has_toc,
    }


def parse_arguments(argv: list[str]) -> tuple[list[str], str, str]:
    """把 argv 解析为 (input_paths, extraction_mode, install_mode)。"""
    input_paths = []
    extraction_mode = "text"

    args = argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--mode":
            if i + 1 < len(args):
                extraction_mode = args[i+1].lower()
                i += 2
            else:
                i += 1
        elif arg == "--install-missing":
            if i + 1 < len(args) and not args[i+1].startswith("--"):
                i += 2
            else:
                i += 1
        elif arg == "--no-install-missing":
            i += 1
        elif arg.startswith("-"):
            print(f"WARNING: Unknown flag '{arg}' — ignoring it.", file=sys.stderr)
            i += 1
        else:
            input_paths.append(arg)
            i += 1

    install_mode = normalize_install_mode(argv)
    if extraction_mode not in ("technical", "text"):
        extraction_mode = "text"

    return input_paths, extraction_mode, install_mode


def resolve_input_files(paths: list[str]) -> list[Path]:
    """把路径（包括文件、目录和 glob 模式）解析为 Path 对象列表。

    显式给出的文件参数保持用户给出的顺序；展开得到的结果（目录、glob）
    按确定性规则排序，保证重复运行产出相同的输出。

    开头的 "~" 在这里展开，而不是依赖 shell：glob 模式必须加引号才能
    未经展开地传到这里（"~/books/*.pdf"），而加引号会同时阻止 shell
    展开波浪号。`glob.glob` 和 `Path` 都会把 "~" 当作字面目录名，不做
    这一步的话模式会静默地什么都匹配不到。
    """
    resolved = []
    for raw_path in paths:
        # 在入口处一次性规范化 "~"，让下面的 glob 分支和文件/目录分支
        # 看到的都是真实路径。
        path_str = os.path.expanduser(raw_path)
        # 检查是否含有 glob 通配符
        if any(char in path_str for char in ("*", "?", "[")):
            glob_matches = glob.glob(path_str, recursive=True)
            # glob 展开结果按确定性规则排序
            expanded = []
            for match in glob_matches:
                p = Path(match)
                if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                    expanded.append(p.resolve())
            expanded.sort(key=lambda x: str(x).lower())
            resolved.extend(expanded)
        else:
            p = Path(path_str)
            if p.is_dir():
                # 目录展开结果按确定性规则排序
                dir_files = []
                for root, _, files in os.walk(p):
                    for file in files:
                        file_path = Path(root) / file
                        if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                            dir_files.append(file_path.resolve())
                dir_files.sort(key=lambda x: str(x).lower())
                resolved.extend(dir_files)
            else:
                # 即使不存在也保留，以便错误检查能报告它
                resolved.append(p.resolve())

    # 去重并保持插入顺序（显式文件按用户给出的顺序）
    seen = set()
    unique_paths = []
    for path in resolved:
        resolved_path = path.resolve() if path.exists() else path
        if resolved_path not in seen:
            seen.add(resolved_path)
            unique_paths.append(resolved_path)

    return unique_paths


def extract_single_file(input_path: Path, extraction_mode: str, install_mode: str) -> dict:
    """从单个文件提取文本和元数据。"""
    input_str = str(input_path)

    if not input_path.exists():
        raise ExtractionError(f"File not found: {input_str}")

    ext = input_path.suffix.lower()
    document_format = ext.lstrip(".")

    # 后缀不受支持时嗅探魔数。
    #
    # 这个函数里的所有失败都必须以 ExtractionError 的形式浮出水面：
    # main() 里的批处理循环只捕获这一种异常，其他任何异常都会中止整个
    # 运行 —— 包括那些本来能正常提取的来源。无法读取或无法打开的文件
    # 是单个来源的问题，所以在这里转换异常类型。（下面的 ZipFile 分支
    # 已经对 OSError 这么做了。）
    if ext not in SUPPORTED_EXTENSIONS:
        try:
            with open(input_str, "rb") as f:
                header = f.read(8)
        except OSError as exc:
            raise ExtractionError(
                f"Could not read {input_path.name}: {exc.strerror or exc}"
            ) from exc
        if header[:4] == b"%PDF":
            ext = ".pdf"
            document_format = "pdf"
        elif header[:2] == b"PK":
            try:
                with zipfile.ZipFile(input_str) as zf:
                    names = set(zf.namelist())
                    if "word/document.xml" in names:
                        ext = ".docx"
                        document_format = "docx"
                    else:
                        raise ExtractionError(
                            f"Unsupported ZIP-based format '{input_path.name}'. Supported: {supported_formats_message()}"
                        )
            except (zipfile.BadZipFile, KeyError, OSError):
                raise ExtractionError(
                    f"Unsupported ZIP-based format '{input_path.name}'. Supported: {supported_formats_message()}"
                )
        else:
            raise ExtractionError(
                f"Unsupported format '{ext or '<none>'}'. Supported: {supported_formats_message()}"
            )

    prepare_dependencies(ext, extraction_mode, install_mode)

    text = ""
    method = ""
    pages = 0
    pages_label = "sections"

    if ext == ".pdf":
        print(f"Extracting PDF: {input_str}")
        if looks_image_only(input_str):
            raise ExtractionError(
                f"{input_path.name} looks like a scanned (image-only) PDF: its first pages "
                "contain no extractable text, only images.\n"
                "Run OCR on it first, then retry:\n"
                "  ocrmypdf input.pdf output.pdf"
            )
        if extraction_mode == "technical":
            print("Mode: technical — using Docling (layout-aware)...", end=" ", flush=True)
            text = extract_with_docling(input_str)
            if text and text.strip():
                method = "docling"
                print("OK")
            else:
                print("not available, falling back to pdftotext")
                extraction_mode = "text"

        if extraction_mode == "text" or not text:
            print("Mode: text — using pdftotext...")
            print("Trying pdftotext...", end=" ", flush=True)
            text = extract_with_pdftotext(input_str)

            if text and text.strip():
                method = "pdftotext"
                print("OK")
            else:
                print("not available")
                print("Trying pypdf...", end=" ", flush=True)
                text = extract_with_pypdf(input_str)
                if text and text.strip():
                    method = "pypdf"
                    print("OK")
                else:
                    print("not available")
                    print("Trying pdfminer.six...", end=" ", flush=True)
                    text = extract_with_pdfminer(input_str)
                    if text and text.strip():
                        method = "pdfminer"
                        print("OK")
                    else:
                        print("FAILED")
                        raise ExtractionError(
                            "Could not extract text from PDF.\n"
                            "Install one of: poppler-utils (pdftotext), pypdf, or pdfminer.six\n"
                            "  sudo apt install poppler-utils\n"
                            "  pip3 install pypdf\n"
                            "  pip3 install pdfminer.six"
                        )


        pages = count_pages(input_str)
        pages_label = "pages"
    elif ext in TEXT_EXTENSIONS:
        print(f"Extracting text document: {input_str}")
        text = read_text_file(input_str)
        if text is None or not text.strip():
            raise ExtractionError(f"Could not read text document: {input_path.name}")
        method = "plain-text"
        pages = 0
        pages_label = "sections"
    elif ext in HTML_EXTENSIONS:
        print(f"Extracting HTML: {input_str}")
        text = extract_html_file(input_str)
        if text is None or not text.strip():
            raise ExtractionError(f"Could not extract text from HTML: {input_path.name}")
        method = "html-parser"
        pages = 0
        pages_label = "sections"
    elif ext == ".docx":
        print(f"Extracting DOCX: {input_str}")
        text, method = extract_docx(input_str)
        pages = 0
        pages_label = "sections"
    elif ext == ".rtf":
        print(f"Extracting RTF: {input_str}")
        text, method = extract_rtf(input_str)
        pages = 0
        pages_label = "sections"

    text, removed_invisible = sanitize_extracted_text(text)
    if removed_invisible:
        print(
            f"  [security] removed {removed_invisible} invisible Unicode "
            f"code point(s) from {input_path.name}",
            file=sys.stderr,
        )
    if not text.strip():
        raise ExtractionError(
            f"Extracted text from {input_path.name} contained no visible content "
            "after Unicode sanitization."
        )

    tokens = estimate_tokens(text)
    structure = detect_structure(text)
    print(
        f"  chapters: {structure['chapters_detected']} "
        f"({structure['chapters_method']})"
    )
    file_size_mb = os.path.getsize(input_str) / (1024 * 1024)

    return {
        "source_file": str(input_path.resolve()),
        "filename": input_path.name,
        "format": document_format,
        "extraction_method": method,
        "file_size_mb": round(file_size_mb, 2),
        pages_label: pages,
        "pages_label": pages_label,
        "pages": pages,
        "chars": len(text),
        "words": len(text.split()),
        "estimated_tokens": tokens,
        "text": text,
        **structure,
    }


def prepare_output_dir(path: Path) -> None:
    """创建工作目录，并防范两类共享 tmp 目录风险：
    在可预测路径上预先埋好的符号链接，以及复用一个已被其他用户
    拥有的目录（两者都可能泄露或篡改提取出的文档文本，而文档
    内容可能是敏感的）。
    """
    if path.is_symlink():
        raise ExtractionError(
            f"Refusing to use {path}: it is a symbolic link, not a real "
            "directory. Remove it or set EXPLAIN_BOOK_WORKDIR to a private path."
        )
    if path.exists():
        if not path.is_dir():
            raise ExtractionError(f"Refusing to use {path}: it exists and is not a directory.")
        if hasattr(os, "getuid"):
            owner_uid = path.stat().st_uid
            if owner_uid != os.getuid():
                raise ExtractionError(
                    f"Refusing to use {path}: it is owned by a different user "
                    f"(uid {owner_uid}). Set EXPLAIN_BOOK_WORKDIR to a private directory."
                )
            os.chmod(path, 0o700)
    else:
        path.mkdir(parents=True, mode=0o700)


def print_intro() -> None:
    """每次运行开头打印的两行归属信息。

    放在这里打印而不是只写在 SKILL.md 里，这样无论 agent 以何种方式
    调用提取流程都会显示。注明提取引擎内嵌（vendor）自哪个上游项目。
    """
    sys.stderr.write(
        "explain-book · parses a book into a structured document set (Markdown)\n"
        "extraction engine vendored from book-to-skill (MIT) · "
        "github.com/virgiliojr94/book-to-skill\n\n"
    )


def print_support_note() -> None:
    """运行成功后才打印的一行结尾致谢，注明上游提取引擎的来源。

    该引擎内嵌自 book-to-skill，其作者利用个人时间维护；这一行给心怀
    感激的用户指路上游的赞助页面。提取失败时绝不打印。

    写到 stdout，和结尾报告的其余部分在一起：当运行被管道捕获时
    （agent 正是这样捕获输出的），stderr 无缓冲而 stdout 有缓冲，
    两者混用会把这行结尾语顶到输出最前面。
    """
    print(
        "\n   The extraction engine comes from book-to-skill, maintained upstream in personal time."
        "\n   If it saves you work, you can fund its upkeep: "
        "github.com/sponsors/virgiliojr94"
    )


def print_usage() -> None:
    """打印独立命令行用法。"""
    print(
        "Usage: explain-book <path-to-document-folder-or-glob>... "
        "[--mode technical|text] [--install-missing ask|yes|no]",
        file=sys.stderr,
    )
    print(
        "       explain-book --check    # report which extractors are installed",
        file=sys.stderr,
    )
    print(f"Supported formats: {supported_formats_message()}", file=sys.stderr)


def main():
    print_intro()

    if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
        print_usage()
        sys.exit(0)

    if "--check" in sys.argv[1:]:
        sys.exit(run_dependency_check())

    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    raw_input_paths, extraction_mode, install_mode = parse_arguments(sys.argv)

    if not raw_input_paths:
        print("ERROR: No input document, folder, or glob pattern specified.", file=sys.stderr)
        sys.exit(1)

    input_files = resolve_input_files(raw_input_paths)

    if not input_files:
        print(f"ERROR: No supported files found matching: {', '.join(raw_input_paths)}", file=sys.stderr)
        sys.exit(1)

    prepare_output_dir(OUTPUT_DIR)

    extracted_sources = []
    combined_texts = []
    errors = []

    for file_path in input_files:
        try:
            res = extract_single_file(file_path, extraction_mode, install_mode)
        except ExtractionError as exc:
            print(f"WARNING: Skipping {file_path.name}: {exc}", file=sys.stderr)
            errors.append((file_path, str(exc)))
            continue
        extracted_sources.append(res)

        # 用清晰的分隔边界包装文本
        separator = f"\n\n{'=' * 80}\nSOURCE: {res['filename']} (Path: {res['source_file']})\n{'=' * 80}\n\n"
        combined_texts.append(separator + res["text"])

    if not extracted_sources:
        print(f"\nERROR: All {len(errors)} source(s) failed extraction:", file=sys.stderr)
        for path, err in errors:
            print(f"  - {path.name}: {err}", file=sys.stderr)
        sys.exit(1)

    # 合并文本
    consolidated_text = "".join(combined_texts).strip()

    # 写出合并后的文本
    OUTPUT_TEXT.write_text(consolidated_text, encoding="utf-8")

    # 汇总元数据
    total_file_size_mb = sum(src["file_size_mb"] for src in extracted_sources)
    total_pages = sum(src["pages"] for src in extracted_sources)
    total_chars = len(consolidated_text)
    total_words = len(consolidated_text.split())
    total_tokens = estimate_tokens(consolidated_text)

    # 只从来源正文检测结构。full_text.txt 里生成的 SOURCE 横幅是一排
    # "="，否则它们会变成幻影 setext 标题，让检测结果依赖于来源路径的
    # 长度。
    structure_text = "\n\n".join(src["text"] for src in extracted_sources)
    consolidated_structure = detect_structure(structure_text)
    # has_toc 是按来源各自成立的属性，必须按来源逐个合并，而不能从合并
    # 后的语料上重新推导。detect_structure 只扫描前 ~30k 字符，因为目录
    # 位于一本书的卷首 —— 但在合并后的语料上，这个窗口只覆盖第一个
    # 来源，后面任何一本书里的目录都不可见，答案会仅随输入顺序翻转。
    # 每个单来源结果都已经扫描过各自的卷首，所以直接对它们取或（OR）。
    consolidated_structure["has_toc"] = any(
        src["has_toc"] for src in extracted_sources
    )

    metadata = {
        "source_file": "Consolidated from multiple sources" if len(extracted_sources) > 1 else extracted_sources[0]["source_file"],
        "filename": "multi-source" if len(extracted_sources) > 1 else extracted_sources[0]["filename"],
        "format": "mixed" if len(extracted_sources) > 1 else extracted_sources[0]["format"],
        "extraction_method": "multi-method" if len(extracted_sources) > 1 else extracted_sources[0]["extraction_method"],
        "extraction_mode": extraction_mode,
        "file_size_mb": round(total_file_size_mb, 2),
        "pages": total_pages,
        "chars": total_chars,
        "words": total_words,
        "estimated_tokens": total_tokens,
        "estimated_tokens_human": f"~{total_tokens // 1000}K",
        "output_text": str(OUTPUT_TEXT),
        "total_sources": len(extracted_sources),
        "sources": [
            {
                "source_file": src["source_file"],
                "filename": src["filename"],
                "format": src["format"],
                "extraction_method": src["extraction_method"],
                "file_size_mb": src["file_size_mb"],
                "pages": src["pages"],
                "pages_label": src["pages_label"],
                "chars": src["chars"],
                "words": src["words"],
                "estimated_tokens": src["estimated_tokens"],
                "chapters_detected": src["chapters_detected"],
                "chapters_method": src["chapters_method"],
                "has_toc": src["has_toc"]
            }
            for src in extracted_sources
        ],
        **consolidated_structure,
    }

    # encoding="utf-8" 是必需的，不是装饰：元数据用 ensure_ascii=False
    # 转储，任何非 ASCII 的章节标题、文件名或路径都会原样到达编码器。
    # 缺了它，write_text() 会退回 locale 编码，在 Windows cp1252 主机或
    # LC_ALL=C 环境下抛出 UnicodeEncodeError —— 而且是在所有来源都已
    # 提取完毕之后。
    OUTPUT_META.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    page_line = f"   Total Pages: {total_pages}"
    print("\nExtraction complete:")
    print(f"   Sources : {len(extracted_sources)} processed")
    print(f"   Size    : {total_file_size_mb:.2f} MB")
    print(page_line)
    print(f"   Words   : {total_words:,}")
    print(f"   Tokens  : ~{total_tokens // 1000}K")
    print(
        f"   Chapters: {consolidated_structure['chapters_detected']} detected overall "
        f"({consolidated_structure['chapters_method']})"
    )
    if consolidated_structure["chapters_method"] == "structural" and (
        consolidated_structure["chapters_detected"] <= 1 and total_words > 5000
    ):
        # 数字编号的 "第N章" 标题一无所获，而结构性兜底对一份相当长的
        # 文档只找回一个小节。这种组合是检测失败的可能性远大于它真是
        # 一本只有一章的书，而且这个失败在它产出的输出里并不可见。
        print(
            "   WARN    : only one section found in a document this long — chapter "
            "detection likely failed; check the headings before generating."
        )
    print(f"   ToC     : {'yes' if consolidated_structure['has_toc'] else 'not detected'}")
    if not consolidated_structure["has_toc"]:
        print(
            "   WARN    : No table of contents detected — chapter mapping in Step 3 "
            "will rely on heading scan only, which may miss or duplicate sections."
        )
    print(f"\n   Text -> {OUTPUT_TEXT}")
    print(f"   Meta -> {OUTPUT_META}")
    if errors:
        print(f"\n   WARNING: {len(errors)} source(s) skipped due to errors:")
        for path, err in errors:
            print(f"     - {path.name}: {err}")
    else:
        print_support_note()
