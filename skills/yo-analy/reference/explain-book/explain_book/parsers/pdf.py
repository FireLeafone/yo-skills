from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from collections import Counter

# 单独成行、独占一行的页码：阿拉伯数字，或前言部分用来编页码的罗马数字。
#
# 罗马数字分支刻画的是规范数字的"形状"，而不是罗列它可能包含的字母。
# `[ivxlcdm]{1,7}` 会匹配任何由这些字母组成的短词，因此 "MIX"、"CIVIL"、
# "DIM"、"MILD"、"VIVID" 一旦落在页面首行或末行的非空行上，就会被悄悄删掉
# —— 而单字成行恰恰是分部标题或展示性标题的典型模样。误删真实文本比留下
# 一个游离数字更糟糕，所以模式现在是精确匹配的。
#
# 范围取 1-99，前言页码实际就用这个范围；因此 "c"/"d"/"m" 不再单独匹配，
# 孤立的 "C" 或 "M" 行现在会作为文本保留。`(?=[ivxl])` 是非空守卫：两个
# 分组各自都可省略，没有它该模式会匹配空行。
_ROMAN_1_99 = r"(?=[ivxl])(?:xc|xl|l?x{0,3})(?:ix|iv|v?i{0,3})"
_PDF_PAGE_NUM = re.compile(rf"^\s*(?:\d{{1,4}}|{_ROMAN_1_99})\s*$", re.IGNORECASE)
_PDF_HYPHEN_WRAP = re.compile(r"(\w)-\n(\w)")


def clean_pdftotext(text: str) -> str:
    """清理 pdftotext '-layout' 的输出（页面以换页符分隔）：删除重复出现的
    页眉/页脚与页面边缘的页码，并把被连字符拆到两行的单词重新拼接起来。"""
    pages = text.split("\f")
    if len(pages) >= 3:
        # 在超过半数页面的首/尾重复出现的行视为样板内容。
        edge = Counter()
        for p in pages:
            nb = [ln.strip() for ln in p.splitlines() if ln.strip()]
            if nb:
                edge[nb[0]] += 1
                # 在只有一行的页面上，首行和末行是同一行。若把它计两次，等于
                # 让一页向下面的"超过半数页面"阈值投了两票 —— 那么一个在 4 页
                # 里出现 2 次的分部隔页就会攒到 4 票而非 2 票，被当成样板删掉。
                if len(nb) > 1:
                    edge[nb[-1]] += 1
        boiler = {ln for ln, c in edge.items() if c > len(pages) / 2}
        kept = []
        for p in pages:
            lines = p.splitlines()
            nb_idx = [i for i, ln in enumerate(lines) if ln.strip()]
            first = nb_idx[0] if nb_idx else None
            last = nb_idx[-1] if nb_idx else None
            for i, ln in enumerate(lines):
                # 页眉/页脚和页码只出现在页面边缘 —— 那也是收集 `boiler` 的
                # 唯一位置。如果对每一行都删样板字符串，那么当页眉重复章节
                # 标题时（常见排版），页面中部真正的标题也会连同页眉一起被
                # 删掉。
                if i in (first, last):
                    s = ln.strip()
                    if s in boiler or _PDF_PAGE_NUM.match(s):
                        continue
                kept.append(ln)
        text = "\n".join(kept)
    else:
        text = text.replace("\f", "\n")
    # 已知瑕疵（ponytail）：朴素的去连字符处理；可能把本来带连字符的换行
    # 复合词粘在一起（"well-\nknown" -> "wellknown"）。真出问题了再做词典
    # 感知的切分。
    return _PDF_HYPHEN_WRAP.sub(r"\1\2", text)


def extract_with_pdftotext(pdf_path: str) -> str | None:
    if not shutil.which("pdftotext"):
        return None
    try:
        pdf_path = os.path.abspath(pdf_path)
        result = subprocess.run(
            ["pdftotext", "-layout", pdf_path, "-"],
            capture_output=True, text=True, timeout=120,
            encoding="utf-8", errors="replace",
        )
        if result.returncode == 0 and result.stdout.strip():
            return clean_pdftotext(result.stdout)
    except Exception as e:
        print(f"  [warn] extract_with_pdftotext failed: {type(e).__name__}: {e}", file=sys.stderr)
    return None


def looks_image_only(pdf_path: str, pages: int = 5) -> bool:
    """前 `pages` 页提取不出任何文本时返回 True —— 这是扫描版/纯图片 PDF
    的特征。廉价的预检：让扫描件在一秒内失败，而不是等整条提取链跑完才
    发现。尽力而为：没有 pdftotext 时返回 False，正常流程（以及最后的
    空文本守卫）仍然生效。"""
    if not shutil.which("pdftotext"):
        return False
    try:
        result = subprocess.run(
            ["pdftotext", "-f", "1", "-l", str(pages), os.path.abspath(pdf_path), "-"],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
        return result.returncode == 0 and not result.stdout.strip()
    except Exception:
        return False


def extract_with_pypdf(pdf_path: str) -> str | None:
    try:
        import pypdf
        text_parts = []
        with open(pdf_path, "rb") as f:
            reader = pypdf.PdfReader(f)
            for page in reader.pages:
                try:
                    text_parts.append(page.extract_text() or "")
                except Exception:
                    text_parts.append("")
        # 用换页符连接各页，好让 clean_pdftotext 不只能去连字符，还能剥离
        # 每页重复的页眉/页脚。
        return clean_pdftotext("\f".join(text_parts))
    except ImportError:
        return None
    except Exception as e:
        print(f"  [warn] extract_with_pypdf failed: {type(e).__name__}: {e}", file=sys.stderr)
        return None


def extract_with_pdfminer(pdf_path: str) -> str | None:
    try:
        from pdfminer.high_level import extract_text
        text = extract_text(pdf_path)  # 已按页以换页符分隔
        return clean_pdftotext(text) if text else text
    except ImportError:
        return None
    except Exception as e:
        print(f"  [warn] extract_with_pdfminer failed: {type(e).__name__}: {e}", file=sys.stderr)
        return None


def extract_with_docling(pdf_path: str) -> str | None:
    """使用 Docling 进行版面感知提取。最适合含表格和代码的技术类书籍。"""
    try:
        from docling.document_converter import DocumentConverter
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.datamodel.base_models import InputFormat
        from docling.document_converter import PdfFormatOption

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False
        pipeline_options.do_table_structure = True

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        result = converter.convert(pdf_path)
        return result.document.export_to_markdown()
    except ImportError:
        return None
    except Exception as e:
        print(f"  [warn] extract_with_docling failed: {type(e).__name__}: {e}", file=sys.stderr)
        return None


def count_pages(pdf_path: str) -> int:
    # 优先尝试 pdfinfo
    if shutil.which("pdfinfo"):
        try:
            pdf_path = os.path.abspath(pdf_path)
            result = subprocess.run(
                ["pdfinfo", pdf_path], capture_output=True, text=True, timeout=15
            )
            for line in result.stdout.splitlines():
                if line.startswith("Pages:"):
                    return int(line.split(":")[1].strip())
        except Exception:
            pass
    # 回退：用 pypdf 统计页数
    try:
        import pypdf
        with open(pdf_path, "rb") as f:
            return len(pypdf.PdfReader(f).pages)
    except Exception:
        return 0
