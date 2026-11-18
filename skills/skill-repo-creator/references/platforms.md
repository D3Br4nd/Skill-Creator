# Platform snapshot

Verified on 2026-11-18 against the pages linked in each section. Treat it as a starting point: platforms change, so re-read the linked page before relying on a row.

Each section states how its content was verified:

- **vendor**: read on the vendor's own documentation.
- **third-party**: taken only from the documentation of the community `skills` CLI.
- **unverified**: the vendor page could not be read; the content comes from search-result summaries.

## Contents

- Shared standard
- Claude Code
- claude.ai
- Claude API
- OpenAI Codex and the ChatGPT desktop app
- ChatGPT on the web
- OpenAI API
- OpenCode
- Google Antigravity
- Other agents
- The skills CLI
- Platforms not listed here

## Shared standard

Verification: vendor. Source: https://agentskills.io/specification

- A skill is a folder with a `SKILL.md` file: YAML frontmatter, then Markdown instructions.
- Required fields: `name` (1 to 64 characters, lowercase letters, digits and hyphens, equal to the folder name) and `description` (1 to 1024 characters).
- Optional fields: `license`, `compatibility` (at most 500 characters), `metadata` (string keys and string values), `allowed-tools` (experimental).
- Optional folders: `scripts/`, `references/`, `assets/`.
- Reference validator: `skills-ref validate ./my-skill` (https://github.com/agentskills/agentskills/tree/main/skills-ref).

Claude Code, OpenAI Codex and Google Antigravity state that their skills follow or build on this standard. OpenCode reads the same folder format and accepts the standard's portability fields.

## Claude Code

Verification: vendor. Sources: https://code.claude.com/docs/en/skills and https://code.claude.com/docs/en/memory

- Install paths: `.claude/skills/<name>/` (project) and `~/.claude/skills/<name>/` (personal). A skill folder may be a symlink.
- Skills of the signed-in claude.ai account are synced into `~/.claude/skills/synced/` (in the terminal from version 2.1.273). A user-authored skill folder named `synced` is skipped.
- Invocation: automatic from the description, or `/<name>`.
- Listing limit: the description plus the Claude Code field `when_to_use` is cut at 1,536 characters. With many skills, descriptions are dropped to fit a budget of 1% of the context window.
- A new top-level skills folder created during a session needs `/reload-skills`.
- Extra frontmatter fields exist (invocation control, subagent execution, hooks and others). They work only in Claude Code.
- Project instructions: reads `CLAUDE.md`. A `CLAUDE.md` containing `@AGENTS.md` imports a shared `AGENTS.md`. From version 2.1.277 it also reads `AGENTS.md` directly when no `CLAUDE.md` exists.
- Runtime: the user's machine, with full network access.

## claude.ai

Verification: vendor. Source: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview

- Custom skills are uploaded as zip files.
- Availability: Pro, Max, Ultra, Team and Enterprise plans with code execution enabled.
- Only the six standard frontmatter fields are accepted. Any other key is a hard error.
- `name` cannot contain `anthropic` or `claude`. Neither `name` nor `description` can contain XML tags.
- Network access is full, partial or absent, depending on user and admin settings.
- This page says custom skills do not sync across surfaces: a skill uploaded to claude.ai is not available in the Claude API, and the reverse. The Claude Code page documents one exception, in one direction: claude.ai account skills are synced into Claude Code (see the Claude Code section). Skills created in Claude Code folders stay on the filesystem, separate from claude.ai and the API.
- Step-by-step upload instructions: https://support.claude.com/en/articles/12512198-creating-custom-skills (not read for this snapshot).

## Claude API

Verification: vendor. Sources: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview and https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

- Upload through the `/v1/skills` endpoints. Use a skill by listing its `skill_id` in the `container` parameter together with the code execution tool.
- Uploaded skills are shared with the whole workspace.
- Runtime: a sandbox with no network access and no package installation. Only preinstalled packages are available.
- Body guidance: under 500 lines, references one level deep, a contents list in reference files over 100 lines.

## OpenAI Codex and the ChatGPT desktop app

Verification: vendor. Source: https://learn.chatgpt.com/docs/build-skills (https://developers.openai.com/codex/skills redirects there)

- Standalone skills work in the ChatGPT desktop app, the Codex CLI and the IDE extension. Skills bundled in plugins also work in ChatGPT on web, desktop and mobile.
- Install paths: `.agents/skills/` in the working folder, in each parent folder and at the repository root; `$HOME/.agents/skills` for the user; `/etc/codex/skills` for the machine. Symlinked skill folders are followed.
- Invocation: automatic from the description; `$<name>` or `/skills` in Codex; `@` in ChatGPT.
- Listing budget: at most 2% of the context window, or 8,000 characters when the window is unknown. Descriptions are shortened first, so the key use case goes first.
- Bundled skills include `skill-creator` and `skill-installer`. Two skills with the same name are not merged.
- Optional sidecar file `agents/openai.yaml`: interface metadata, `policy.allow_implicit_invocation` and tool dependencies.
- Vendor advice: one job per skill, instructions before scripts, imperative steps with explicit inputs and outputs, and test prompts against the description.
- Distribution beyond one repository is done with plugins.

## ChatGPT on the web

Verification: unverified. On 2026-11-18 both https://openai.com/academy/skills/ and https://help.openai.com/en/articles/20001066-skills-in-chatgpt returned HTTP 403 to automated requests. The points below come from search-result summaries of those pages and must be confirmed before they are repeated to a user:

- A skill has a name and description, workflow instructions (normally a `SKILL.md` file) and supporting resources.
- Skills can be created by chatting ("Build me a skill ..."), in a skills editor, or by uploading from the computer.
- Access is limited to some Business, Enterprise, Healthcare and Edu workspaces, depending on workspace settings.

## OpenAI API

Verification: unverified. Source named by search results: https://developers.openai.com/api/docs/guides/tools-skills

- Search-result summaries mention a `POST /v1/skills` endpoint that accepts a directory or a zip, with limits of 50 MB per zip, 500 files per version and 25 MB per uncompressed file. Confirm on the page before relying on it.

## OpenCode

Verification: vendor. Source: https://opencode.ai/docs/skills/

- Install paths: `.opencode/skills/` (project) and `~/.config/opencode/skills` (global). For compatibility it also reads `.claude/skills` and `.agents/skills`, in the project and in the home folder.
- The skill ID comes from the path, not from the frontmatter `name`. Keep the two equal.
- A skill without a `description` is not advertised to the model.
- Loading: the model calls the `skill` tool with the ID, or the user mentions `@<id>`.
- Paths written in a skill resolve against the folder that holds `SKILL.md`. Bundled files are read only when the skill says so.
- `license` and `compatibility` are accepted and not interpreted.
- Hiding a skill from the model: `metadata.opencode/autoinvoke: false`, or a `deny` permission rule.

## Google Antigravity

Verification: vendor. Source: https://antigravity.google/docs/skills/

- Install paths: `<workspace-root>/.agents/skills/<name>/` (workspace) and `~/.gemini/config/skills/<name>/` (global). The older `.agent/skills` still works.
- Frontmatter: `description` is required; `name` is optional and defaults to the folder name. No other field is documented.
- Vendor examples use the folders `scripts/`, `examples/` and `resources/`.
- Invocation: automatic from the description, or `/<name>`.
- The CLI needs `/skills reload` after a skill is added while it is running.
- Vendor advice: keep skills focused, write clear third-person descriptions, treat scripts as black boxes (run them with `--help`), and include decision trees in complex skills.

## Other agents

Verification: third-party. Source: https://github.com/vercel-labs/skills/blob/main/docs/agents.md

These paths come from the `skills` CLI documentation, not from each vendor. Check the vendor's documentation before giving them to a user.

| Agent | Project path | Global path |
|---|---|---|
| Cursor | `.agents/skills/` | `~/.cursor/skills/` |
| Gemini CLI | `.agents/skills/` | `~/.gemini/skills/` |
| GitHub Copilot | `.agents/skills/` | `~/.copilot/skills/` |
| Windsurf | `.windsurf/skills/` | `~/.codeium/windsurf/skills/` |
| Goose | `.goose/skills/` | `~/.config/goose/skills/` |
| Roo Code | `.roo/skills/` | `~/.roo/skills/` |

## The skills CLI

Verification: third-party tool, read on its own documentation. Source: https://github.com/vercel-labs/skills/blob/main/docs/commands.md

- `npx skills add <owner>/<repo>` installs from GitHub, and `npx skills add ./path` from a local folder. `-g` installs for the user instead of the project, `-a <agent>` selects agents, `--list` lists the skills without installing.
- In a repository it looks for a root `SKILL.md` first and then for `skills/<name>/SKILL.md`, which is the layout used here.
- It needs Node.js 22.20 or later. It is a community project and does not belong to any agent vendor.

## Platforms not listed here

There is no snapshot. Search the vendor's official documentation for Agent Skills or `SKILL.md` support. If the platform has none, find its native customisation format (custom instructions, custom assistants, projects) and its limits, then apply the adapter rule in `SKILL.md`.
