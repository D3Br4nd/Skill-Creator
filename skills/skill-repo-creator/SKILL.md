---
name: skill-repo-creator
description: >-
  Creates a professional, agent-agnostic Agent Skill packaged as its own git repository
  (SKILL.md, evals, README, MIT LICENSE, .gitignore, AGENTS.md, validator), after checking
  the target platform's official documentation. Use when the user asks to create, build,
  scaffold or package a new skill, or to turn a repetitive task into a reusable skill for
  any AI platform or coding agent, including Italian requests such as "crea una skill",
  "nuova skill", "voglio una skill per" or "automatizza questo compito".
license: MIT
compatibility: Requires Python 3.8+ and git. Web access is needed to verify official platform documentation.
metadata:
  author: "Max Brandini"
  version: "0.1.0"
---

# Skill Repo Creator

Turn one repetitive task into a professional, reusable skill, delivered as a standalone git repository that any agent supporting the Agent Skills open standard can install.

Paths in this file are relative to the folder that contains it. Call the scripts by their full path, because the working directory is usually the user's project.

## Inputs

Two inputs are required:

1. **Platform**: the AI platform or agent the user mainly works with.
2. **Repetitive task**: the activity to automate.

If one is missing, ask for it (for both in a single message when both are missing) and wait. Derive everything else yourself: name, triggers, output format, edge cases. Ask a further question only when a wrong guess would make the skill useless.

## Operating rules

- **Official sources first.** Platform capabilities change. State only what you confirmed in the vendor's documentation during this run, and say plainly when a capability does not exist or cannot be confirmed. Never invent a feature.
- **Portable by default.** Whatever the platform, write the skill to the open standard and to [references/portability.md](references/portability.md), so it runs unchanged in other agents.
- **One skill, one job.** Unrelated tasks become separate skills in separate repositories.
- **Lean.** Write instructions only, unless an operation is fragile or must be deterministic; then bundle a script. Add only what the agent does not already know.
- **Few exchanges.** The finished skill must do its task with the fewest possible questions to its user, and return the same output structure every time.
- **Languages.** Use the user's language for everything the user reads: questions, the README and the final report. Write agent-facing files (`SKILL.md`, references, `AGENTS.md`) in English unless the user asks otherwise, and put trigger phrases in the user's language in the description.
- **Stay local.** Create and commit the repository locally. Push, create a remote or install the skill into the user's agents only when asked.

## Workflow

Copy this checklist into your working notes and tick each step:

```text
- [ ] 1. Research the platform's official docs
- [ ] 2. Design the skill and draft three evals
- [ ] 3. Scaffold the repository
- [ ] 4. Write the content
- [ ] 5. Validate until 0 errors
- [ ] 6. Test
- [ ] 7. Commit locally
- [ ] 8. Deliver the five-part report
```

### 1. Research the platform's official docs

1. Read [references/platforms.md](references/platforms.md): the last verified snapshot of each platform, with the official URLs.
2. Fetch the platform's current official documentation and confirm four things: whether it loads Agent Skills folders, where skills are installed, which frontmatter fields and limits apply, and whether it supports attached files, tools, script execution and external actions such as connectors.
3. Keep every URL you relied on, with the recommendation it supports. They go in the README and in part 5 of the report.

If the live documentation contradicts the snapshot, follow the live documentation and tell the user what changed. If you have no web access, use the snapshot and label each platform claim "not re-verified".

**Platform without Agent Skills support.** Keep `skills/<name>/SKILL.md` as the source of truth. Add `adapters/<platform>.md` with the same instructions in the platform's own format (for example custom instructions) and put its install steps in the README.

### 2. Design the skill and draft three evals

Read [references/authoring-rules.md](references/authoring-rules.md) before designing. It holds the rules for names, descriptions, structure, scripts and evals. Decide:

- **Name**: short, specific and tied to the task, in lowercase with hyphens.
- **Description**: third person, what the skill does, then "Use when ..." with the words the user would really type.
- **Freedom**: exact commands for fragile steps, criteria for judgment calls.
- **Files**: what stays in `SKILL.md` and what moves to `references/`, `scripts/` or `assets/`.

Draft three evals now, before writing instructions: a typical request, the same task worded differently, and an edge case. They define what "working" means.

### 3. Scaffold the repository

```bash
python3 scripts/scaffold_skill_repo.py --name <skill-name> --description "<description>" --dest <parent-directory>
```

- `--dest`: the directory the user named; otherwise the one set in the project's instruction file; otherwise the current directory. A skill repository is standalone, so the script refuses a destination inside a git repository. In that case use a folder outside it, usually the parent of the current repository.
- `--lang it`: README in Italian (the default is `en`).
- `--author "<name>"`: copyright holder, when it differs from the git user name.

The script fills the templates in `assets/repo-template/`, creates `<parent-directory>/<skill-name>/`, links the skill into the new repository's `.claude/skills/` and `.agents/skills/` folders so it can be tested in place, and runs `git init`. It refuses to overwrite a non-empty folder. Do not read the templates; read the generated files instead. Run the script with `--help` to see the other options.

### 4. Write the content

Replace every double-bracket TODO marker in the new repository:

- `skills/<name>/SKILL.md`: keep every section of the template. Together they are the standard structure of the skills produced here.
- `skills/<name>/evals/evals.json` and `eval_queries.json`: the three evals from step 2, and at least eight trigger queries, half of them near misses that must not trigger the skill.
- `README.md`: purpose, notes for the primary platform, three test prompts, requirements and the official sources. The install table comes from the snapshot and states its date. Check the primary platform's row against the live docs and correct it if they differ; leave the other rows as they are.

Add `references/`, `scripts/` or `assets/` inside the skill folder only when the design calls for them. Link each new file from `SKILL.md` and add it to the layout in `README.md` and `AGENTS.md`. Put input files for evals in `evals/files/`.

### 5. Validate until 0 errors

```bash
python3 <new-repo>/scripts/validate_skill.py
```

Fix every ERROR and run it again, until it reports 0 errors. For each WARN, fix it or explain in the report why it is acceptable.

### 6. Test

Run the three README test prompts with the skill loaded, each in a fresh context (a subagent or a new session), and compare each result with its `expected_output`. If a result falls short, fix the skill and validate again. If you cannot run the prompts, report the tests as "not executed". Never report a test you did not run as passed.

### 7. Commit locally

```bash
git -C <new-repo> add -A
git -C <new-repo> commit -m "Initial commit: <skill-name> skill"
```

### 8. Deliver the five-part report

Use the format below.

## Output format

Reply in the user's language with exactly these five parts. In Italian the headings are `PARTE 1: ANALISI TECNICA`, `PARTE 2: SKILL COMPLETA`, `PARTE 3: INSTALLAZIONE E IMPOSTAZIONI`, `PARTE 4: TEST PRATICI` and `PARTE 5: FONTI UFFICIALI`.

```markdown
## PART 1: TECHNICAL ANALYSIS
[How the task is automated on the chosen platform according to its official docs, and what the platform cannot do.]

## PART 2: COMPLETE SKILL
[Repository path, file tree, the frontmatter verbatim and the section outline of SKILL.md. Paste the whole SKILL.md only for a chat-only platform or when the user asks.]

## PART 3: INSTALLATION AND SETTINGS
[Exact steps for the primary platform, then the portable alternatives. Extra files or settings, if any.]

## PART 4: PRACTICAL TESTS
[Three prompts to try, each with its expected result, and whether you executed them.]

## PART 5: OFFICIAL SOURCES
[Each URL consulted, with the recommendation the skill relies on. Anything left unverified.]
```

## Quality checks

Before delivering, confirm each point:

- The validator reports 0 errors, and every remaining warning is explained.
- Every claim about the primary platform, in the README and in the report, has an official URL or is marked as unverified.
- The description says what the skill does and when to use it, with trigger phrases in the user's language.
- `SKILL.md` contains no agent-specific syntax, tool names or install paths.
- The repository holds `README.md`, `LICENSE` (MIT), `.gitignore`, `AGENTS.md`, `CHANGELOG.md` and at least three evals.
- The work is committed locally and nothing was pushed.

## Edge cases

- **The platform or the task is missing.** Ask for it and do not scaffold until the answer arrives.
- **The task covers several unrelated jobs.** Propose one skill per job and ask which to build first.
- **A folder with that name already exists at the destination.** Stop and ask whether to choose a new name or update the existing repository. Never overwrite.
- **The official docs cannot be reached.** Continue from the snapshot, mark platform claims "not re-verified" and say so in parts 1 and 5.
- **The user wants to change an existing skill repository.** Edit it in place: follow its `AGENTS.md`, run its validator and add a changelog entry. Do not scaffold again.

## Examples

**Request:** "Piattaforma: Claude Code. Compito: ogni lunedì trasformo l'export CSV delle vendite in un report con i totali per categoria."

**Result:** a repository `weekly-sales-report/` in the destination directory, scaffolded with `--lang it`. Its `SKILL.md` description ends with Italian trigger phrases. It has three evals, a README in Italian with the Claude Code install steps and links to the official docs, a validator run with 0 errors and one local commit. The reply is the five-part report in Italian.

**Request:** "make me a skill that renames client photos"

**Result:** one question asking which platform the user works with, since the task is already clear. No files are created until the answer arrives.
