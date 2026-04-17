---
name: harness-engineer
description: Design and generate complete Harness structures for Claude Code agents. Use this skill whenever the user asks to "create a harness", "build an agent structure", "make a CLAUDE.md", "design an agent workflow", "scaffold a project for Claude Code", "create skills", "create subagents", "set up a .claude directory", "create a plugin", "set up hooks", "design agent teams", or any request involving agent architecture, context engineering, harness engineering, or Claude Code project configuration. Also trigger when the user mentions "agent harness", "context engineering", "harness structure", "agent scaffold", "plugin manifest", "event hooks", "agent teams", "multi-agent coordination", "evaluator agent", "sprint contract", "context reset", or wants to turn a workflow into a reusable Claude Code project. Even if the user simply describes a task they want to automate with Claude Code, use this skill to design the proper harness around it.
---

# Harness Engineer

Design and generate production-ready Harness structures for Claude Code agents.

## What this skill is (and isn't)

This skill is a **skeleton generator + reference library**. It produces a `.claude/` directory structure with placeholder-filled templates that the user must hand-edit to finalize. It does NOT auto-write a production CLAUDE.md from scratch — Anthropic's guidance is that hand-crafted CLAUDE.md files outperform fully auto-generated ones, so the scaffold deliberately leaves `{placeholder}` values for the user to fill in.

> **About this skill's sources:** Content is drawn from Anthropic's Claude Code documentation (verified April 2026). Where the author made inferences or chose conventions not spelled out by Anthropic, references are labeled `Interpretation` or `Optional Practice`. When documentation conflicts with a reference file here, defer to the official Claude Code docs.

## Core workflow

1. **Understand the task.** Determine what the agent should produce, what information it needs, what actions it takes, and what rules it must follow. Ask clarifying questions if scope is unclear.

2. **Read ONLY the references you need.** The reference files total ~1,800 lines — do not load them all. Use this routing:

   | User's request involves | Read |
   |-------------------------|------|
   | Architecture decisions (how many agents? evaluator? teams?) | `references/harness-principles.md` |
   | CLAUDE.md content, skill design, context budget | `references/context-engineering.md` |
   | Writing any specific file (frontmatter, hooks, settings.json) | `references/file-templates.md` |
   | Seeing complete worked harnesses at different complexity | `references/examples.md` |
   | Plugin packaging | `file-templates.md` §Plugin + `examples.md` Example 4 |
   | Agent teams | `harness-principles.md` §Agent teams |
   | Hook events, exit codes, matchers | `file-templates.md` §Hooks (single source of truth) |

3. **Design the architecture.** Start with the simplest structure (single agent + rich CLAUDE.md) and add components only when the current structure fails without them. Key decisions:
   - How many subagents, and what's each one's specialty?
   - Which frontmatter fields does each subagent need? (see `file-templates.md` for the 17-field table)
   - What skills should be bundled? What references/scripts do they need?
   - What slash commands serve as entry points?
   - What rules apply to which file patterns (glob-scoped)?
   - What hooks enforce deterministic constraints that CLAUDE.md cannot guarantee?
   - Plugin packaging? (If yes: no `hooks`/`mcpServers`/`permissionMode` in subagents)
   - Agent teams? (Higher token cost, needs `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)
   - Claude Agent SDK orchestration more appropriate than `.claude/` for this use case?

4. **Generate the files.** Either use `scripts/scaffold.py` for a quick skeleton, or hand-write from templates in `file-templates.md`. Customize placeholders for the specific task. Hook scripts MUST read input from **stdin as JSON** (not `$FILE` env vars).

5. **Package and deliver.** Organize into a clean directory, ZIP if the user wants a shareable artifact, and present with an architecture diagram and usage notes.

## Key design principles

Read `references/harness-principles.md` for the full framework. The rules that prevent the most common mistakes:

- **Simplest wins.** Single agent with rich context beats multi-agent complexity. Every component encodes an assumption about what the model cannot do alone — stress-test those assumptions as models improve.
- **Skills over system prompt.** Move specialized knowledge to skills so it loads on demand.
- **Rules over CLAUDE.md.** Move file-specific constraints to glob-scoped rules.
- **Hooks over CLAUDE.md for hard requirements.** CLAUDE.md is advisory (~80% compliance); hooks are deterministic (100%). Use `SessionStart` with `matcher: "compact"` for reminders that must survive compaction.
- **JSON for state tracking.** Models treat JSON as code and modify it more carefully than Markdown.
- **`type: "prompt"` hooks are for yes/no model decisions, NOT reminder injection.** Using them as reminders is a subtle bug that won't do what you expect.

## Output structure

Every harness includes at minimum:

```
project-name/
├── CLAUDE.md                     # Always. Under 200 lines. Hand-edit required.
├── .claude/
│   ├── settings.json             # Permissions, hooks, env
│   └── [components as needed]
└── [working directories]
```

Scale up based on task complexity — see the calibration table in `references/examples.md` §Complexity calibration guide.

## Pre-delivery checklist (10 items)

1. CLAUDE.md is under 200 lines; every line would prevent a mistake if removed
2. Skill descriptions are "pushy" — they list specific trigger phrases
3. Subagent tool access follows least privilege; `model` defaults to `inherit` unless there's a reason to override
4. Subagent frontmatter uses only supported fields (17 documented — see `file-templates.md` §frontmatter)
5. Progress tracking uses JSON, not Markdown
6. Hooks read input from **stdin as JSON**; prefer `if` for declarative filtering; `type: "prompt"` used only for yes/no model decisions
7. PreToolUse hooks use modern `hookSpecificOutput.permissionDecision` for blocking (exit 2 still works but is less expressive)
8. Reminders that must survive compaction live in `SessionStart` with `matcher: "compact"`, not in `PreCompact` or `type: prompt` hooks
9. If plugin: subagents have NO `hooks`/`mcpServers`/`permissionMode`; hook paths use `${CLAUDE_PLUGIN_ROOT}`
10. Each component passes the stress test: would removing it cause a specific failure? If the current model could handle it alone, remove the component

## Known false claims to avoid

Things people say about Claude Code that are **not true** in the current docs — do not include these in generated harnesses:

- "Shift+Tab toggles Delegate mode" — no such shortcut exists. The correct way to prevent the lead from implementing tasks is `tools: Agent(worker_a, worker_b), Read, Bash` in the lead's frontmatter, or a natural-language instruction.
- "`type: prompt` hooks inject reminders" — they send a prompt to a fresh model for yes/no decisions.
- "Exit code 2 always blocks" — it only blocks for certain events. `PostToolUse`, `Notification`, `SubagentStart`, `SessionStart/End`, `CwdChanged`, `FileChanged`, `PostCompact`, `StopFailure`, `PermissionDenied` do NOT block on exit 2.
- "Agent teams recommend 2-3 teammates" — Anthropic recommends 3-5.
- "`opusplan` is a valid subagent `model` value" — it's a valid `/model` CLI alias, but subagent frontmatter documentation only explicitly lists `sonnet`/`opus`/`haiku`/`inherit`/full model IDs.