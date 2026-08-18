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

WORDS_PER_TOKEN = 0.75  # approximate (Latin / whitespace-delimited text)
# CJK scripts carry little or no whitespace, so word-splitting under-counts them
# by orders of magnitude. Count CJK codepoints directly against this
# chars-per-token ratio instead (see estimate_tokens in utils.py).
CJK_CHARS_PER_TOKEN = 1.5  # approximate for cl100k-style tokenizers

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
