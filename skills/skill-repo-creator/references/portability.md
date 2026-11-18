# Portability rules

The installable unit is the folder containing `SKILL.md`. Keep its workflow and resources usable after copying that folder into a different host. Runtime, permissions and discovery conventions vary by host. See `platforms.md` for the evidence behind individual host restrictions.

## Rules

1. **Standard frontmatter only.** Top-level keys are limited to `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools`. Claude's upload surfaces answer any other key with "Unexpected key(s) in SKILL.md frontmatter".
2. **No agent extensions at the top level.** These are valid in one agent and non-portable everywhere else: `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `disallowed-tools`, `model`, `effort`, `context`, `agent`, `background`, `hooks`, `paths`, `shell`.
3. **String metadata.** The standard defines `metadata` as string keys with string values, so quote every value: `version: "1.0"`.
4. **A name that is safe everywhere.** Follow the standard, avoid `anthropic` and `claude`, and avoid the names of skills that agents bundle, such as `skill-creator` and `skill-installer`. Codex does not merge two skills with the same name; it lists both.
5. **A description that survives truncation.** The limit is 1024 characters, but agents shorten the listing when many skills are installed. Put the key use case and the trigger words in the first sentence.
6. **A neutral body.** Address "the agent". Describe the action ("read the file", "run the script") instead of naming one agent's tool. Do not use argument placeholders, substitution variables, inline shell injection or slash-command syntax.
7. **No invocation syntax in the skill.** Explicit invocation differs by agent: a leading `/` in Claude Code and Antigravity, `$` or `/skills` in Codex, `@` in ChatGPT and OpenCode. Put it in the README, per agent.
8. **Relative paths.** Resolve bundled resource paths against the folder that holds `SKILL.md`, even when the working directory differs. Never write an install location into the skill.
9. **Standard folders.** Use `scripts/`, `references/` and `assets/`. Agents open whatever `SKILL.md` links, so the standard names work even where the vendor's examples use other names.
10. **Declared requirements.** Runtimes differ: the Claude API runs skills with no network and no package installation, claude.ai depends on admin settings, and local agents have the user's full environment. State runtime, packages and network needs in the skill body. The standard also defines an optional `compatibility` field. If a receiving validator rejects that field, keep the requirements in the body.
11. **Scripts run through their interpreter.** Write `python3 scripts/x.py`, not `./scripts/x.py`. Copying a folder or uploading a zip can drop the executable bit.
12. **Human documentation outside the skill folder.** README, changelog and license stay at the repository root. The skill folder holds only what the agent needs.

## Where agent-specific needs go

| Need | Portable choice |
|---|---|
| Limit automatic invocation | Tighten the description first. If a switch is still needed, it is agent-specific (a frontmatter key in Claude Code, a metadata entry in OpenCode, `agents/openai.yaml` in Codex): document it in the README instead of adding it to the skill. |
| Interface metadata such as icon and display name | A sidecar file that other agents ignore, for example `agents/openai.yaml` for Codex. |
| Pre-approved tools | `allowed-tools` is in the standard but experimental, and its values are agent-specific tool names. Use it only when the user asks. |
| MCP tools | Declare the required service and operation in the skill requirements. Document host-specific tool identifiers in the integration instructions. |
| A platform without Agent Skills support | Keep `SKILL.md` as the source. Add an adapter at the repository root when the vendor documents a usable customization format. |

## Development links

The default scaffold contains the portable skill and repository maintenance files. For in-repository discovery, `--dev-links` also writes a Claude Code instruction shim and symlinks under `.claude/skills/` and `.agents/skills/`. A host that supports neither link can load a copy from its documented install directory.
