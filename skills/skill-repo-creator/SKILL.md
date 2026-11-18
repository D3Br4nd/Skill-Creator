---
name: skill-repo-creator
description: >-
  Packages a repetitive task as a reusable Agent Skill in its own git repository.
  Use when someone asks to build or scaffold a new skill, including “crea una skill”
  or “trasforma questa procedura in una skill”. Accepts a named platform or a
  portable brief. Installation, troubleshooting and running existing skills are
  separate tasks.
license: MIT
metadata:
  author: "Max Brandini"
  version: "0.2.0"
---

# Skill Repo Creator

Turn one recurring task into a standalone git repository containing an installable skill, evaluation cases and instructions for its users. The factory requires a writable filesystem, Python 3.8+ and git. Live source checks need web access. Paths to bundled resources are relative to this file. Resolve script paths against this folder even when running from another project.

## Understand the request

Identify the input, the recurring transformation and the result the user expects. If the task itself is missing, ask for it. Ask about an ambiguous detail only when it would materially change the result. If the brief covers independent jobs, agree on one before creating its repository.

- **Task only or several agents.** Use the [Agent Skills specification](https://agentskills.io/specification) as the baseline. Write for the capabilities the task needs. A missing platform alone requires no follow-up.
- **Named platform.** Keep the same portable skill folder. Check the vendor's official documentation for discovery, installation and the specific capabilities the task needs. Put installation commands, account settings and invocation syntax in the README.
- **Platform with a different customization format.** If the vendor documents a usable alternative, add the minimum instructions or artifact needed under `adapters/` and explain how to use it. If support is unknown, deliver the portable folder and identify the open question. A failed documentation lookup does not establish lack of support.

Consult [references/platforms.md](references/platforms.md) for sources and the dated install table. If live sources are unavailable, identify snapshot claims as “not re-verified” and preserve their original verification status. Keep URLs paired with the decisions they support. Use [references/portability.md](references/portability.md) for dependency declarations and optional host integrations.

## Build the repository

1. **Define success.** Read [references/authoring-rules.md](references/authoring-rules.md). Choose a descriptive name and draft three evals before writing the workflow. Cover a typical request, a paraphrase and an edge case, each with an observable expected result. Add at least eight trigger queries with a balance of matches and near misses.
2. **Scaffold.** Run the bundled script with the user’s destination or the workspace default. Otherwise choose a parent directory outside any existing git worktree. Preserve existing work when a name collides.

   ```sh
   python3 "<skill-folder>/scripts/scaffold_skill_repo.py" --name "<skill-name>" --description "<description>" --dest "<parent-directory>"
   ```

   The script renders `assets/repo-template/`, copies the validator and initializes git. The MIT holder defaults to the git user name. Use `--author` for an explicit holder. The default layout is independent of host discovery folders. Use `--dev-links` when local testing specifically calls for the bundled discovery links.

3. **Write the skill.** Replace the scaffold markers. Keep the goal, essential inputs, procedure and success criteria. Merge or remove template headings that add no task-specific guidance. Bundle a script for deterministic work, state its runtime in the skill body and use the optional `compatibility` field when the target accepts it and link the resources the agent needs. Put eval fixtures under `evals/files/` and list their paths relative to the installed skill folder.
4. **Write for the reader.** Use the user's language for questions, the generated README and the report, unless they request otherwise. Keep the repository base and agent-facing files in English by default. Include natural trigger phrases in the user's language alongside the English description. In the generated README, retain the install table's snapshot date, verify any requested platform and identify which behaviors were actually tested.
5. **Validate and exercise.** Run `python3 "<new-repo>/scripts/validate_skill.py"`. Fix every error and fix or explain each warning. Run the three README prompts in fresh contexts when available and compare the actual output with the corresponding evals. Correct failures and rerun the affected checks. Record unexecuted prompts as such. Structural validation alone does not exercise the skill.
6. **Commit locally.** Check that the new repository contains its own git metadata and that the intended files are present, then stage them and make one initial commit. Leave publishing and installation to an explicit user request.

## Delivery

Use five parts, with headings translated into the user's language.

1. **Technical analysis** explains how the task works, required capabilities and any platform limits.
2. **Complete skill** gives the repository path and tree, the full SKILL.md verbatim and a one-line description of each other bundled file.
3. **Installation and settings** identifies the installable folder and gives documented steps for the requested host, or the dated choices for a portable brief.
4. **Practical tests** lists the three prompts, their expected results and what was actually run.
5. **Official sources** pairs each source with the decision it supports and identifies anything still unverified.
