import os
import tempfile
from pathlib import Path

OUTPUT_DIR = Path(
    os.environ.get(
        "EXPLAIN_BOOK_WORKDIR",
        str(Path(tempfile.gettempdir()) / "explain_book_work"),
    )
)
OUTPUT_TEXT = OUTPUT_DIR / "full_text.txt"
OUTPUT_META = OUTPUT_DIR / "metadata.json"

WORDS_PER_TOKEN = 0.75  # 近似值（适用于以空白分词的拉丁文文本）
# 中日韩文字基本不含空白符，按词切分会把它们低估几个数量级。
# 因此改为按此"每 token 字符数"比例直接统计 CJK 码点
# （见 utils.py 中的 estimate_tokens）。
CJK_CHARS_PER_TOKEN = 1.5  # 近似值，适用于 cl100k 风格的 tokenizer

TEXT_EXTENSIONS = {".txt", ".text", ".md", ".markdown", ".rst", ".adoc", ".asciidoc"}
HTML_EXTENSIONS = {".html", ".htm", ".xhtml"}
SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".rtf",
    *TEXT_EXTENSIONS,
    *HTML_EXTENSIONS,
}

PYTHON_DEPENDENCIES = {
    "docling": "docling",
    "pypdf": "pypdf",
    "pdfminer": "pdfminer.six",
    "bs4": "beautifulsoup4",
    "docx": "python-docx",
    "striprtf": "striprtf",
}


def supported_formats_message() -> str:
    return ", ".join(sorted(SUPPORTED_EXTENSIONS))
