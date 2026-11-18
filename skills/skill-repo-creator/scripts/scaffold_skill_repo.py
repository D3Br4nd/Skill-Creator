#!/usr/bin/env python3
"""Scaffold a standalone git repository that packages one Agent Skill.

Creates <dest>/<name>/ from the templates in ../assets/repo-template/, copies
the validator into it, links the skill into the in-repo agent directories and
runs `git init`. Nothing is committed and nothing is pushed.

Usage:
    python3 scaffold_skill_repo.py --name NAME --description TEXT --dest PARENT_DIR
                                   [--title TEXT] [--author TEXT] [--lang en|it]
                                   [--no-git] [--no-dev-links] [--allow-nested]

Exit status: 0 = repository created, 1 = refused (the message says why).
Standard library only; Python 3.8+.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # keep __pycache__ out of the skill folder

import argparse
import datetime
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import validate_skill as rules  # noqa: E402  (sibling module; single source for naming rules)

TEMPLATE_DIR = SCRIPT_DIR.parent / "assets" / "repo-template"
PLATFORMS_SNAPSHOT = SCRIPT_DIR.parent / "references" / "platforms.md"
VALIDATOR = SCRIPT_DIR / "validate_skill.py"
NAME_PLACEHOLDER = "__SKILL_NAME__"
README_TEMPLATES = {"en": "README.md.tmpl", "it": "README.it.md.tmpl"}
# Folded YAML lines stay well under common 100-column limits once indented.
YAML_WRAP_WIDTH = 86


def fail(message):
    print("error: " + message, file=sys.stderr)
    sys.exit(1)


def git(*args, cwd=None):
    """Run git; return (ok, stdout). A missing git binary counts as not ok."""
    try:
        done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    except OSError:
        return False, ""
    return done.returncode == 0, done.stdout.strip()


def snapshot_date():
    """Return the date on which the install paths shipped in the README were last verified."""
    try:
        text = PLATFORMS_SNAPSHOT.read_text(encoding="utf-8")
    except OSError:
        fail("%s not found (the skill folder is incomplete)" % PLATFORMS_SNAPSHOT)
    match = re.search(r"Verified on (\d{4}-\d{2}-\d{2})", text)
    if not match:
        fail("%s has no 'Verified on YYYY-MM-DD' line; restore it so READMEs can state the date" % PLATFORMS_SNAPSHOT)
    return match.group(1)


def output_path(relative, lang):
    """Map a template path to its output path, or None when it does not apply."""
    name = relative.name
    if name in README_TEMPLATES.values():
        if name != README_TEMPLATES[lang]:
            return None
        return relative.with_name("README.md")
    if name.endswith(".tmpl"):
        name = name[: -len(".tmpl")]
    if name.startswith("dot-"):
        name = "." + name[len("dot-"):]
    return relative.with_name(name)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Scaffold a standalone git repository for one Agent Skill.",
        epilog="Next: replace every TODO marker, then run <repo>/scripts/validate_skill.py until it reports 0 errors.",
    )
    parser.add_argument("--name", required=True, help="skill name: lowercase letters, digits, hyphens; also the repo folder name")
    parser.add_argument("--description", required=True, help="what the skill does and when to use it (third person, max 1024 chars)")
    parser.add_argument("--dest", required=True, help="existing parent directory; the repo is created at DEST/NAME")
    parser.add_argument("--title", help="human-readable title (default: derived from the name)")
    parser.add_argument("--author", help="copyright holder for the MIT license (default: git config user.name)")
    parser.add_argument("--lang", choices=sorted(README_TEMPLATES), default="en", help="language of the README (default: en)")
    parser.add_argument("--no-git", action="store_true", help="do not run git init")
    parser.add_argument("--no-dev-links", action="store_true", help="do not symlink the skill into .claude/skills and .agents/skills")
    parser.add_argument("--allow-nested", action="store_true", help="allow creating the repo inside an existing git work tree")
    args = parser.parse_args(argv)

    name = args.name.strip()
    problems = rules.check_name(name)
    if problems:
        fail("invalid --name:\n  - " + "\n  - ".join(problems))
    description = " ".join(args.description.split())
    errors, warnings = rules.check_description(description)
    if errors:
        fail("invalid --description:\n  - " + "\n  - ".join(errors))

    if not TEMPLATE_DIR.is_dir():
        fail("template directory not found: %s (the skill folder is incomplete)" % TEMPLATE_DIR)
    parent = Path(args.dest).expanduser().resolve()
    if not parent.is_dir():
        fail("--dest %s does not exist; create it first or pass an existing directory" % parent)
    target = parent / name
    if target.exists() and any(target.iterdir()):
        fail("%s already exists and is not empty; choose another name or remove it yourself" % target)
    inside_repo, _ = git("rev-parse", "--is-inside-work-tree", cwd=str(parent))
    if inside_repo and not args.allow_nested:
        fail(
            "%s is inside a git repository; a skill repo must be standalone. "
            "Pick a --dest outside it, or pass --allow-nested if this is intended." % parent
        )

    author = args.author or git("config", "user.name")[1]
    if not author:
        fail("no author: pass --author \"Name\" (git config user.name is not set)")
    today = datetime.date.today()
    title = args.title or " ".join(word.capitalize() for word in name.split("-"))
    folded = textwrap.fill(description, width=YAML_WRAP_WIDTH, break_long_words=False, break_on_hyphens=False)
    tokens = {
        "SKILL_NAME": name,
        "SKILL_TITLE": title,
        "DESCRIPTION": description,
        "DESCRIPTION_YAML": folded.replace("\n", "\n  "),
        "AUTHOR": author,
        "AUTHOR_YAML": author.replace("\\", "\\\\").replace('"', '\\"'),
        "YEAR": str(today.year),
        "DATE": today.isoformat(),
        "SNAPSHOT_DATE": snapshot_date(),
    }

    created = []
    for source in sorted(TEMPLATE_DIR.rglob("*")):
        if not source.is_file() or source.name == ".DS_Store":
            continue
        relative = output_path(source.relative_to(TEMPLATE_DIR), args.lang)
        if relative is None:
            continue
        destination = target / Path(str(relative).replace(NAME_PLACEHOLDER, name))
        destination.parent.mkdir(parents=True, exist_ok=True)
        text = source.read_text(encoding="utf-8")
        # Single pass, so inserted values are never re-scanned for tokens.
        text = re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: tokens.get(m.group(1), m.group(0)), text)
        destination.write_text(text, encoding="utf-8")
        created.append(destination)

    scripts_dir = target / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    shutil.copyfile(str(VALIDATOR), str(scripts_dir / "validate_skill.py"))
    created.append(scripts_dir / "validate_skill.py")

    notes = []
    if not args.no_dev_links:
        for link_dir in rules.DEV_LINK_DIRS:
            link = target / link_dir / name
            link.parent.mkdir(parents=True, exist_ok=True)
            try:
                link.symlink_to(Path("..") / ".." / "skills" / name, target_is_directory=True)
                created.append(link)
            except OSError as exc:
                notes.append("could not create symlink %s (%s); install the skill manually to test it" % (link, exc))

    if not args.no_git:
        ok, _ = git("init", "-b", "main", cwd=str(target))
        if not ok:  # git older than 2.28 has no -b flag
            ok, _ = git("init", cwd=str(target))
            if ok:
                git("symbolic-ref", "HEAD", "refs/heads/main", cwd=str(target))
        if not ok:
            notes.append("git init failed or git is not installed; initialise the repository manually")

    print("Created skill repository: %s" % target)
    for path in sorted(created):
        print("  " + path.relative_to(target).as_posix())
    for warning in warnings:
        print("warning: " + warning)
    for note in notes:
        print("note: " + note)
    print("Next: replace every TODO marker, then run: python3 %s" % (scripts_dir / "validate_skill.py"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
