# Skill authoring rules

Rules distilled from the official sources listed at the end. Each rule carries the tag of the source it comes from:

- **[S]** Agent Skills specification (agentskills.io)
- **[E]** Agent Skills evaluation and description guides (agentskills.io)
- **[A]** Anthropic skill authoring best practices
- **[C]** Claude Code skills documentation
- **[O]** OpenAI "Build skills" documentation
- **[G]** Google Antigravity skills documentation

## Contents

- Anatomy: the standard sections
- Frontmatter
- Description
- Body
- Progressive disclosure
- Workflows, templates and examples
- Scripts
- Evals
- Sources

## Anatomy: the standard sections

Every skill produced here has these eleven elements. The template already contains a place for each one.

| Element | Where it lives |
|---|---|
| Name | frontmatter `name` |
| Description | frontmatter `description`, opening sentence |
| Triggers | frontmatter `description`, "Use when ..." clause |
| Main goal | first paragraph of the body |
| Inputs | `## Inputs` |
| Operating instructions | `## Operating rules` |
| Procedure | `## Workflow` |
| Output format | `## Output format` |
| Quality rules | `## Quality checks` |
| Exception handling | `## Edge cases` |
| Practical examples | `## Examples`, the README test prompts and `evals/` |

Triggers belong in the description, not in the body: agents read the body only after they have decided to load the skill. [S][A]

## Frontmatter

- `name` and `description` are required. [S][A][O]
- The only other portable fields are `license`, `compatibility` (at most 500 characters), `metadata` (a map of string keys to string values) and `allowed-tools` (a space-separated string, experimental). [S]
- Add nothing else at the top level. Claude's upload surfaces reject any other key with a hard error. [C]
- `name`: 1 to 64 characters, lowercase letters, digits and single hyphens, no leading or trailing hyphen, equal to the folder name. [S] It must not contain `anthropic` or `claude`. [A]
- Prefer a gerund or a noun phrase that names the task: `processing-pdfs`, `pdf-processing`. Avoid vague names such as `helper`, `utils`, `tools`, `data`. [A]
- Quote any value that contains a colon followed by a space, or a space followed by `#`. Quote numbers and booleans under `metadata`. When the YAML does not parse, at least one agent loads the skill with empty metadata, so the skill silently stops triggering. [C]
- Include `compatibility` only when the skill has real environment requirements. [S]

## Description

Agents load only the name and the description at startup, so the description alone decides whether the skill is used. [S][A][O][G]

- State what the skill does, then when to use it: "Extracts ... Use when ...". [S][A]
- Write in third person. "Processes Excel files", not "I can help you" and not "You can use this". [A][G]
- Put the key use case and the trigger words first. Agents shorten or drop descriptions when many skills are installed. [O][C]
- Describe the user's intent, not the implementation. Name the contexts where the skill applies, including requests that do not mention the domain by name. [E]
- When near misses exist, say what the skill does not cover. [O][E]
- Use the words the user would type, in the user's language.
- Stay within 1024 characters, and use square brackets instead of angle brackets. [S][A][C]

## Body

- Assume the agent is already capable. Add only what it does not know, and make each paragraph justify its token cost. [A]
- Keep the body under 500 lines, about 5000 tokens. [S][A]
- Match the freedom to the task. Give text guidance when many approaches work, a parameterised pattern when one is preferred, and an exact command when the operation is fragile or the sequence matters. [A]
- Write imperative steps with explicit inputs and outputs. [O]
- Explain why a rule exists. Reasons work better than "ALWAYS" and "NEVER". [E]
- Give one default instead of a menu of options, with an escape hatch only where it is needed. [A]
- Use one term per concept throughout. [A]
- Leave out anything that will go stale. Put superseded methods under an "Old patterns" heading. [A]
- Put the most important instructions near the top. After a long conversation is compacted, an agent may keep only the start of the skill. [C]
- For a complex skill, add a decision tree that selects the right approach. [G]
- Keep one job per skill. [O][G]

## Progressive disclosure

Agents load a skill in three stages: metadata at startup (about 100 tokens), the `SKILL.md` body when the skill triggers, and bundled files only when the body sends the agent to them. [S][A]

- Move detail into `references/` when the body approaches the limit. [S][A]
- Link every bundled file directly from `SKILL.md`. Agents may read only part of a file reached through a second hop. [S][A]
- For each file, say what it contains and when to read it. [A][C]
- Start any reference file longer than 100 lines with a contents list. [A]
- Name files for their content (`form_validation_rules.md`, not `doc2.md`) and group them by domain. [A]
- Use relative paths with forward slashes. [S][A]

## Workflows, templates and examples

- Break a complex task into numbered steps. For a long one, give a checklist the agent copies and ticks off. [A]
- Add a feedback loop to quality-critical work: run the validator, fix the errors, repeat. [A]
- Give the output format as a template. Say "use this exact structure" when consistency matters, and "sensible default, adapt as needed" when it does not. [A]
- Show input/output pairs when the result depends on style. [A]
- For branching tasks, state the decision first and then one workflow per branch. [A]
- For batch or destructive operations, have the agent write a plan file, validate it with a script, and only then execute. [A]

## Scripts

- Instructions only is the default. Add a script when the behaviour must be deterministic or needs external tooling. [O][A]
- Handle error conditions inside the script instead of leaving them to the agent. [A]
- Justify every constant in a comment. [A]
- Say whether the agent should run the script or read it. Running is the usual case; tell the agent to call `--help` rather than read the source. [A][G]
- Keep scripts self-contained, list their dependencies and never assume a package is installed. [S][A]
- Write specific error messages that say what to fix. [A]
- Refer to MCP tools by fully qualified name, `ServerName:tool_name`. [A]

## Evals

- Write three evals before writing extensive instructions, and measure the baseline without the skill. [A]
- Store them in `evals/evals.json` inside the skill folder: `skill_name` and an `evals` array of `id`, `prompt`, `expected_output`, optional `files` and optional `assertions`. [E]
- Keep the input files of an eval in `evals/files/` and list them in `files` with paths relative to the skill folder, such as `evals/files/sales.csv`. [E]
- Write prompts a real user would type: varied wording, concrete details such as file paths, and at least one edge case. [E]
- Add `assertions` after the first run, once it is clear what a good result looks like. Each must be verifiable: "the output file is valid JSON", not "the output is good". [E]
- Test the description with trigger queries: about twenty, half that should trigger and half near misses that share keywords but need something else. Run each three times and treat a trigger rate above 0.5 as a pass. [E]
- Run every eval in a clean context, with and without the skill. Keep the run outputs in a `<name>-workspace/` folder beside the skill; the repository ignores it. [E]
- Test with each model the skill will be used with. [A]

## Sources

- [S] https://agentskills.io/specification
- [E] https://agentskills.io/skill-creation/evaluating-skills and https://agentskills.io/skill-creation/optimizing-descriptions
- [A] https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- [C] https://code.claude.com/docs/en/skills
- [O] https://learn.chatgpt.com/docs/build-skills
- [G] https://antigravity.google/docs/skills/
