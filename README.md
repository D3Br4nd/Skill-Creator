<div align="center">

# Skill-Creator

**Turn a task you repeat into an Agent Skill your team can inspect, test and reuse.**

[![Creator version](https://img.shields.io/badge/version-0.3.0-d95432?style=flat-square)](skills/skill-repo-creator/SKILL.md)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-open%20standard-7048a8?style=flat-square)](https://agentskills.io/specification)
[![Python](https://img.shields.io/badge/Python-3.8%2B-3572a5?style=flat-square)](#requirements)
[![License](https://img.shields.io/badge/license-MIT-2ea44f?style=flat-square)](LICENSE)

[Quick start](#quick-start) · [Examples](#examples) · [Field test](#field-test) · [Inside the repository](#inside-the-generated-repository) · [Installation](#installation) · [Development](#development)

</div>

---

Give the factory a recurring task. It creates a sibling git repository with the skill, example requests, a validator and one local commit. Name an agent if you want its installation steps checked. A task-only brief produces a portable skill folder.

## Quick start

Open this checkout with your agent. If it needs an explicit entry point, point it to the [creator skill](skills/skill-repo-creator/SKILL.md). Then give it a task with a recognizable result.

> “Create a reusable skill for our Monday report. We export a CSV with category, product and revenue. Produce a Markdown table of revenue by category and the five highest-grossing products.”

A brief like this could produce `../weekly-sales-report/`. Open its README for worked prompts and installation steps. The folder your team installs is `skills/weekly-sales-report/` inside that new repository.

## Examples

| Your brief | What to expect |
|---|---|
| “Turn our transcript-to-decisions checklist into a reusable skill. Leave unknown owners blank.” | A portable workflow with an evaluation that checks what happens when nobody takes ownership. |
| “Crea una skill per OpenCode che trasformi le note di rilascio in un aggiornamento per i clienti.” | An Italian README and delivery report, Italian trigger phrases, and installation guidance for OpenCode. |
| “Our review runs offline and uses a local Python script. Package it as a skill.” | The script travels with the skill. Its instructions name the required runtime so a teammate can check the target environment. |

## Field test

The factory built a skill to reconcile invoices with payments. Each agent received the same synthetic records and accounting rules in fresh sessions. Five checks per case covered invoice balances, payment allocations, unapplied cash, duplicate and conflicting IDs, and totals by currency.

| Agent | Cases | Without the skill | With the skill |
|---|---|---:|---:|
| Codex | Three cases covering partial payments, conflicting IDs and ambiguous references | 15/15 | 15/15 |
| OpenCode with GPT-4.1 mini | One case with duplicate and conflicting payments | 1/5 | 5/5 |

OpenCode initially held an entire €100 payment after spotting a duplicate. With the skill, it counted the payment once, applied €90 to the invoice and left €10 unapplied. Both replies wrapped the requested JSON in Markdown. After a delivery-instruction edit, a fresh assisted session returned directly parseable JSON and retained all five accounting points on the same case.

The evaluators loaded the skill explicitly. Automatic selection when both `skill-creator` and `skill-repo-creator` are available is still untested. [Evaluation method](skills/skill-repo-creator/references/behavioral-evaluation.md)

## Inside the generated repository

```text
weekly-sales-report/
├── skills/weekly-sales-report/     ← copy this folder to install the skill
│   ├── SKILL.md                     instructions and trigger description
│   └── evals/                       behavior cases and trigger queries
├── scripts/validate_skill.py        local structural checks
├── README.md                        use, installation, requirements and sources
├── AGENTS.md                        maintenance instructions
├── CHANGELOG.md
├── .gitignore
└── LICENSE                          MIT
```

| Stage | What the factory checks |
|---|---|
| Design | Defines the expected result for a typical request, a paraphrase and an edge case before writing the workflow. |
| Packaging | Keeps task resources inside the installable folder. Host setup belongs in the README or a documented adapter. |
| Validation | Checks frontmatter, local links, evaluation files and unfinished template markers. |
| Practical tests | Runs the same prompts with and without the skill and scores both outputs against criteria set beforehand. The report shows gains, ties and regressions, plus a second-host check when available. |

The five-part handoff covers technical choices, the complete skill, installation, practical tests and sources. Questions, generated READMEs and handoffs follow the user's language. Agent-facing instructions default to English.

## Installation

To use **the creator** from another project, copy `skills/skill-repo-creator/` into your agent's documented skill directory. To install **a skill you generated**, copy its corresponding folder from the new repository. The [platform reference](skills/skill-repo-creator/references/platforms.md) lists project and user locations, verification dates and sources.

From a local checkout, the community CLI can also install the creator into a project:

```sh
npx skills add .
```

The CLI has its own Node.js requirement. You can use the factory directly from this checkout with the tools below. [CLI documentation](https://github.com/vercel-labs/skills)

### Requirements

The factory uses Python 3.8+ with the standard library, Git and a writable destination. Set your Git author identity for the local commit. Live documentation checks use web access. Offline runs use the bundled snapshot and label its claims accordingly. Each generated skill declares its own runtime requirements.

## Development

Run these from the factory root:

```sh
python3 skills/skill-repo-creator/scripts/validate_skill.py . --strict
python3 -B -m unittest discover -s tests
```

To scaffold an unfinished repository manually:

```sh
python3 skills/skill-repo-creator/scripts/scaffold_skill_repo.py \
  --name weekly-sales-report \
  --description "Summarizes sales by category. Use when preparing the weekly revenue report." \
  --dest ..
```

Fill the template prompts and run `python3 ../weekly-sales-report/scripts/validate_skill.py`. Add `--dev-links` to the scaffold command if you want in-repository discovery links and the Claude Code instruction shim for local testing.

| For maintainers | Where to look |
|---|---|
| Which decisions shape a generated skill? | [Authoring rules](skills/skill-repo-creator/references/authoring-rules.md) · [Portability rules](skills/skill-repo-creator/references/portability.md) · [Behavioral evaluation](skills/skill-repo-creator/references/behavioral-evaluation.md) |
| What does the scaffolder copy? | [Repository templates](skills/skill-repo-creator/assets/repo-template/) |
| Where do platform claims come from? | [Platform snapshot](skills/skill-repo-creator/references/platforms.md) · [Source index](sources/links-best-practices.md) |

## License

[MIT](LICENSE) © 2026 Max Brandini
