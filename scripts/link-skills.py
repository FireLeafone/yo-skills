#!/usr/bin/env python3
"""Create symlinks from yo-skills skills into a local test project's .agents/skills/."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {"_template", ".git", "node_modules", "__pycache__"}

# Default skill subdirectories per agent, relative to the target project root.
AGENT_SKILL_SUBDIRS: dict[str, Path] = {
    "codex": Path(".agents") / "skills",
    "cursor": Path(".cursor") / "skills",
    "kimi": Path(".kimi") / "skills",
    "claude": Path(".claude") / "skills",
}
DEFAULT_AGENT = "claude"
DEFAULT_SKILLS_SUBDIR = AGENT_SKILL_SUBDIRS[DEFAULT_AGENT]


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


def resolve_existing_target(link_path: Path) -> Path | None:
    if not link_path.exists() and not link_path.is_symlink():
        return None
    try:
        return link_path.resolve()
    except OSError:
        return None


def is_valid_link(link_path: Path, expected_target: Path) -> bool:
    existing = resolve_existing_target(link_path)
    if existing is None:
        return False
    return existing == expected_target.resolve()


def remove_link(link_path: Path) -> None:
    if link_path.is_symlink():
        link_path.unlink()
        return
    if sys.platform == "win32" and link_path.is_dir():
        try:
            link_path.rmdir()
        except OSError as exc:
            raise RuntimeError(
                f"Cannot remove existing path (expected symlink/junction): {link_path}"
            ) from exc
        return
    if link_path.exists():
        raise RuntimeError(
            f"Refusing to replace non-link path: {link_path}. Remove it manually or pick another target."
        )


def create_directory_link(source: Path, link_path: Path) -> str:
    source = source.resolve()
    link_path.parent.mkdir(parents=True, exist_ok=True)

    if sys.platform == "win32":
        try:
            os.symlink(source, link_path, target_is_directory=True)
            return "symlink"
        except OSError:
            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link_path), str(source)],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "").strip()
                raise RuntimeError(
                    "Failed to create Windows junction. Enable Developer Mode or run as Administrator, "
                    f"or remove the blocking path.\n{detail}"
                )
            return "junction"

    os.symlink(source, link_path, target_is_directory=True)
    return "symlink"


def link_skill(source: Path, link_path: Path, force: bool, dry_run: bool) -> tuple[str, str]:
    source = source.resolve()
    expected_target = source

    if is_valid_link(link_path, expected_target):
        return "skipped", "already linked"

    if link_path.exists() or link_path.is_symlink():
        if not force:
            existing = resolve_existing_target(link_path)
            detail = f" -> {existing}" if existing else ""
            raise RuntimeError(
                f"Target already exists: {link_path}{detail}. Use --force to replace."
            )
        if not dry_run:
            remove_link(link_path)

    if dry_run:
        return "planned", f"{link_path} -> {source}"

    link_type = create_directory_link(source, link_path)
    return "linked", f"{link_type}: {link_path} -> {source}"


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(
        description="Link yo-skills skills into a local test project for Agents (.agents/skills/)."
    )
    parser.add_argument(
        "--target",
        "-t",
        type=Path,
        required=True,
        help="Local test project root path",
    )
    parser.add_argument(
        "--skill",
        "-s",
        type=str,
        default=None,
        help="Link a single skill by directory name (default: all skills)",
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        default=repo_root / "skills",
        help="Path to yo-skills skills source directory",
    )
    parser.add_argument(
        "--agent",
        "-a",
        type=str,
        choices=list(AGENT_SKILL_SUBDIRS.keys()),
        default=None,
        help="Target agent (sets default skills-subdir): codex, cursor, kimi, claude",
    )
    parser.add_argument(
        "--skills-subdir",
        type=Path,
        default=None,
        help="Skills directory relative to the test project (overrides --agent default)",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Replace existing symlinks/junctions",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned links without creating them",
    )
    args = parser.parse_args()

    skills_root = args.skills_dir.resolve()
    project_root = args.target.resolve()

    if args.skills_subdir:
        skills_dest_root = project_root / args.skills_subdir
    elif args.agent:
        skills_dest_root = project_root / AGENT_SKILL_SUBDIRS[args.agent]
    else:
        skills_dest_root = project_root / DEFAULT_SKILLS_SUBDIR

    if not project_root.is_dir():
        print(f"Target project path not found: {project_root}", file=sys.stderr)
        return 1

    skills = discover_skills(skills_root)
    if args.skill:
        skills = [path for path in skills if path.name == args.skill]
        if not skills:
            print(f"Skill not found: {args.skill}", file=sys.stderr)
            return 1

    if not skills:
        print(f"No skills found under {skills_root}", file=sys.stderr)
        return 1

    linked = 0
    skipped = 0
    planned = 0

    for skill in skills:
        link_path = skills_dest_root / skill.name
        try:
            status, message = link_skill(skill, link_path, args.force, args.dry_run)
        except RuntimeError as exc:
            print(f"Error linking {skill.name}: {exc}", file=sys.stderr)
            return 1

        print(message)
        if status == "linked":
            linked += 1
        elif status == "skipped":
            skipped += 1
        elif status == "planned":
            planned += 1

    action = "Would link" if args.dry_run else "Linked"
    print(
        f"\n{action} {linked + planned} skill(s), skipped {skipped}. "
        f"Destination: {skills_dest_root}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
