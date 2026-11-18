# Portability rules

A skill produced here must load and behave the same in every agent that supports the Agent Skills open standard. These rules come from comparing the official documentation of Claude Code, claude.ai, OpenAI Codex, OpenCode and Google Antigravity. The URLs are in `platforms.md`, in this folder.

## Rules

1. **Standard frontmatter only.** Top-level keys are limited to `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools`. Claude's upload surfaces answer any other key with "Unexpected key(s) in SKILL.md frontmatter".
2. **No agent extensions at the top level.** These are valid in one agent and non-portable everywhere else: `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `disallowed-tools`, `model`, `effort`, `context`, `agent`, `background`, `hooks`, `paths`, `shell`.
3. **String metadata.** The standard defines `metadata` as string keys with string values, so quote every value: `version: "1.0"`.
4. **A name that is safe everywhere.** Follow the standard, avoid `anthropic` and `claude`, and avoid the names of skills that agents bundle, such as `skill-creator` and `skill-installer`. Codex does not merge two skills with the same name; it lists both.
5. **A description that survives truncation.** The limit is 1024 characters, but agents shorten the listing when many skills are installed. Put the key use case and the trigger words in the first sentence.
6. **A neutral body.** Address "the agent". Describe the action ("read the file", "run the script") instead of naming one agent's tool. Do not use argument placeholders, substitution variables, inline shell injection or slash-command syntax.
7. **No invocation syntax in the skill.** Explicit invocation differs by agent: a leading `/` in Claude Code and Antigravity, `$` or `/skills` in Codex, `@` in ChatGPT and OpenCode. Put it in the README, per agent.
8. **Relative paths.** Agents resolve paths against the folder that holds `SKILL.md`. Never write an install location into the skill.
9. **Standard folders.** Use `scripts/`, `references/` and `assets/`. Agents open whatever `SKILL.md` links, so the standard names work even where the vendor's examples use other names.
10. **Declared requirements.** Runtimes differ: the Claude API runs skills with no network and no package installation, claude.ai depends on admin settings, and local agents have the user's full environment. Prefer the standard library, and state runtime, packages and network needs in `compatibility`.
11. **Scripts run through their interpreter.** Write `python3 scripts/x.py`, not `./scripts/x.py`. Copying a folder or uploading a zip can drop the executable bit.
12. **Human documentation outside the skill folder.** README, changelog and license stay at the repository root. The skill folder holds only what the agent needs.

## Where agent-specific needs go

| Need | Portable choice |
|---|---|
| Limit automatic invocation | Tighten the description first. If a switch is still needed, it is agent-specific (a frontmatter key in Claude Code, a metadata entry in OpenCode, `agents/openai.yaml` in Codex): document it in the README instead of adding it to the skill. |
| Interface metadata such as icon and display name | A sidecar file that other agents ignore, for example `agents/openai.yaml` for Codex. |
| Pre-approved tools | `allowed-tools` is in the standard but experimental, and its values are agent-specific tool names. Use it only when the user asks. |
| MCP tools | Name the server and the tool as `ServerName:tool_name`, and state the dependency in `compatibility`. |
| A platform without Agent Skills support | Keep `SKILL.md` as the source and add `adapters/<platform>.md` at the repository root. |

## Development links

The scaffolder symlinks the skill into `.claude/skills/` and `.agents/skills/` at the repository root, so an agent opened in the repository can load the skill for testing. Claude Code and Codex document that they follow symlinked skill folders. For other agents, and on Windows without symlink support, install the skill by copying the folder.
