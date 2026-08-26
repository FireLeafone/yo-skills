from __future__ import annotations

import html
import html.parser
from explain_book.parsers.text import read_text_file


class _HTMLTextExtractor(html.parser.HTMLParser):
    """仅使用标准库的最简 HTML → 纯文本转换器。"""

    SKIP_TAGS = {"script", "style", "head"}

    # 块级元素。它们在开始标签和结束标签处都会发出一个边界 —— 结束标签处
    # 的边界很关键：没有它，相邻两个块的文字会粘连（"<h2>第一章</h2>引子"
    # 变成 "第一章引子"），从而破坏章节识别 —— 中文章节标题匹配要求标题
    # 独占一行，粘连后的行不再匹配。
    BLOCK_TAGS = frozenset({
        "address", "article", "aside", "blockquote", "br", "dd", "details",
        "div", "dl", "dt", "fieldset", "figcaption", "figure", "footer",
        "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hgroup", "hr",
        "li", "main", "nav", "ol", "p", "pre", "section", "table", "tbody",
        "tfoot", "thead", "tr", "ul",
    })
    # 表格单元格用制表符而非换行分隔，使一行保持在同一行上 —— 这与标准库
    # DOCX 回退解析器对制表符连接的表格行采用的约定一致，也能让表格形式的
    # 目录（"第一章 | 引论 | 1"）仍可作为单独一行标题被解析出来。
    CELL_TAGS = frozenset({"td", "th"})

    def __init__(self):
        super().__init__()
        self._parts: list[str] = []
        self._skip_depth = 0
        # 等待下一个非空文本段的最强边界。推迟写入（而不是立即追加）意味着
        # "<div><p>x" 这类嵌套块会合成为一个分隔符，而不是一串空行。
        self._pending = ""

    def _mark(self, separator: str) -> None:
        # "\n" 优先于 "\t"：行/块边界不能被紧跟在 <tr> 之后打开的 <td>
        # 降级为单元格边界。
        if separator == "\n" or not self._pending:
            self._pending = separator

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
        if tag in self.BLOCK_TAGS:
            self._mark("\n")
        elif tag in self.CELL_TAGS:
            self._mark("\t")

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            if self._skip_depth:
                self._skip_depth -= 1
            return
        if tag in self.BLOCK_TAGS:
            self._mark("\n")
        elif tag in self.CELL_TAGS:
            self._mark("\t")

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._pending:
            if not data.strip():
                # 标签之间的纯空白文本只是排版缩进。它不能满足待处理的边界，
                # 而在边界之前输出它只会增加行尾空格 —— 丢弃它，继续等待真正
                # 的内容。
                return
            # 抑制开头的分隔符，避免输出以空行开始。
            if self._parts:
                self._parts.append(self._pending)
            self._pending = ""
        self._parts.append(data)

    def get_text(self) -> str:
        # HTMLParser(convert_charrefs=True) 已经在 handle_data 中解码过实体；
        # 不要再次 unescape，否则二次编码的实体（如 "&amp;amp;"）会被错误地
        # 还原。
        return "".join(self._parts)


def extract_html_content(raw_html: str) -> str:
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(raw_html, "html.parser")
        for element in soup(["script", "style", "head"]):
            element.decompose()
        return soup.get_text(separator="\n")
    except ImportError:
        parser = _HTMLTextExtractor()
        parser.feed(raw_html)
        return parser.get_text()


def extract_html_file(path: str) -> str | None:
    raw = read_text_file(path)
    if raw is None:
        return None
    return extract_html_content(raw)
