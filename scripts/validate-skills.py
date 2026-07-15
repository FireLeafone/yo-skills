#!/usr/bin/env python3
"""Validate all skills in the yo-skills repository against Agent Skills spec."""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: pyyaml. Run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
    "disable-model-invocation",
    "argument-hint",
}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SKIP_DIRS = {"_template", ".git", "node_modules", "__pycache__"}

def parse_frontmatter(content: str) -> tuple[dict | None, str | None]:
    if not content.startswith("---"):
        return None, "Missing YAML frontmatter (must start with ---)"
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return None, "Invalid frontmatter block"
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return None, f"Invalid YAML: {exc}"
    if not isinstance(data, dict):
        return None, "Frontmatter must be a YAML mapping"
    return data, None

def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{skill_dir.name}: SKILL.md not found"]
    content = skill_md.read_text(encoding="utf-8")
    frontmatter, err = parse_frontmatter(content)
    if err:
        return [f"{skill_dir.name}: {err}"]
    unexpected = set(frontmatter.keys()) - ALLOWED_FRONTMATTER_KEYS
    if unexpected:
        errors.append(
            f"{skill_dir.name}: unexpected frontmatter keys: {', '.join(sorted(unexpected))}"
        )
    name = frontmatter.get("name")
    if not name:
        errors.append(f"{skill_dir.name}: missing 'name' in frontmatter")
    elif not isinstance(name, str):
        errors.append(f"{skill_dir.name}: 'name' must be a string")
    else:
        name = name.strip()
        if name != skill_dir.name:
            errors.append(
                f"{skill_dir.name}: frontmatter name '{name}' must match directory name"
            )
        if not NAME_PATTERN.match(name):
            errors.append(f"{skill_dir.name}: invalid name format '{name}'")
        if len(name) > 64:
            errors.append(f"{skill_dir.name}: name exceeds 64 characters")
    description = frontmatter.get("description")
    if not description:
        errors.append(f"{skill_dir.name}: missing 'description' in frontmatter")
    elif not isinstance(description, str) or not description.strip():
        errors.append(f"{skill_dir.name}: 'description' must be a non-empty string")
    elif len(description.strip()) > 1024:
        errors.append(f"{skill_dir.name}: description exceeds 1024 characters")
    body = content.split("---", 2)[-1].strip()
    if not body:
        errors.append(f"{skill_dir.name}: SKILL.md body is empty")
    if len(content.splitlines()) > 500:
        errors.append(f"{skill_dir.name}: SKILL.md exceeds 500 lines (consider progressive disclosure)")
    return errors

def discover_skills(skills_root: Path) -> list[Path]:
    if not skills_root.is_dir():
        return []
    skills: list[Path] = []
    for child in sorted(skills_root.iterdir()):
        if not child.is_dir() or child.name in SKIP_DIRS or child.name.startswith("."):
            continue
        if (child / "SKILL.md").exists():
            skills.append(child)
    return skills

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate yo-skills skills")
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "skills",
        help="Path to skills directory",
    )
    parser.add_argument(
        "--skill",
        type=str,
        default=None,
        help="Validate a single skill by directory name",
    )
    args = parser.parse_args()
    skills_root = args.skills_dir.resolve()
    skills = discover_skills(skills_root)
    if args.skill:
        skills = [p for p in skills if p.name == args.skill]
        if not skills:
            print(f"Skill not found: {args.skill}", file=sys.stderr)
            return 1
    if not skills:
        print(f"No skills found under {skills_root}")
        return 0
    all_errors: list[str] = []
    for skill in skills:
        all_errors.extend(validate_skill(skill))
    if all_errors:
        print("Validation failed:\n")
        for err in all_errors:
            print(f"  - {err}")
        return 1
    print(f"OK: {len(skills)} skill(s) validated")
    for skill in skills:
        print(f"  - {skill.name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())