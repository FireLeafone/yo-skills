from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

from explain_book.config import PYTHON_DEPENDENCIES, HTML_EXTENSIONS


# --check 预检报告使用的有序分组。每一项描述一种格式及其所需的东西。
# `modules` 是可选的 Python 包（除非另有说明，任意一个即可）；`system` 是
# 通过 PATH 解析的外部命令。
DEPENDENCY_GROUPS = [
    {
        "label": "PDF (text-heavy)",
        "modules": ["pypdf", "pdfminer"],
        "any_of_modules": True,
        "any_tool_suffices": True,
        "system": [("pdftotext", "poppler-utils", "sudo apt install poppler-utils")],
        "note": "any one of pdftotext / pypdf / pdfminer is enough",
    },
    {
        "label": "PDF (technical: tables, code, formulas)",
        "modules": ["docling"],
        "any_of_modules": True,
        "system": [],
        "note": "needed only for --mode technical; otherwise falls back to the text chain",
    },
    {
        "label": "DOCX",
        "modules": ["docx"],
        "any_of_modules": True,
        "system": [],
        "note": "falls back to a stdlib ZIP/XML parser if missing",
    },
    {
        "label": "HTML",
        "modules": ["bs4"],
        "any_of_modules": True,
        "system": [],
        "note": "falls back to the stdlib html.parser if missing",
    },
    {
        "label": "RTF",
        "modules": ["striprtf"],
        "any_of_modules": True,
        "system": [],
        "note": "falls back to a basic regex cleanup if missing",
    },
]


def python_module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def isolated_install_hint(module_name: str) -> str | None:
    """解释某个"已作为工具安装、但当前解释器无法导入"的模块。

    pipx —— Docling 官方文档建议的安装方式 —— 会把包放进它自己的
    virtualenv，PATH 上只暴露可执行文件。此时该模块在当前解释器里确实
    无法导入，所以 "✗ python: docling" 是对的却毫无用处：用户明明装了，
    我们却说它缺失。

    返回一行文字，指出可执行文件的位置以及能导入该模块的解释器；若没有
    这样的可执行文件则返回 None。绝不声称模块可用 —— 解析器靠的是
    import，PATH 上的二进制并不能让 import 成功；它只是告诉我们可用的
    环境在哪里。
    """
    executable = shutil.which(module_name)
    if not executable:
        return None
    # pipx 布局：<venv>/bin/<tool> —— 其同级的 `python` 可以导入该模块。
    venv_python = Path(executable).resolve().parent / "python"
    where = f"\n        {venv_python} scripts/extract.py …" if venv_python.exists() else ""
    return (
        f"a `{module_name}` command exists at {executable}, so it is installed in an "
        f"isolated environment (pipx?).\n        Run the extractor with that "
        f"environment's Python, or install it into this one:{where}"
    )


def missing_python_packages(module_names: list[str]) -> list[str]:
    missing = []
    for module_name in module_names:
        if not python_module_available(module_name):
            missing.append(PYTHON_DEPENDENCIES[module_name])
    return missing


def install_python_packages(packages: list[str]) -> bool:
    if not packages:
        return True

    print(f"Installing missing Python package(s): {', '.join(packages)}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", *packages],
            text=True,
            timeout=600,
        )
    except Exception as exc:
        print(f"Package installation failed: {exc}", file=sys.stderr)
        return False

    importlib.invalidate_caches()
    return result.returncode == 0


def normalize_install_mode(argv: list[str]) -> str:
    mode = os.environ.get("EXPLAIN_BOOK_INSTALL_MISSING", "ask").lower()
    if "--no-install-missing" in argv:
        return "no"
    if "--install-missing" in argv:
        idx = argv.index("--install-missing")
        if idx + 1 < len(argv) and not argv[idx + 1].startswith("--"):
            mode = argv[idx + 1].lower()
        else:
            mode = "yes"
    if mode in {"1", "true", "y", "yes", "install"}:
        return "yes"
    if mode in {"0", "false", "n", "no", "fallback", "skip"}:
        return "no"
    return "ask"


def offer_dependency_install(
    *,
    feature: str,
    module_names: list[str],
    fallback: str | None,
    install_mode: str,
) -> None:
    packages = missing_python_packages(module_names)
    if not packages:
        return

    message = f"{feature} uses {', '.join(packages)} if installed"
    if fallback:
        message += f", otherwise {fallback}"
    message += "."
    print(message)

    should_install = False
    if install_mode == "yes":
        should_install = True
    elif install_mode == "ask" and sys.stdin.isatty():
        answer = input("Missing package(s) detected. Do you want to install? y=install, n=fallback: ").strip().lower()
        should_install = answer in {"y", "yes", "install"}
    else:
        if fallback:
            print("Non-interactive mode or install disabled; using fallback.")
        else:
            print("Non-interactive mode or install disabled; installation skipped.")

    if not should_install:
        if fallback:
            print(f"Using fallback: {fallback}.")
        return

    if install_python_packages(packages):
        still_missing = missing_python_packages(module_names)
        if not still_missing:
            print("Package installation complete.")
            return
        print(f"Package installation incomplete; still missing: {', '.join(still_missing)}", file=sys.stderr)
    else:
        print("Package installation failed.", file=sys.stderr)

    if fallback:
        print(f"Using fallback: {fallback}.")


def prepare_dependencies(ext: str, extraction_mode: str, install_mode: str) -> None:
    if ext == ".pdf" and extraction_mode == "technical":
        offer_dependency_install(
            feature="Technical PDF extraction",
            module_names=["docling"],
            fallback="the PDF text fallback chain",
            install_mode=install_mode,
        )

    if ext == ".pdf" and not shutil.which("pdftotext"):
        offer_dependency_install(
            feature="PDF text extraction",
            module_names=["pypdf", "pdfminer"],
            fallback="any installed Python PDF parser; extraction fails if none are available",
            install_mode=install_mode,
        )

    if ext in HTML_EXTENSIONS:
        offer_dependency_install(
            feature="HTML extraction",
            module_names=["bs4"],
            fallback="a stdlib HTML parser",
            install_mode=install_mode,
        )

    if ext == ".docx":
        offer_dependency_install(
            feature="DOCX extraction",
            module_names=["docx"],
            fallback="a stdlib ZIP/XML parser",
            install_mode=install_mode,
        )

    if ext == ".rtf":
        offer_dependency_install(
            feature="RTF extraction",
            module_names=["striprtf"],
            fallback="a basic regex cleanup fallback",
            install_mode=install_mode,
        )


def run_dependency_check() -> int:
    """扫描所有格式的全部可选依赖，打印状态报告，并给出安装缺失项所需的
    确切命令。

    返回进程退出码：恒为 0（缺少可选依赖不算错误 —— 多数格式会降级到
    回退方案）。供 `extract.py --check` 使用。
    """
    print("explain-book — dependency check\n")

    missing_pip_packages: list[str] = []
    missing_system: list[tuple[str, str]] = []  # (名称, 安装提示)

    for group in DEPENDENCY_GROUPS:
        print(f"  {group['label']}")

        present_modules = [m for m in group["modules"] if python_module_available(m)]
        absent_modules = [m for m in group["modules"] if not python_module_available(m)]
        system_present = [c for c, _, _ in group["system"] if shutil.which(c)]
        system_absent = [c for c, _, _ in group["system"] if not shutil.which(c)]

        for module_name in group["modules"]:
            pip_name = PYTHON_DEPENDENCIES.get(module_name, module_name)
            ok = module_name in present_modules
            print(f"      {'✓' if ok else '✗'} python: {pip_name}")
            if not ok:
                missing_pip_packages.append(pip_name)
                hint = isolated_install_hint(module_name)
                if hint:
                    print(f"        ↳ {hint}")

        for cmd, pretty, hint in group["system"]:
            ok = cmd in system_present
            print(f"      {'✓' if ok else '✗'} system: {cmd} ({pretty})")
            if not ok:
                missing_system.append((pretty, hint))

        # 满足条件语义：
        #  - any_tool_suffices：任一提取器（模块或系统工具）存在即满足
        #  - any_of_modules：至少一个模块存在
        #  - 其他情况：列出的模块全部存在
        #  - 非替代关系的系统工具始终必需
        if group.get("any_tool_suffices"):
            satisfied = bool(present_modules) or bool(system_present)
        else:
            if group["modules"]:
                satisfied = bool(present_modules) if group["any_of_modules"] else not absent_modules
            else:
                satisfied = True
            if system_absent:
                satisfied = False

        if satisfied:
            status = "ready"
        elif group.get("required"):
            status = "MISSING — required, no fallback"
        else:
            status = "fallback available (install for best quality)"
        print(f"      → {status} — {group['note']}\n")

    # 去重且保持原有顺序
    missing_pip_packages = list(dict.fromkeys(missing_pip_packages))
    missing_system = list(dict.fromkeys(missing_system))

    if not missing_pip_packages and not missing_system:
        print("All optional dependencies are installed. You're ready for every format.")
        return 0

    print("To enable the best extractor for every format, install the missing pieces:\n")
    if missing_pip_packages:
        print(f"  {sys.executable} -m pip install {' '.join(missing_pip_packages)}")
    for pretty, hint in missing_system:
        print(f"  # {pretty}: {hint}")
    print(
        "\nNote: missing Python packages are optional — every format falls back "
        "to a stdlib parser or an alternative extractor."
    )
    return 0
