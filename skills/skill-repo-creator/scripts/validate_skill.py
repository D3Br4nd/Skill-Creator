#!/usr/bin/env python3
"""Validate an Agent Skill, or a repository that packages one, before it ships.

Checks the Agent Skills specification (https://agentskills.io/specification),
the portable-frontmatter rules shared by the major agents, and this project's
repository conventions. Standard library only; Python 3.8+.

Usage:
    python3 validate_skill.py [PATH] [--strict]

PATH is a skill directory (contains SKILL.md) or a skill repository (contains
skills/<name>/SKILL.md). Without PATH, the repository that holds this script is
validated when the script lives in <repo>/scripts/; otherwise the current
directory is used.

Exit status: 0 = no errors, 1 = errors found (or warnings with --strict),
2 = PATH is neither a skill nor a skill repository.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# --- Limits and rules, each traced to its source ---------------------------

# agentskills.io/specification: the only frontmatter fields the standard defines.
# Claude's upload surfaces reject any other top-level key with a hard error.
ALLOWED_KEYS = ("name", "description", "license", "compatibility", "metadata", "allowed-tools")
NAME_MAX = 64            # specification: name is 1-64 characters
DESCRIPTION_MAX = 1024   # specification: description is 1-1024 characters
COMPATIBILITY_MAX = 500  # specification: compatibility is 1-500 characters
BODY_MAX_LINES = 500     # specification + Anthropic best practices: keep SKILL.md under 500 lines
REFERENCE_TOC_LINES = 100  # Anthropic best practices: reference files over 100 lines need a contents list
MIN_EVALS = 3            # Anthropic best practices checklist: at least three evaluations
MIN_TRIGGER_QUERIES = 8  # agentskills.io: ~20 queries recommended; 8 is the floor for a useful signal
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RESERVED_WORDS = ("anthropic", "claude")  # Anthropic: reserved words not allowed in name
VAGUE_NAMES = {"helper", "helpers", "utils", "tools", "documents", "data", "files", "misc", "skill"}

# Markers left behind by scaffold_skill_repo.py until the author replaces them.
SCAFFOLD_TOKENS = (
    "{{SKILL_NAME}}", "{{SKILL_TITLE}}", "{{DESCRIPTION}}", "{{DESCRIPTION_YAML}}",
    "{{AUTHOR}}", "{{AUTHOR_YAML}}", "{{YEAR}}", "{{DATE}}", "{{SNAPSHOT_DATE}}",
)
TODO_MARKER = "[[TODO"

REQUIRED_REPO_FILES = ("README.md", "LICENSE", ".gitignore", "AGENTS.md")
DEV_LINK_DIRS = (".claude/skills", ".agents/skills")
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".txt", ".toml", ""}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}

KEY_RE = re.compile(r"^([A-Za-z_][\w.\-/]*)\s*:(?:\s+(.*))?\s*$")
BLOCK_HEADER_RE = re.compile(r"^[>|][+\-]?[1-9]?[+\-]?\s*(#.*)?$")
BOOL_RE = re.compile(r"^(true|false|yes|no|on|off)$", re.I)
NULL_RE = re.compile(r"^(null|~)$", re.I)
NUMBER_RE = re.compile(r"^[-+]?(0x[0-9a-f_]+|0o[0-7_]+|(\d[\d_]*(\.\d*)?|\.\d+)(e[-+]?\d+)?)$", re.I)
LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'][^\"']*[\"'])?\s*\)")
WHEN_CUE_RE = re.compile(
    r"\buse (this skill )?(when|whenever|for|if|to)\b|\bwhen (the|a) user\b|\bwhen working\b"
    r"|\busa(re)? (questa skill )?quando\b|\bda usare quando\b|\bquando l.utente\b",
    re.I,
)
POV_RE = re.compile(
    r"^\s*(I|We|You)\b|\bI can\b|\bI will\b|\bI'll\b|\byou can use\b|\bposso\b|\bpuoi usare\b|\bti aiuto\b",
    re.I,
)
AGENT_SPECIFIC = (
    (re.compile(r"\$\{CLAUDE_[A-Z_]+\}"), "an agent-specific substitution variable"),
    (re.compile(r"\$ARGUMENTS\b"), "an agent-specific argument placeholder"),
    (re.compile(r"(^|\s)!`[^`\n]+`"), "agent-specific shell injection syntax"),
    (re.compile(r"~/\.(claude|codex|gemini|agents|config/opencode)\b"), "an agent-specific install path"),
)
WINDOWS_PATH_RE = re.compile(r"\b(scripts|references|reference|assets|resources|examples)\\[\w.\-]+")
TOC_HEADING_RE = re.compile(r"^#{1,4}\s*(table of contents|contents|indice|sommario)\b", re.I)


class Report:
    """Collects findings so every problem is shown in one run."""

    def __init__(self):
        self.items = []

    def error(self, where, message):
        self.items.append(("ERROR", where, message))

    def warn(self, where, message):
        self.items.append(("WARN", where, message))

    def count(self, level):
        return sum(1 for item in self.items if item[0] == level)


class Field:
    """One frontmatter value. kind: str | bool | number | null | map | list."""

    __slots__ = ("kind", "value", "line")

    def __init__(self, kind, value, line):
        self.kind = kind
        self.value = value
        self.line = line


class FrontmatterError(Exception):
    pass


# --- Frontmatter parsing (YAML subset used by SKILL.md) ---------------------

def split_frontmatter(text):
    """Return (frontmatter_lines, body_lines, first_body_line_number)."""
    lines = [line.rstrip("\r") for line in text.split("\n")]
    if not lines or lines[0].rstrip() != "---":
        raise FrontmatterError(
            "line 1 must be '---' to open the YAML frontmatter; agents ignore frontmatter that starts later"
        )
    for index in range(1, len(lines)):
        if lines[index].rstrip() == "---":
            return lines[1:index], lines[index + 1:], index + 2
    raise FrontmatterError("frontmatter is never closed: add a '---' line after the last field")


def parse_scalar(raw):
    """Parse a one-line YAML scalar. Return (kind, value, problem_or_None)."""
    text = raw.strip()
    if not text:
        return "null", None, None
    if text[0] == '"':
        match = re.match(r'^"((?:[^"\\]|\\.)*)"\s*(#.*)?$', text)
        if not match:
            return "str", text, "double-quoted value is not closed, or has an unescaped quote inside"
        escapes = {"n": "\n", "t": "\t"}
        return "str", re.sub(r"\\(.)", lambda m: escapes.get(m.group(1), m.group(1)), match.group(1)), None
    if text[0] == "'":
        match = re.match(r"^'((?:[^']|'')*)'\s*(#.*)?$", text)
        if not match:
            return "str", text, "single-quoted value is not closed (write a literal quote as '')"
        return "str", match.group(1).replace("''", "'"), None
    problem = None
    if text[0] in "[{*&!|>%@`" or text.startswith(("- ", "? ")):
        problem = "value starts with %r, which YAML treats as syntax; wrap the value in double quotes" % text[0]
    elif re.search(r":(\s|$)", text):
        problem = "unquoted value contains ': ', which breaks YAML parsing; wrap it in double quotes or use a '>-' block"
    elif re.search(r"\s#", text):
        problem = "unquoted value contains ' #', which YAML reads as a comment; wrap the value in double quotes"
    if NULL_RE.match(text):
        return "null", None, problem
    if BOOL_RE.match(text):
        return "bool", text, problem
    if NUMBER_RE.match(text):
        return "number", text, problem
    return "str", text, problem


def fold_block(block, folded):
    """Resolve a '>' (folded) or '|' (literal) block scalar to its text."""
    indents = [len(line) - len(line.lstrip(" ")) for line in block if line.strip()]
    if not indents:
        return ""
    base = min(indents)
    lines = [line[base:] if line.strip() else "" for line in block]
    if not folded:
        return "\n".join(lines).strip()
    paragraphs, current = [], []
    for line in lines:
        if line.strip():
            current.append(line.strip())
        elif current:
            paragraphs.append(" ".join(current))
            current = []
    if current:
        paragraphs.append(" ".join(current))
    return "\n".join(paragraphs).strip()


def parse_map(block, first_line):
    """Parse an indented flat mapping. Return (entries, problems)."""
    entries, problems, base = {}, [], None
    for offset, line in enumerate(block):
        lineno = first_line + offset
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if base is None:
            base = indent
        if indent != base:
            problems.append((lineno, "nested or misaligned entry; this must be a flat map of string keys to string values"))
            continue
        match = re.match(r"^\s*(\"[^\"]+\"|'[^']+'|[^\s:#][^:#]*?)\s*:(?:\s+(.*))?\s*$", line)
        if not match:
            problems.append((lineno, "cannot parse this line as 'key: value'"))
            continue
        kind, value, problem = parse_scalar(match.group(2) or "")
        if problem:
            problems.append((lineno, problem))
        entries[match.group(1).strip("\"'")] = Field(kind, value, lineno)
    return entries, problems


def parse_frontmatter(fm_lines):
    """Return ({key: Field}, [(line_number, problem)]). Line numbers are file lines."""
    fields, problems, index, total = {}, [], 0, len(fm_lines)
    while index < total:
        line, lineno = fm_lines[index], index + 2
        if not line.strip() or line.strip().startswith("#"):
            index += 1
            continue
        if line[0] in " \t":
            problems.append((lineno, "unexpected indentation: top-level keys start at column 1"))
            index += 1
            continue
        match = KEY_RE.match(line)
        if not match:
            problems.append((lineno, "cannot parse this line as 'key: value' (a space is required after the colon)"))
            index += 1
            continue
        key, rest = match.group(1), (match.group(2) or "").strip()
        end = index + 1
        while end < total and (not fm_lines[end].strip() or fm_lines[end][0] in " \t"):
            end += 1
        block = fm_lines[index + 1:end]
        while block and not block[-1].strip():
            block.pop()
        if key in fields:
            problems.append((lineno, "duplicate key %r" % key))
        if BLOCK_HEADER_RE.match(rest):
            fields[key] = Field("str", fold_block(block, rest[0] == ">"), lineno)
        elif not rest or rest.startswith("#"):
            content = [b for b in block if b.strip() and not b.strip().startswith("#")]
            if not content:
                fields[key] = Field("null", None, lineno)
            elif content[0].strip() == "-" or content[0].strip().startswith("- "):
                fields[key] = Field("list", [c.strip()[1:].strip() for c in content], lineno)
            else:
                entries, map_problems = parse_map(block, lineno + 1)
                fields[key] = Field("map", entries, lineno)
                problems.extend(map_problems)
        else:
            continued = " ".join([rest] + [b.strip() for b in block if b.strip()])
            kind, value, problem = parse_scalar(continued)
            if problem:
                problems.append((lineno, problem))
            fields[key] = Field(kind, value, lineno)
        index = end
    return fields, problems


# --- Reusable rule checks (also imported by scaffold_skill_repo.py) ---------

def check_name(name, directory_name=None):
    """Return the list of rule violations for a skill name."""
    if not name:
        return ["name is empty"]
    errors = []
    if len(name) > NAME_MAX:
        errors.append("name is %d characters; the maximum is %d" % (len(name), NAME_MAX))
    if not NAME_RE.match(name):
        errors.append(
            "name %r must use only lowercase letters, digits and single hyphens, "
            "and must not start or end with a hyphen" % name
        )
    for word in RESERVED_WORDS:
        if word in name:
            errors.append("name contains the reserved word %r, which Claude's upload surfaces reject" % word)
    if directory_name is not None and name != directory_name:
        errors.append("name %r must equal its directory name %r" % (name, directory_name))
    return errors


def check_description(description):
    """Return (errors, warnings) for a description string."""
    errors, warnings = [], []
    if not description or not description.strip():
        return ["description is empty; agents use it to decide when to load the skill"], warnings
    if len(description) > DESCRIPTION_MAX:
        errors.append("description is %d characters; the maximum is %d" % (len(description), DESCRIPTION_MAX))
    if "<" in description or ">" in description:
        errors.append("description contains '<' or '>'; XML-like tags are rejected, use square brackets instead")
    if len(description) < 40:
        warnings.append("description is very short; say what the skill does and when to use it, with trigger keywords")
    if not WHEN_CUE_RE.search(description):
        warnings.append("description has no 'Use when ...' clause; state the situations that should trigger the skill")
    if POV_RE.search(description):
        warnings.append("description should be in third person ('Extracts ...'), not first or second person")
    return errors, warnings


# --- Markdown helpers -------------------------------------------------------

def strip_code(lines):
    """Blank out fenced blocks and inline code so example links are not followed."""
    cleaned, fence = [], None
    for line in lines:
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence is None and marker:
            fence = (marker.group(1)[0], len(marker.group(1)))
            cleaned.append("")
        elif fence is not None:
            if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= fence[1]:
                fence = None
            cleaned.append("")
        else:
            cleaned.append(re.sub(r"`+[^`\n]*`+", "", line))
    return cleaned


def local_links(lines):
    """Yield (line_number, target) for relative links outside code."""
    for number, line in enumerate(strip_code(lines), start=1):
        for match in LINK_RE.finditer(line):
            target = match.group(1)
            if re.match(r"^[a-z][a-z0-9+.\-]*:", target, re.I) or target.startswith(("#", "//")):
                continue
            target = target.split("#", 1)[0]
            if target:
                yield number, target


def read_text(path):
    return path.read_text(encoding="utf-8", errors="replace")


def iter_text_files(root):
    """Yield text files under root, skipping templates, VCS data and eval workspaces."""
    for dirpath, dirnames, filenames in os.walk(str(root)):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.endswith("-workspace"))
        for filename in sorted(filenames):
            path = Path(dirpath) / filename
            if filename == ".DS_Store" or path.suffix == ".tmpl" or path.is_symlink():
                continue
            if path.suffix.lower() in TEXT_SUFFIXES:
                yield path


def check_placeholders(root, report):
    for path in iter_text_files(root):
        rel = path.relative_to(root).as_posix()
        for number, line in enumerate(read_text(path).splitlines(), start=1):
            if TODO_MARKER in line:
                report.error("%s:%d" % (rel, number), "unfilled TODO marker; replace it with real content")
            for token in SCAFFOLD_TOKENS:
                if token in line:
                    report.error("%s:%d" % (rel, number), "unreplaced scaffold token %s" % token)


# --- Skill validation -------------------------------------------------------

def check_evals(skill_dir, name, prefix, report):
    evals_path = skill_dir / "evals" / "evals.json"
    where = prefix + "evals/evals.json"
    if not evals_path.is_file():
        report.error(where, "missing; add at least %d test cases (prompt + expected_output)" % MIN_EVALS)
    else:
        try:
            data = json.loads(read_text(evals_path))
        except ValueError as exc:
            report.error(where, "not valid JSON: %s" % exc)
            data = None
        if data is not None:
            if not isinstance(data, dict) or not isinstance(data.get("evals"), list):
                report.error(where, "expected an object with 'skill_name' and an 'evals' array")
            else:
                if data.get("skill_name") != name:
                    report.error(where, "skill_name %r must equal the skill name %r" % (data.get("skill_name"), name))
                cases = data["evals"]
                if len(cases) < MIN_EVALS:
                    report.error(where, "has %d test case(s); at least %d are required" % (len(cases), MIN_EVALS))
                seen = set()
                for position, case in enumerate(cases, start=1):
                    if not isinstance(case, dict):
                        report.error(where, "test case %d is not an object" % position)
                        continue
                    if case.get("id") in seen or case.get("id") is None:
                        report.error(where, "test case %d needs a unique 'id'" % position)
                    seen.add(case.get("id"))
                    for key in ("prompt", "expected_output"):
                        if not isinstance(case.get(key), str) or not case[key].strip():
                            report.error(where, "test case %d has no %r text" % (position, key))
                    for listed in case.get("files") or []:
                        if not (skill_dir / str(listed)).exists():
                            report.error(where, "test case %d lists a missing file: %s" % (position, listed))
    queries_path = skill_dir / "evals" / "eval_queries.json"
    where = prefix + "evals/eval_queries.json"
    if not queries_path.is_file():
        report.warn(where, "missing; add should-trigger and should-not-trigger queries to test the description")
        return
    try:
        queries = json.loads(read_text(queries_path))
    except ValueError as exc:
        report.error(where, "not valid JSON: %s" % exc)
        return
    valid = isinstance(queries, list) and all(
        isinstance(q, dict) and isinstance(q.get("query"), str) and isinstance(q.get("should_trigger"), bool)
        for q in queries
    )
    if not valid:
        report.error(where, "expected an array of {\"query\": string, \"should_trigger\": true|false}")
        return
    kinds = {q["should_trigger"] for q in queries}
    if len(queries) < MIN_TRIGGER_QUERIES or kinds != {True, False}:
        report.warn(
            where,
            "has %d queries; write at least %d, mixing should-trigger and near-miss should-not-trigger cases"
            % (len(queries), MIN_TRIGGER_QUERIES),
        )


def validate_skill(skill_dir, report, prefix="", scan_placeholders=True):
    """Validate one skill directory. Return the skill name, or None if unreadable."""
    where = prefix + "SKILL.md"
    if "SKILL.md" not in os.listdir(str(skill_dir)):
        report.error(where, "missing; the file must be named exactly SKILL.md (upper case)")
        return None
    text = read_text(skill_dir / "SKILL.md")
    if text.startswith("﻿"):
        report.error(where, "starts with a UTF-8 byte-order mark; save the file without a BOM")
        text = text[1:]
    try:
        fm_lines, body_lines, body_start = split_frontmatter(text)
    except FrontmatterError as exc:
        report.error(where, str(exc))
        return None
    fields, problems = parse_frontmatter(fm_lines)
    for lineno, problem in problems:
        report.error("%s:%d" % (where, lineno), problem)
    try:
        import yaml  # optional second opinion when PyYAML happens to be installed
    except ImportError:
        yaml = None
    if yaml is not None:
        try:
            if not isinstance(yaml.safe_load("\n".join(fm_lines)), dict):
                report.error(where, "frontmatter is not a YAML mapping")
        except yaml.YAMLError as exc:
            report.error(where, "frontmatter is not valid YAML: %s" % " ".join(str(exc).split()))

    for key, field in fields.items():
        if key not in ALLOWED_KEYS:
            report.error(
                "%s:%d" % (where, field.line),
                "top-level key %r is not portable (allowed: %s); move agent-specific settings under 'metadata'"
                % (key, ", ".join(ALLOWED_KEYS)),
            )

    def text_field(key, required=False):
        field = fields.get(key)
        if field is None or field.kind == "null":
            if required:
                report.error(where, "required field %r is missing or empty" % key)
            return None
        if field.kind != "str":
            report.error("%s:%d" % (where, field.line), "%r must be a string (found a %s); quote it" % (key, field.kind))
            return None
        return field.value

    name = text_field("name", required=True)
    if name is not None:
        for message in check_name(name, skill_dir.name):
            report.error("%s:%d" % (where, fields["name"].line), message)
        if name in VAGUE_NAMES:
            report.warn(where, "name %r is too generic; name the task (e.g. 'processing-pdfs')" % name)

    description = text_field("description", required=True)
    if description is not None:
        errors, warnings = check_description(description)
        for message in errors:
            report.error("%s:%d" % (where, fields["description"].line), message)
        for message in warnings:
            report.warn("%s:%d" % (where, fields["description"].line), message)

    text_field("license")
    compatibility = text_field("compatibility")
    if compatibility is not None and len(compatibility) > COMPATIBILITY_MAX:
        report.error(where, "compatibility is %d characters; the maximum is %d" % (len(compatibility), COMPATIBILITY_MAX))
    text_field("allowed-tools")
    metadata = fields.get("metadata")
    if metadata is not None and metadata.kind != "null":
        if metadata.kind != "map":
            report.error("%s:%d" % (where, metadata.line), "metadata must be a map of string keys to string values")
        else:
            for key, field in metadata.value.items():
                if field.kind != "str":
                    report.error(
                        "%s:%d" % (where, field.line),
                        "metadata.%s is a %s; the standard requires string values, so wrap it in quotes" % (key, field.kind),
                    )

    body_text = "\n".join(body_lines)
    if not body_text.strip():
        report.error(where, "body is empty; add the instructions the agent must follow")
    if len(body_lines) > BODY_MAX_LINES:
        report.warn(where, "body is %d lines; keep it under %d and move detail to references/" % (len(body_lines), BODY_MAX_LINES))
    for offset, line in enumerate(body_lines):
        lineno = body_start + offset
        for pattern, label in AGENT_SPECIFIC:
            if pattern.search(line):
                report.warn("%s:%d" % (where, lineno), "contains %s; keep SKILL.md portable across agents" % label)
        if WINDOWS_PATH_RE.search(line):
            report.warn("%s:%d" % (where, lineno), "Windows-style path; use forward slashes, which work everywhere")

    root = skill_dir.resolve()
    for lineno, target in local_links(text.split("\n")):
        resolved = (skill_dir / target).resolve()
        if root != resolved and root not in resolved.parents:
            report.error("%s:%d" % (where, lineno), "link %r leaves the skill folder; bundle the file inside the skill" % target)
        elif not resolved.exists():
            report.error("%s:%d" % (where, lineno), "link target %r does not exist" % target)

    for path in sorted(skill_dir.rglob("*.md")):
        rel = path.relative_to(skill_dir).as_posix()
        if rel == "SKILL.md" or rel.split("/")[0] in ("assets", "evals"):
            continue
        lines = read_text(path).split("\n")
        if len(lines) > REFERENCE_TOC_LINES and not any(TOC_HEADING_RE.match(l) for l in lines[:40]):
            report.warn(prefix + rel, "over %d lines with no 'Contents' section near the top" % REFERENCE_TOC_LINES)
        for lineno, target in local_links(lines):
            if target.lower().endswith(".md"):
                report.warn("%s%s:%d" % (prefix, rel, lineno), "links to %r; keep references one level deep from SKILL.md" % target)

    for sub in ("references", "scripts", "assets"):
        base = skill_dir / sub
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.name.startswith(".") or "__pycache__" in path.parts:
                continue
            parts = path.relative_to(skill_dir).as_posix().split("/")
            mentions = ["/".join(parts[:size]) for size in range(len(parts), 1, -1)]
            if not any(mention in text for mention in mentions):
                report.warn(prefix + "/".join(parts), "never mentioned in SKILL.md, so agents will not find it")

    if name is not None:
        check_evals(skill_dir, name, prefix, report)
    if scan_placeholders:
        check_placeholders(skill_dir, report)
    return name


# --- Repository validation --------------------------------------------------

def validate_repo(repo, report):
    for filename in REQUIRED_REPO_FILES:
        path = repo / filename
        if not path.is_file() or not read_text(path).strip():
            report.error(filename, "missing or empty; every skill repository ships this file")
    license_path = repo / "LICENSE"
    if license_path.is_file() and "MIT License" not in read_text(license_path):
        report.error("LICENSE", "is not the MIT License, which is this project's standard")

    skills_dir = repo / "skills"
    skill_dirs = sorted(p for p in skills_dir.iterdir() if p.is_dir() and not p.name.startswith("."))
    names = []
    for skill_dir in skill_dirs:
        if skill_dir.name.endswith("-workspace"):
            continue
        if not (skill_dir / "SKILL.md").is_file():
            report.warn("skills/%s" % skill_dir.name, "has no SKILL.md, so it is not a skill")
            continue
        name = validate_skill(skill_dir, report, prefix="skills/%s/" % skill_dir.name, scan_placeholders=False)
        names.append(name or skill_dir.name)
    if not names:
        report.error("skills/", "contains no skill; expected skills/<name>/SKILL.md")
    check_placeholders(repo, report)

    for link_dir in DEV_LINK_DIRS:
        for name in names:
            link = repo / link_dir / name
            if link.is_symlink() and link.resolve() != (skills_dir / name).resolve():
                report.error("%s/%s" % (link_dir, name), "symlink does not point to skills/%s" % name)


def default_target():
    here = Path(__file__).resolve().parent
    if here.name == "scripts" and (here.parent / "skills").is_dir():
        return here.parent
    return Path.cwd()


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate an Agent Skill directory or a skill repository.",
        epilog="Exit status: 0 = no errors, 1 = problems found, 2 = PATH is not a skill or skill repository.",
    )
    parser.add_argument("path", nargs="?", help="skill directory or skill repository (default: see module docstring)")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args(argv)

    target = Path(args.path).expanduser() if args.path else default_target()
    if not target.is_dir():
        print("error: %s is not a directory" % target, file=sys.stderr)
        return 2
    report = Report()
    if (target / "SKILL.md").is_file():
        kind = "skill"
        validate_skill(target, report)
    elif (target / "skills").is_dir():
        kind = "repository"
        validate_repo(target, report)
    else:
        print(
            "error: %s is neither a skill (no SKILL.md) nor a skill repository (no skills/ directory)" % target,
            file=sys.stderr,
        )
        return 2

    print("Validating %s: %s" % (kind, target.resolve()))
    for level, where, message in report.items:
        print("  %-5s %s: %s" % (level, where, message))
    errors, warnings = report.count("ERROR"), report.count("WARN")
    print("Result: %d error(s), %d warning(s)" % (errors, warnings))
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
