---
name: harness-engineer
description: Design and generate complete Harness structures for Claude Code agents. Use this skill whenever the user asks to "create a harness", "build an agent structure", "make a CLAUDE.md", "design an agent workflow", "scaffold a project for Claude Code", "create skills", "create subagents", "set up a .claude directory", "create a plugin", "set up hooks", "design agent teams", or any request involving agent architecture, context engineering, harness engineering, or Claude Code project configuration. Also trigger when the user mentions "agent harness", "context engineering", "harness structure", "agent scaffold", "plugin manifest", "event hooks", "agent teams", "multi-agent coordination", "evaluator agent", "sprint contract", "context reset", or wants to turn a workflow into a reusable Claude Code project. Even if the user simply describes a task they want to automate with Claude Code, use this skill to design the proper harness around it.
---

# Harness Engineer

Design and generate production-ready Harness structures for Claude Code agents.

## What this skill does

Take a user's task description and produce a complete `.claude/` directory structure with all necessary files: `CLAUDE.md`, subagents, skills, commands, rules, hooks, plugin manifests, settings, and progress tracking. Every output follows Anthropic's published best practices for harness engineering and context engineering (updated March 2026).

## Core workflow

1. **Understand the task** — Ask clarifying questions if the scope, audience, or constraints are unclear. Determine what the agent should produce, what information it needs, what actions it should take, and what rules it must follow.

2. **Read references** — Before generating any files, read the reference files bundled with this skill:
   - `references/harness-principles.md` — Anthropic's harness engineering principles
   - `references/context-engineering.md` — Context engineering best practices
   - `references/file-templates.md` — Templates for every file type
   - `references/examples.md` — Complete worked examples

3. **Design the architecture** — Decide which components are needed:
   - How many subagents? What are their specializations?
   - What skills should be bundled? What references and scripts do they need?
   - What slash commands serve as entry points?
   - What rules apply to which file patterns?
   - What hooks enforce deterministic constraints?
   - Should this be packaged as a plugin for sharing?
   - Does the task warrant agent teams for parallel work?
   - What format should progress tracking use?

4. **Generate all files** — Create every file with proper content. Use the templates from `references/file-templates.md` as starting points, then customize for the specific task.

5. **Package and deliver** — Organize into a clean directory, create a ZIP, and present to the user with an architecture diagram and usage instructions.

## Architecture decision framework

Read `references/harness-principles.md` for the full decision framework. Key rules:

- Start with the simplest possible structure. Single agent with rich context beats multi-agent complexity.
- Every component encodes an assumption about what the model cannot do alone. Stress-test those assumptions as models improve.
- Add subagents only when context isolation or tool restriction is genuinely needed.
- Add an evaluator agent when self-evaluation fails (subjective tasks, complex QA).
- Every file in CLAUDE.md must pass the test: "Would Claude make a mistake without this line?"
- Skills over system prompt. Move specialized knowledge to skills so it loads on demand.
- Rules over CLAUDE.md. Move file-specific constraints to glob-scoped rules.
- Hooks over CLAUDE.md for hard requirements. CLAUDE.md is advisory (~80% compliance); hooks are deterministic (100%).
- JSON for state tracking. Models treat JSON as code and modify it more carefully than Markdown.
- Consider plugin packaging when the harness should be shared across projects or teams.

## Output structure

Every harness must include at minimum:

```
project-name/
├── CLAUDE.md                     # Always. Under 200 lines.
├── .claude/
│   ├── settings.json             # Permissions and tool config
│   └── [components as needed]
└── [working directories]
```

Scale up from there based on task complexity. Read `references/file-templates.md` for the template of each component type.

## Quality checklist (run before delivery)

1. CLAUDE.md is under 200 lines and every line would prevent a mistake if removed
2. All skill descriptions are "pushy" — they list specific trigger phrases
3. Subagent tool access follows least privilege (read-only agents get read-only tools)
4. Rules use glob patterns that match the correct directories
5. No duplicate instructions across CLAUDE.md, skills, and rules
6. Progress tracking file uses JSON, not Markdown
7. Working directories exist with .gitkeep files
8. Hooks enforce hard requirements (linting, security, formatting) that CLAUDE.md cannot guarantee
9. If packaged as plugin: manifest is valid, skills are namespaced, hooks use `${CLAUDE_PLUGIN_ROOT}`
10. An architecture diagram or README explains the structure
11. The harness follows the principle: "find the simplest solution possible"
12. The harness has been stress-tested: would removing any component cause failures? Would the current model handle any component's job without it?
