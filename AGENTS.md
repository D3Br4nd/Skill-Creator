# Skill-Creator

This repository is a skill factory. It holds one skill, `skills/skill-repo-creator/`, which turns a repetitive task into a new Agent Skill packaged as its own standalone git repository.

## When the user asks for a new skill

The user gives the repetitive task to automate and may name a target platform. A task-only brief uses the portable Agent Skills format.

Read `skills/skill-repo-creator/SKILL.md` and follow it from start to finish. If your agent already lists a skill named `skill-repo-creator`, load that skill instead; it is the same file.

## Defaults for this workspace

- **Destination.** Create each new skill repository in the parent directory of this repository, as `../<skill-name>/`. Never create it inside this repository.
- **Language.** Match the user's language for human-facing output: questions, the generated `README.md` (unless the user prefers English) and the five-part report, defaulting to English. Keep the base repository and all agent-facing files (`SKILL.md`, `references/`, `AGENTS.md`, scripts) in English unless the user explicitly asks otherwise, and include trigger phrases in the user's language in the `description` when they write in another language.
- **License.** MIT. The copyright holder is the git user name unless the user names another.
- **Git.** Run `git init` and make one local commit per new repository. Do not push, create a remote repository or install a skill into the user's agents unless asked.

## Maintaining this repository

- `sources/links-best-practices.md` is the list of official sources. The rules distilled from them live in `skills/skill-repo-creator/references/`.
- When an official page changes, update the matching reference file and the verification date at the top of `references/platforms.md`. Record only what you read on the vendor's page, and label the rest as unverified.
- `skills/skill-repo-creator/assets/repo-template/` holds the English base files of every generated repository. Template files end in `.tmpl`, so no tool mistakes them for a live skill.
- The install table in `README.md.tmpl` repeats the vendor-verified paths from `references/platforms.md`, and the scaffolder prints that file's verification date under it. Change the table and the snapshot together.
- `skills/skill-repo-creator/scripts/validate_skill.py` is copied into every generated repository. Keep it free of dependencies outside the Python standard library.
- Before committing, run `python3 skills/skill-repo-creator/scripts/validate_skill.py .` and fix every ERROR.
- After changing a script or a template, run `python3 -B -m unittest discover -s tests`. The tests scaffold a throwaway repository and check that the validator fails on the untouched scaffold and passes once the TODO markers are replaced. Add a test for every new validator rule.
- This repository follows the same agent-agnostic rules it enforces: `skills/skill-repo-creator/references/portability.md`.
