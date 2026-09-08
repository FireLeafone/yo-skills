#!/usr/bin/env python3
"""
项目分析辅助脚本：探测 Node / JVM / Python 等生态并输出 JSON。
脚本失败或缺少文件时，执行方可改为手工读取配置文件（见 SKILL.md）。
"""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def find_package_json(root: Path) -> dict | None:
    p = root / "package.json"
    if not p.is_file():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def extract_node_tech_stack(package_data: dict) -> dict:
    if not package_data:
        return {}
    tech = {
        "dependencies": package_data.get("dependencies", {}),
        "devDependencies": package_data.get("devDependencies", {}),
        "scripts": package_data.get("scripts", {}),
    }
    deps = {**tech["dependencies"], **tech["devDependencies"]}
    frameworks = []
    if "react" in deps:
        frameworks.append(f"React {deps.get('react', '')}")
    if "vue" in deps:
        frameworks.append(f"Vue {deps.get('vue', '')}")
    if "@angular/core" in deps:
        frameworks.append(f"Angular {deps.get('@angular/core', '')}")
    tech["frameworks"] = frameworks
    return tech


def _local_tag(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _child_by_local(parent: ET.Element, name: str) -> ET.Element | None:
    for c in parent:
        if _local_tag(c.tag) == name:
            return c
    return None


def parse_pom_basic(pom_path: Path) -> dict | None:
    """解析 pom.xml 基础坐标与多模块列表（忽略 Maven 命名空间差异）。"""
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
        artifact_el = _child_by_local(root, "artifactId")
        artifact = (artifact_el.text or "").strip() if artifact_el is not None else ""
        pack_el = _child_by_local(root, "packaging")
        packaging = (pack_el.text or "jar").strip() if pack_el is not None else "jar"
        parent_el = _child_by_local(root, "parent")
        parent_id = ""
        if parent_el is not None:
            pa = _child_by_local(parent_el, "artifactId")
            parent_id = (pa.text or "").strip() if pa is not None else ""
        modules: list[str] = []
        modules_el = _child_by_local(root, "modules")
        if modules_el is not None:
            for mod in modules_el:
                if _local_tag(mod.tag) == "module" and mod.text:
                    modules.append(mod.text.strip())
        return {
            "artifactId": artifact or None,
            "packaging": packaging or None,
            "parentArtifactId": parent_id or None,
            "modules": modules or None,
        }
    except (ET.ParseError, OSError):
        return None


def parse_gradle_hint(root: Path) -> dict:
    """不解析完整 Gradle AST，仅做存在性与 Spring 线索。"""
    for name in ("build.gradle", "build.gradle.kts"):
        p = root / name
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        spring = "spring-boot" in text.lower() or "org.springframework.boot" in text
        return {"buildFile": name, "springBootLikely": spring}
    return {}


def parse_pyproject_basic(py_path: Path) -> dict | None:
    try:
        text = py_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    out: dict = {"path": str(py_path.name)}
    # 极简正则提取 [project] name / version（无 TOML 库时）
    m = re.search(r'^\s*name\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if m:
        out["name"] = m.group(1)
    m = re.search(r'^\s*version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if m:
        out["version"] = m.group(1)
    m = re.search(r'^\s*requires-python\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if m:
        out["requiresPython"] = m.group(1)
    if sys.version_info >= (3, 11):
        try:
            import tomllib

            with open(py_path, "rb") as f:
                data = tomllib.load(f)
            proj = data.get("project") or {}
            if isinstance(proj, dict):
                out["name"] = proj.get("name") or out.get("name")
                out["version"] = proj.get("version") or out.get("version")
                rp = proj.get("requires-python")
                if rp:
                    out["requiresPython"] = rp
        except OSError:
            pass
        except Exception:
            pass
    return out

def summarize_requirements(req_path: Path, max_lines: int = 8) -> dict:
    try:
        lines = req_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {}
    nonblank = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]
    return {
        "path": str(req_path.name),
        "lineCount": len(lines),
        "nonCommentCount": len(nonblank),
        "sample": nonblank[:max_lines],
    }


def detect_jvm(root: Path) -> dict:
    out: dict = {"maven": False, "gradle": False}
    pom = root / "pom.xml"
    if pom.is_file():
        out["maven"] = True
        out["pom"] = parse_pom_basic(pom)
    gradle_files = [root / "build.gradle", root / "build.gradle.kts"]
    if any(f.is_file() for f in gradle_files):
        out["gradle"] = True
        hint = parse_gradle_hint(root)
        if hint:
            out["gradleHint"] = hint
    return out


def detect_python(root: Path) -> dict:
    out: dict = {}
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        out["pyproject"] = parse_pyproject_basic(pyproject)
    for name in ("requirements.txt", "Pipfile"):
        p = root / name
        if p.is_file():
            if name == "requirements.txt":
                out["requirements"] = summarize_requirements(p)
            else:
                out["pipfile"] = name
    for p in sorted(root.glob("requirements-*.txt")):
        out.setdefault("requirementsExtras", []).append(p.name)
    if (root / "setup.py").is_file():
        out["setupPy"] = True
    if (root / "setup.cfg").is_file():
        out["setupCfg"] = True
    return out


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python analyze_project.py <project_root_dir>", file=sys.stderr)
        sys.exit(1)

    root_dir = Path(sys.argv[1]).resolve()
    if not root_dir.is_dir():
        print(json.dumps({"error": "not a directory", "path": str(root_dir)}))
        sys.exit(1)

    package_data = find_package_json(root_dir)
    detected: dict = {
        "node": package_data is not None,
        "jvm": (root_dir / "pom.xml").is_file()
        or (root_dir / "build.gradle").is_file()
        or (root_dir / "build.gradle.kts").is_file(),
        "python": bool(
            (root_dir / "pyproject.toml").is_file()
            or (root_dir / "requirements.txt").is_file()
            or (root_dir / "Pipfile").is_file()
            or (root_dir / "setup.py").is_file()
        ),
    }

    result: dict = {
        "projectRoot": str(root_dir),
        "detected": detected,
    }

    if package_data:
        result["node"] = extract_node_tech_stack(package_data)

    if detected["jvm"]:
        result["jvm"] = detect_jvm(root_dir)

    if detected["python"]:
        py = detect_python(root_dir)
        if py:
            result["python"] = py

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
