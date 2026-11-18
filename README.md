# Skill-Creator

A skill factory repository for AI agents. Provide two inputs — the target platform and the repetitive task — and get a complete, standalone git repository containing a portable skill ready to install.

Every skill follows the [Agent Skills open standard](https://agentskills.io) and the official guidelines of Anthropic, OpenAI, Google Antigravity, and OpenCode, so it works unchanged across agents.

## Languages

The repository base and all agent-facing files (`SKILL.md`, `references/`, `AGENTS.md`, scripts, templates) stay in English so generated skills remain portable and consistent. You can prompt the agent in **any language** (English, Italian, Spanish, French, German, Japanese, and more): questions, the generated `README.md`, and the final delivery report match your language, and natural trigger phrases in your language are added to the skill's `description` alongside the English wording.

## How to use

Clone and open this folder with your agent (Claude Code, Codex, OpenCode, Antigravity) and send your request. For example:

> Platform: Claude Code. Task: every Monday I turn the weekly sales CSV export into a markdown report with category totals.

The agent follows the workflow in `skills/skill-repo-creator/SKILL.md`:

1. Checks the target platform's live official documentation.
2. Designs the skill and drafts three evaluation cases.
3. Scaffolds a standalone git repository beside this one: `../<skill-name>/`.
4. Writes the content and runs the validator until 0 errors remain.
5. Tests the skill, creates one local commit, and delivers a five-part report: technical analysis, complete skill, installation and settings, practical tests, and official sources.

The agent never pushes, creates a remote repository, or installs anything into your agents unless you ask.

If you add a `.claude/skills` directory during an active Claude Code session, run `/reload-skills` so the new skill appears (or `/skills reload` in the Antigravity CLI).

## What each generated repository contains

```text
<skill-name>/
├── skills/<skill-name>/
│   ├── SKILL.md                   the skill: instructions and metadata
│   └── evals/                     test cases and trigger queries
├── scripts/validate_skill.py      validator, run before every commit
├── README.md                      purpose, install steps, test prompts, sources
├── AGENTS.md                      rules for keeping the skill agent-agnostic
├── CLAUDE.md                      imports AGENTS.md for Claude Code
├── CHANGELOG.md
├── LICENSE                        MIT
├── .gitignore
├── .claude/skills/<skill-name>    symlink to the skill for in-repo testing
└── .agents/skills/<skill-name>    symlink to the skill for in-repo testing
```

Agents install only `skills/<skill-name>/`. Everything outside it is documentation and tooling.

## Rules every skill follows

- **Portable frontmatter.** Only the six fields defined by the open standard: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`.
- **Name.** Lowercase letters, digits, and single hyphens, at most 64 characters, matching the folder name, without the reserved words `anthropic` or `claude`.
- **Description.** Third person, stating what the skill does and when to use it, at most 1024 characters, no angle brackets.
- **Body.** Under 500 lines, with no syntax, tool names, or install paths tied to a single agent.
- **Standard structure.** Goal, inputs, operating rules, workflow, output format, quality checks, edge cases, examples.
- **Evals.** At least three test cases and a set of trigger queries mixing positive matches and near misses.
- **License.** MIT.

The validator enforces these rules and blocks delivery while errors remain. Full details live in `skills/skill-repo-creator/references/`:

| File | Contents |
|---|---|
| `authoring-rules.md` | How to write names, descriptions, bodies, scripts, and evals, with the source of each rule |
| `portability.md` | Rules for keeping skills independent of any single agent |
| `platforms.md` | Where each platform installs skills and which limits apply, with verification dates |

## Repository structure

```text
Skill-Creator/
├── skills/skill-repo-creator/
│   ├── SKILL.md                   workflow the agent follows
│   ├── references/                authoring, portability, and platform references
│   ├── scripts/                   scaffold_skill_repo.py and validate_skill.py
│   ├── assets/repo-template/      English base templates for generated repositories
│   └── evals/                     test cases and trigger queries for this skill
├── tests/                         automated unit tests for both scripts
├── sources/                       list of official vendor documentation links
├── AGENTS.md                      instructions for agents working in this repo
├── CLAUDE.md                      imports AGENTS.md for Claude Code
├── .claude/skills/skill-repo-creator   symlink to the skill for in-repo use
└── .agents/skills/skill-repo-creator   symlink to the skill for in-repo use
```

## Useful commands

```bash
# Validate this repository
python3 skills/skill-repo-creator/scripts/validate_skill.py .

# Run the script test suite
python3 -B -m unittest discover -s tests

# Manually scaffold a new skill repository
python3 skills/skill-repo-creator/scripts/scaffold_skill_repo.py \
  --name skill-name --description "What it does. Use when ..." --dest ..

# Validate a generated repository
python3 ../skill-name/scripts/validate_skill.py
```

## Using the skill outside this folder

To create skills from any project, copy `skills/skill-repo-creator` into your agent's global skills folder. For Claude Code:

```bash
cp -R skills/skill-repo-creator ~/.claude/skills/
```

Install paths for other agents (OpenAI Codex, OpenCode, Google Antigravity, and more) are listed in `skills/skill-repo-creator/references/platforms.md`. You can also install across multiple agents at once with the community [`skills` CLI](https://github.com/vercel-labs/skills) (`npx skills add . -g` from a local clone, or `npx skills add <owner>/<repo> -g` from GitHub).

## Sources

The starting list of official documentation links is in `sources/links-best-practices.md`. Verification status as of November 18, 2026:

| Source | Status |
|---|---|
| [OpenCode: skills](https://opencode.ai/docs/skills/) | Verified |
| [Google Antigravity: skills](https://antigravity.google/docs/skills/) | Verified |
| [Anthropic: skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Verified |
| [OpenAI Academy: skills](https://openai.com/academy/skills/) | Unverified: returned HTTP 403 to automated requests |

OpenAI rules were verified against the official [Build skills](https://learn.chatgpt.com/docs/build-skills) documentation. Additional verified sources include the [Agent Skills specification](https://agentskills.io/specification), its guides on [evaluating skills](https://agentskills.io/skill-creation/evaluating-skills) and [optimizing descriptions](https://agentskills.io/skill-creation/optimizing-descriptions), and the [Claude Code skills](https://code.claude.com/docs/en/skills) documentation.

To incorporate the OpenAI Academy page, save a copy from a browser into `sources/` and ask the agent to update the references.

## License

[MIT](LICENSE) © 2026 Max Brandini
