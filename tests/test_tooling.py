"""Tests for the scaffolder and the validator.

Run from the repository root:
    python3 -m unittest discover -s tests -v
"""
import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "skill-repo-creator" / "scripts"
SCAFFOLD = SCRIPTS / "scaffold_skill_repo.py"
VALIDATE = SCRIPTS / "validate_skill.py"
DESCRIPTION = "Turns a weekly sales CSV export into a markdown report. Use when the user asks for the weekly sales report."


def run(script, *args):
    return subprocess.run([sys.executable, str(script)] + [str(a) for a in args], capture_output=True, text=True)


def make_skill(parent, name="demo-skill", frontmatter=None, body="# Demo\n\nDo the task.\n", evals=3, directory=None):
    """Write a minimal skill that is valid unless the arguments break it."""
    skill = Path(parent) / (directory or name)
    (skill / "evals").mkdir(parents=True)
    if frontmatter is None:
        frontmatter = "name: %s\ndescription: %s\n" % (name, DESCRIPTION)
    (skill / "SKILL.md").write_text("---\n%s---\n\n%s" % (frontmatter, body), encoding="utf-8")
    cases = [{"id": i, "prompt": "prompt %d" % i, "expected_output": "result"} for i in range(1, evals + 1)]
    (skill / "evals" / "evals.json").write_text(json.dumps({"skill_name": name, "evals": cases}), encoding="utf-8")
    queries = [{"query": "query %d" % i, "should_trigger": i % 2 == 0} for i in range(8)]
    (skill / "evals" / "eval_queries.json").write_text(json.dumps(queries), encoding="utf-8")
    return skill


class TempDirTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()

    def tearDown(self):
        self._tmp.cleanup()

    def assert_error(self, result, fragment):
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        errors = [line for line in result.stdout.splitlines() if line.strip().startswith("ERROR")]
        self.assertTrue(any(fragment in line for line in errors), "no ERROR containing %r in:\n%s" % (fragment, result.stdout))

    def assert_warning(self, result, fragment):
        warnings = [line for line in result.stdout.splitlines() if line.strip().startswith("WARN")]
        self.assertTrue(any(fragment in line for line in warnings), "no WARN containing %r in:\n%s" % (fragment, result.stdout))


class ValidSkillTests(TempDirTest):
    def test_minimal_skill_passes_clean(self):
        result = run(VALIDATE, make_skill(self.tmp), "--strict")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("0 error(s), 0 warning(s)", result.stdout)

    def test_folded_and_quoted_values_are_parsed(self):
        frontmatter = (
            "name: demo-skill\n"
            "description: >-\n"
            "  Turns a weekly sales CSV export into a markdown report: totals per category.\n"
            "  Use when the user asks for the weekly sales report #1.\n"
            "license: MIT\n"
            'compatibility: "Requires Python 3.8+: standard library only"\n'
            "metadata:\n"
            '  author: "Test Author"\n'
            '  version: "1.0"\n'
            "  opencode/autoinvoke: 'false'\n"
            "allowed-tools: Bash(git:*) Read\n"
        )
        result = run(VALIDATE, make_skill(self.tmp, frontmatter=frontmatter), "--strict")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_this_repository_passes_clean(self):
        result = run(VALIDATE, ROOT, "--strict")
        self.assertEqual(result.returncode, 0, result.stdout)


class FrontmatterErrorTests(TempDirTest):
    def check(self, frontmatter, fragment, **kwargs):
        self.assert_error(run(VALIDATE, make_skill(self.tmp, frontmatter=frontmatter, **kwargs)), fragment)

    def test_uppercase_name(self):
        self.check("name: Demo-Skill\ndescription: %s\n" % DESCRIPTION, "lowercase", directory="Demo-Skill")

    def test_consecutive_hyphens(self):
        self.check("name: demo--skill\ndescription: %s\n" % DESCRIPTION, "single hyphens", directory="demo--skill")

    def test_name_differs_from_directory(self):
        self.check("name: other-name\ndescription: %s\n" % DESCRIPTION, "must equal its directory name")

    def test_reserved_word(self):
        result = run(VALIDATE, make_skill(self.tmp, name="claude-tools"))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assert_warning(result, "Claude uploads")

    def test_name_too_long(self):
        name = "a" * 65
        self.check("name: %s\ndescription: %s\n" % (name, DESCRIPTION), "maximum is 64", directory=name)

    def test_non_portable_key(self):
        self.check("name: demo-skill\ndescription: %s\nargument-hint: file\n" % DESCRIPTION, "'argument-hint' is not portable")

    def test_missing_description(self):
        self.check("name: demo-skill\n", "'description' is missing")

    def test_description_too_long(self):
        self.check("name: demo-skill\ndescription: %s\n" % ("Use when needed. " + "x" * 1024), "maximum is 1024")

    def test_xml_tag_is_a_host_warning(self):
        frontmatter = "name: demo-skill\ndescription: Renames <file> items. Use when the user asks to rename.\n"
        result = run(VALIDATE, make_skill(self.tmp, frontmatter=frontmatter))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assert_warning(result, "Claude uploads reject XML tags")

    def test_comparison_is_not_an_xml_tag(self):
        frontmatter = "name: demo-skill\ndescription: Flags values > 20. Use when the user asks for high scores.\n"
        result = run(VALIDATE, make_skill(self.tmp, frontmatter=frontmatter), "--strict")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_unquoted_colon_breaks_yaml(self):
        self.check("name: demo-skill\ndescription: Builds reports. Use when: the user asks for one.\n", "contains ': '")

    def test_compatibility_too_long(self):
        self.check("name: demo-skill\ndescription: %s\ncompatibility: %s\n" % (DESCRIPTION, "y" * 501), "maximum is 500")

    def test_metadata_number_and_boolean(self):
        frontmatter = "name: demo-skill\ndescription: %s\nmetadata:\n  version: 1.0\n  internal: false\n" % DESCRIPTION
        result = run(VALIDATE, make_skill(self.tmp, frontmatter=frontmatter))
        self.assert_error(result, "metadata.version is a number")
        self.assert_error(result, "metadata.internal is a bool")

    def test_allowed_tools_as_list(self):
        self.check("name: demo-skill\ndescription: %s\nallowed-tools:\n  - Read\n  - Grep\n" % DESCRIPTION, "'allowed-tools' must be a string")

    def test_frontmatter_not_closed(self):
        skill = make_skill(self.tmp)
        (skill / "SKILL.md").write_text("---\nname: demo-skill\ndescription: %s\n\n# Body\n" % DESCRIPTION, encoding="utf-8")
        self.assert_error(run(VALIDATE, skill), "never closed")

    def test_frontmatter_not_on_first_line(self):
        skill = make_skill(self.tmp)
        (skill / "SKILL.md").write_text("\n---\nname: demo-skill\ndescription: %s\n---\nBody\n" % DESCRIPTION, encoding="utf-8")
        self.assert_error(run(VALIDATE, skill), "line 1 must be '---'")

    def test_utf8_bom_is_rejected(self):
        skill = make_skill(self.tmp)
        (skill / "SKILL.md").write_text("\ufeff---\nname: demo-skill\ndescription: %s\n---\nBody\n" % DESCRIPTION, encoding="utf-8")
        self.assert_error(run(VALIDATE, skill), "UTF-8 byte-order mark")


class ContentTests(TempDirTest):
    def test_fewer_than_three_evals(self):
        self.assert_error(run(VALIDATE, make_skill(self.tmp, evals=2)), "at least 3 are required")

    def test_missing_evals_file(self):
        skill = make_skill(self.tmp)
        (skill / "evals" / "evals.json").unlink()
        self.assert_error(run(VALIDATE, skill), "evals/evals.json: missing")

    def test_malformed_eval_data_is_reported(self):
        skill = make_skill(self.tmp)
        cases = skill / "evals" / "evals.json"
        data = json.loads(cases.read_text(encoding="utf-8"))
        data["evals"][0]["id"] = []
        cases.write_text(json.dumps(data), encoding="utf-8")
        self.assert_error(run(VALIDATE, skill), "needs a unique 'id'")
        cases.write_text("null", encoding="utf-8")
        self.assert_error(run(VALIDATE, skill), "expected an object")

    def test_evaluation_fixtures_travel_with_the_skill(self):
        skill = make_skill(self.tmp)
        fixture = skill / "evals" / "notes.txt"
        fixture.write_text("meeting notes", encoding="utf-8")
        outside = self.tmp / "other.txt"
        outside.write_text("outside", encoding="utf-8")
        cases = skill / "evals" / "evals.json"
        data = json.loads(cases.read_text(encoding="utf-8"))
        for files, error in [
            (["evals/notes.txt"], None),
            (["../other.txt"], "inside the skill folder"),
            ([str(fixture)], "must be relative"),
            (["evals"], "lists missing file"),
            ("evals/notes.txt", "must be a list"),
            ([None], "non-empty fixture path"),
        ]:
            with self.subTest(files=files):
                data["evals"][0]["files"] = files
                cases.write_text(json.dumps(data), encoding="utf-8")
                result = run(VALIDATE, skill)
                if error:
                    self.assert_error(result, error)
                else:
                    self.assertEqual(result.returncode, 0, result.stdout)

    def test_broken_link(self):
        body = "# Demo\n\nSee [the guide](references/guide.md).\n"
        self.assert_error(run(VALIDATE, make_skill(self.tmp, body=body)), "does not exist")

    def test_link_inside_code_block_is_ignored(self):
        body = "# Demo\n\n```markdown\nSee [the guide](references/guide.md).\n```\n"
        self.assertEqual(run(VALIDATE, make_skill(self.tmp, body=body)).returncode, 0)

    def test_empty_body(self):
        self.assert_error(run(VALIDATE, make_skill(self.tmp, body="")), "body is empty")

    def test_leftover_todo_marker(self):
        self.assert_error(run(VALIDATE, make_skill(self.tmp, body="# Demo\n\n[[TODO: write this]]\n")), "unfilled TODO marker")

    def test_warnings_for_portability_and_structure(self):
        body = (
            "# Demo\n\nRun ${CLAUDE_SKILL_DIR}/scripts/run.py with $ARGUMENTS.\n"
            "Read scripts\\run.py first.\nSee [details](references/details.md).\n"
        )
        skill = make_skill(self.tmp, body=body)
        (skill / "references").mkdir()
        (skill / "references" / "details.md").write_text("# Details\n\nSee [more](more.md).\n" + "line\n" * 120, encoding="utf-8")
        (skill / "references" / "more.md").write_text("# More\n", encoding="utf-8")
        result = run(VALIDATE, skill)
        self.assertEqual(result.returncode, 0, result.stdout)
        for fragment in (
            "substitution variable", "argument placeholder", "Windows-style path",
            "no 'Contents' section", "one level deep", "references/more.md: never mentioned",
        ):
            self.assert_warning(result, fragment)
        self.assertEqual(run(VALIDATE, skill, "--strict").returncode, 1)

    def test_description_style_warnings(self):
        frontmatter = "name: demo-skill\ndescription: I can help you process the weekly sales files quickly.\n"
        result = run(VALIDATE, make_skill(self.tmp, frontmatter=frontmatter))
        self.assert_warning(result, "third person")
        self.assert_warning(result, "no 'Use when ...' clause")

    def test_path_that_is_not_a_skill(self):
        self.assertEqual(run(VALIDATE, self.tmp).returncode, 2)


class ScaffoldTests(TempDirTest):
    def scaffold(self, *extra, name="weekly-sales-report", description=DESCRIPTION, dest=None):
        args = ["--name", name, "--description", description, "--dest", dest or self.tmp, "--author", 'Test "Q" Author']
        return run(SCAFFOLD, *(args + list(extra)))

    def fill_markers(self, repo):
        for path in repo.rglob("*"):
            if path.is_file() and not path.is_symlink() and ".git" not in path.parts and path.suffix in (".md", ".json"):
                text = path.read_text(encoding="utf-8")
                path.write_text(re.sub(r"\[\[TODO[^\]]*\]\]", "Filled in.", text), encoding="utf-8")

    def test_scaffold_fails_validation_until_filled(self):
        result = self.scaffold()
        self.assertEqual(result.returncode, 0, result.stderr)
        repo = self.tmp / "weekly-sales-report"
        for expected in (
            "README.md", "LICENSE", ".gitignore", "AGENTS.md", "CHANGELOG.md",
            "scripts/validate_skill.py", "skills/weekly-sales-report/SKILL.md",
            "skills/weekly-sales-report/evals/evals.json", "skills/weekly-sales-report/evals/eval_queries.json",
        ):
            self.assertTrue((repo / expected).is_file(), expected)
        self.assertTrue((repo / ".git").is_dir())
        readme = (repo / "README.md").read_text(encoding="utf-8")
        self.assertIn("## Install", readme)
        self.assertRegex(readme, r"vendor on \d{4}-\d{2}-\d{2}\.")
        skill_md = (repo / "skills" / "weekly-sales-report" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('author: "Test \\"Q\\" Author"', skill_md)
        self.assertIn('Copyright (c)', (repo / "LICENSE").read_text(encoding="utf-8"))
        self.assertEqual(list(repo.rglob("*.tmpl")), [])
        for optional in ("CLAUDE.md", ".claude", ".agents"):
            self.assertFalse((repo / optional).exists())

        own_validator = repo / "scripts" / "validate_skill.py"
        self.assert_error(run(own_validator), "unfilled TODO marker")
        self.fill_markers(repo)
        result = run(own_validator)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("0 error(s)", result.stdout)

    def test_multilingual_trigger_phrases_pass_strict_validation(self):
        description = (
            'Turns a weekly sales CSV into a markdown report. Use when the user asks for '
            'weekly sales totals, including "report vendite", "posso generare il report", or "informe semanal".'
        )
        frontmatter = "name: demo-skill\ndescription: >-\n  %s\n" % description
        result = run(VALIDATE, make_skill(self.tmp, frontmatter=frontmatter), "--strict")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_portable_factory_copy_can_scaffold_from_another_working_directory(self):
        installed = self.tmp / "skills" / "skill-repo-creator"
        shutil.copytree(SCRIPTS.parent, installed)
        result = run(installed / "scripts" / SCAFFOLD.name, "--name", "claude-notes",
                     "--description", DESCRIPTION, "--dest", self.tmp, "--author", "Test", "--no-dev-links")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Claude uploads", result.stdout)
        repo = self.tmp / "claude-notes"
        self.assertFalse((repo / "CLAUDE.md").exists())
        self.fill_markers(repo)
        standalone = self.tmp / "installed" / "claude-notes"
        shutil.copytree(repo / "skills" / "claude-notes", standalone)
        result = run(repo / "scripts" / "validate_skill.py", standalone)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_repo_level_checks(self):
        self.scaffold("--dev-links")
        repo = self.tmp / "weekly-sales-report"
        self.fill_markers(repo)
        (repo / "LICENSE").write_text("Apache License\n", encoding="utf-8")
        self.assert_error(run(VALIDATE, repo), "is not the MIT License")
        (repo / "LICENSE").unlink()
        self.assert_error(run(VALIDATE, repo), "LICENSE: missing or empty")
        link = repo / ".claude" / "skills" / "weekly-sales-report"
        self.assertTrue((repo / "CLAUDE.md").is_file())
        for parent in (".claude", ".agents"):
            dev_link = repo / parent / "skills" / "weekly-sales-report"
            self.assertTrue(dev_link.is_symlink())
            self.assertEqual(dev_link.resolve(), (repo / "skills" / "weekly-sales-report").resolve())
        link.unlink()
        link.symlink_to(Path("..") / ".." / "scripts", target_is_directory=True)
        self.assert_error(run(VALIDATE, repo), "symlink does not point to skills/weekly-sales-report")

    def test_refuses_invalid_name(self):
        result = self.scaffold(name="Weekly_Report")
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid --name", result.stderr)
        self.assertFalse((self.tmp / "Weekly_Report").exists())

    def test_refuses_invalid_description(self):
        result = self.scaffold(description="  ")
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid --description", result.stderr)

    def test_refuses_existing_folder(self):
        target = self.tmp / "weekly-sales-report"
        target.mkdir()
        (target / "keep.txt").write_text("mine", encoding="utf-8")
        result = self.scaffold()
        self.assertEqual(result.returncode, 1)
        self.assertIn("already exists", result.stderr)
        self.assertEqual((target / "keep.txt").read_text(encoding="utf-8"), "mine")

    def test_refuses_missing_destination(self):
        result = self.scaffold(dest=self.tmp / "nowhere")
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not exist", result.stderr)

    def test_refuses_destination_inside_git_repository(self):
        subprocess.run(["git", "init", "-q", str(self.tmp)], check=True)
        result = self.scaffold()
        self.assertEqual(result.returncode, 1)
        self.assertIn("inside a git repository", result.stderr)
        self.assertEqual(self.scaffold("--allow-nested").returncode, 0)


class CompatibilityTests(unittest.TestCase):
    def test_scripts_parse_as_python_3_8(self):
        for script in (SCAFFOLD, VALIDATE):
            ast.parse(script.read_text(encoding="utf-8"), filename=str(script), feature_version=(3, 8))

    def test_no_bytecode_left_in_skill_folder(self):
        self.assertEqual(list(SCRIPTS.rglob("__pycache__")), [])


if __name__ == "__main__":
    unittest.main()
