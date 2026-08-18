import html
import re
import sys
from explain_book.parsers.text import read_text_file
from explain_book.exceptions import ExtractionError


# RTF 的 unicode 转义：\uN（有符号十进制），后跟其回退字符。解码该码点并
# 丢弃标准的单个回退字符 —— 一个 \'XX 十六进制字节或一个字面 "?"。假定
# 默认的 \uc1（一个回退字符）；\ucN 指令与多字符/成组回退不做解析（仅为
# 尽力而为的回退处理）。
_RTF_UNICODE = re.compile(r"\\u(-?\d+)[ ]?(?:\\'[0-9a-fA-F]{2}|\?)?")


def _rtf_unicode_repl(match: re.Match) -> str:
    cp = int(match.group(1)) % 0x10000      # RTF 使用有符号 16 位；负值按模回绕
    if cp == 0 or 0xD800 <= cp <= 0xDFFF:   # NUL 与孤立代理项：不应出现在文本中
        return ""
    return chr(cp)


# 这些 RTF 组装的是元数据或格式表，而非文档正文。如果只剥离其中的控制字
# （即下面清理逻辑的做法），残余内容会留下来：字体和样式的*名称*、生成器
# 字符串、以及 \info 的标题/作者，全都会混进提取出的书籍文本。
_SKIP_DESTINATIONS = frozenset({
    "fonttbl",            # {\fonttbl{\f0\fnil Calibri;}}   -> "Calibri;"
    "colortbl",           # {\colortbl;\red255...;}          -> ";;;"
    "stylesheet",         # {\stylesheet{\s0 Normal;}}       -> "Normal;"
    "info",               # {\info{\title X}{\author Y}}     -> "XY"
    "listtable", "listoverridetable", "revtbl", "rsidtbl",
    "latentstyles", "datastore", "themedata", "colorschememapping",
    "filetbl", "xmlnstbl", "pgptbl", "protusertbl", "userprops",
    "docvar",
    "pict", "objdata",    # 二进制图片 / OLE 载荷，以十六进制文本形式存在
    "bkmkstart", "bkmkend",
})

# 组的第一个控制字，允许 "\*" 可忽略目标前缀：
# "{\fonttbl"、"{\*\generator"、"{\*\bkmkstart"。
_GROUP_DESTINATION = re.compile(r"\\\*?\\?([a-zA-Z]+)")


def _strip_destination_groups(raw: str) -> str:
    """移除不含文档正文的 RTF 组。

    跟踪花括号深度，从而整组丢弃，而不只是丢弃其中的控制字。按照 RTF 规范，
    不理解某个 ``\\*`` 目标的读取器必须跳过整个组，这同时也能处理
    ``\\*\\generator`` 和任何厂商扩展，而无需逐一点名。转义形式 ``\\{`` /
    ``\\}`` / ``\\\\`` 不视为分隔符。

    一个有用的副作用：对于域，``{\\field{\\*\\fldinst HYPERLINK ...}
    {\\fldrslt 可见文本}}`` 会保留结果而丢弃指令部分。
    """
    out: list[str] = []
    index = 0
    depth = 0
    skip_at_depth = 0  # 处于被跳过的组内时非零
    length = len(raw)

    while index < length:
        char = raw[index]

        # 转义字面量："\{"、"\}"、"\\" 是文本，永远不是组分隔符。
        if char == "\\" and index + 1 < length and raw[index + 1] in "{}\\":
            if not skip_at_depth:
                out.append(raw[index:index + 2])
            index += 2
            continue

        if char == "{":
            depth += 1
            if not skip_at_depth:
                match = _GROUP_DESTINATION.match(raw, index + 1)
                ignorable = raw.startswith("{\\*", index)
                if ignorable or (match and match.group(1) in _SKIP_DESTINATIONS):
                    skip_at_depth = depth
                else:
                    out.append(char)
            index += 1
            continue

        if char == "}":
            if skip_at_depth and depth == skip_at_depth:
                skip_at_depth = 0
            elif not skip_at_depth:
                out.append(char)
            depth -= 1
            index += 1
            continue

        if not skip_at_depth:
            out.append(char)
        index += 1

    if skip_at_depth:
        # 未闭合的目标组：文件是畸形的，未闭合花括号之后的所有内容刚刚都被
        # 丢弃了，而那可能是整本书。相比之下泄漏一些元数据残余是更轻的危害，
        # 因此回退为返回未扫描的原文，而不是返回被截断的文档。
        return raw

    return "".join(out)


def strip_rtf_fallback(raw: str) -> str:
    # 先整组丢弃元数据/表格组，使其内容永远到不了后面的控制字清理 —— 否则
    # 那一步只会剥掉标记，把名称当作正文留下来。
    raw = _strip_destination_groups(raw)
    raw = _RTF_UNICODE.sub(_rtf_unicode_repl, raw)   # 先解码 \uN 转义
    raw = re.sub(r"\\'[0-9a-fA-F]{2}", " ", raw)
    raw = re.sub(r"\\par[d]?", "\n", raw)
    raw = re.sub(r"\\tab", "\t", raw)
    # 先把三个转义字面量（"\\"、"\{"、"\}"）寄存在占位符上，再做下面的
    # 清扫；否则清扫会把反斜杠当作控制符号剥掉，再把花括号连同真正的组
    # 分隔符一起删掉 —— 书里写的 "{a, b}" 就会留下一个孤零零的 "\"。
    # 最长转义优先。
    raw = (
        raw.replace("\\\\", "\x01")
        .replace("\\{", "\x02")
        .replace("\\}", "\x03")
    )
    raw = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", raw)
    raw = raw.replace("{", "").replace("}", "")
    raw = raw.replace("\x01", "\\").replace("\x02", "{").replace("\x03", "}")
    return html.unescape(raw)


def extract_rtf(rtf_path: str) -> tuple[str, str]:
    raw = read_text_file(rtf_path)
    if raw is None:
        raise ExtractionError(f"Could not read RTF file: {rtf_path}")

    try:
        from striprtf.striprtf import rtf_to_text
        text = rtf_to_text(raw)
        if text.strip():
            return text, "striprtf"
    except ImportError:
        pass
    except Exception as e:
        print(f"  [warn] extract_rtf/striprtf failed: {type(e).__name__}: {e}", file=sys.stderr)

    return strip_rtf_fallback(raw), "rtf-regex"
