# harness-engineer

A Claude Code skill for designing and generating agent harness skeletons. Give it a task description and it produces a `.claude/` directory — CLAUDE.md, subagents, skills, commands, rules, hooks, plugin manifests, and progress tracking — with placeholders for the task-specific details you fill in. Content follows Anthropic's Claude Code documentation as of April 2026.

> **What this skill is (and isn't):** A skeleton generator plus a reference library. It is not an auto-writer for production CLAUDE.md files — Anthropic's guidance is that hand-crafted CLAUDE.md files outperform fully auto-generated ones, so the scaffold deliberately leaves `{placeholder}` values for you to finalize. Reference files are labeled `Official`, `Interpretation`, or `Optional Practice` so you can tell load-bearing documentation from author convention.

## Quick start

### As a Claude Code skill

Copy or symlink this directory into your `.claude/skills/` folder:

```bash
cp -r harness-engineer ~/.claude/skills/harness-engineer
```

Then ask Claude Code to design a harness:

```
> Create a harness for a code review agent that checks style, security, and test coverage
> Build a multi-agent pipeline for processing and summarizing research papers
> Scaffold a plugin that automates database migration workflows
```

The skill triggers automatically when you mention agent architecture, harness engineering, scaffolding, or Claude Code project configuration.

### Using the scaffold tool directly

The scaffold script generates a starter directory structure without needing Claude Code:

```bash
# Research agent with multiple subagents
python3 scripts/scaffold.py research-agent ./output \
  --agents planner,researcher,writer \
  --skills deep-research \
  --commands research \
  --rules citations

# Code pipeline with evaluator (Opus model, project-scoped memory)
python3 scripts/scaffold.py code-pipeline ./output \
  --agents implementer \
  --evaluator \
  --hooks \
  --rules code-style,testing \
  --model opus --memory project

# Reusable plugin
python3 scripts/scaffold.py team-tools ./output \
  --plugin \
  --skills code-review \
  --hooks

# Parallel debugging with agent teams
python3 scripts/scaffold.py parallel-debug ./output \
  --agents hypothesis-a,hypothesis-b \
  --teams --model inherit
```

Run `python3 scripts/scaffold.py --help` for all options. Additional flags: `--model` (inherit/sonnet/opus/haiku — default `inherit` matches the main conversation's model), `--memory` (user/project/local/none), `--background`, `--teams`. The scaffold warns when flag combinations silently conflict (e.g. `--plugin` with `--teams` or `--evaluator`, since plugin subagents can't carry `mcpServers`/`hooks`/`permissionMode` and plugins don't inject the `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` env var).

## What's inside

```
harness-engineer/
├── SKILL.md                          # Skill definition and workflow
├── references/
│   ├── harness-principles.md         # Foundational design rules
│   ├── context-engineering.md        # Context optimization strategies
│   ├── file-templates.md             # Templates for every component type
│   └── examples.md                   # Worked examples (simple → complex)
└── scripts/
    └── scaffold.py                   # Directory structure generator
```

### Reference materials

Content in the reference files is tagged with source labels so you can tell what is load-bearing documentation vs. recommended practice:

- **Official** — directly from Anthropic's documentation or engineering blog posts
- **Interpretation** — inferred from Anthropic's examples, observed behavior, or engineering context
- **Optional Practice** — community convention or author recommendation

| File | What it covers |
|------|---------------|
| `harness-principles.md` | Agent loop, harness evolution stages (single → two-agent → three-agent generator/evaluator), model-specific configurations, Claude Agent SDK orchestration, session continuity, verification loops, tool design, the 4 hook handler types (`command` / `http` / `prompt` / `agent`), hook matcher evaluation rules (exact vs. regex), agent teams (3–5 teammates, declarative tool restriction via `Agent(...)` — there is no "Delegate mode" keyboard shortcut), plugins, and the architecture decision framework |
| `context-engineering.md` | Context rot, attention budgets, progressive disclosure, CLAUDE.md design rules, skill/subagent context design (SKILL.md under 500 lines), the `tools` allowlist vs. `disallowedTools` denylist, subagent `skills`/`mcpServers`/`memory` preloading, model-specific compaction strategies, SDK auto-compaction, and 18 anti-patterns |
| `file-templates.md` | Copy-paste templates for CLAUDE.md, settings.json, subagents (17-field frontmatter table, all Official), evaluators, skills, commands, rules, hooks (per-event blocks-on-exit-2 table, modern `hookSpecificOutput.permissionDecision` schema, declarative `if` filtering, `SessionStart matcher: "compact"` for reminders that survive compaction), plugins, progress tracking, and feature lists. Also covers running subagents as the main session agent via `claude --agent` and the `Agent(a, b, c)` tool-allowlist syntax |
| `examples.md` | Four complete examples — simple code reviewer, two-agent content pipeline, four-agent development harness (with Playwright MCP evaluator), and a reusable research plugin. Snippets are tagged ✅ (safe to copy) or 📐 (conceptual pseudocode) |

## Key concepts

**Harness** — Everything outside the model: tool access, context management, safety rules, feedback loops, and observability.

**Progressive disclosure** — Load just enough information for the agent to decide what to do next, then reveal more details as needed. Three tiers: metadata (always loaded) → skill body (on trigger) → references and scripts (on demand).

**Harness evolution** — Start simple and add complexity only when needed:

```
Stage 1: Single agent + CLAUDE.md
  → Stage 2: Initializer + Worker (multi-session tasks)
    → Stage 3: Planner + Generator + Evaluator (QA-critical tasks)
```

**Separation of enforcement mechanisms:**

| Mechanism | Compliance | Use for |
|-----------|-----------|---------|
| CLAUDE.md | ~80% | Guidance, conventions, workflow advice |
| Rules | ~80%, scoped to file patterns | File-type-specific constraints |
| Hooks | 100% (deterministic) | Linting, security checks, formatting |

**Model-specific strategies:** Harness complexity should match the model. Sonnet 4.5 needs context resets and per-sprint evaluation. Opus 4.5 can rely on compaction. Opus 4.6 supports continuous multi-hour sessions with SDK auto-compaction.

## Common false claims the skill actively avoids

A handful of claims about Claude Code circulate in community posts but are not in Anthropic's documentation. The skill is explicit about not generating them:

- **"Shift+Tab toggles Delegate mode."** No such shortcut exists. To prevent an agent-team lead from implementing tasks itself, restrict its tools declaratively — `tools: Agent(worker_a, worker_b), Read, Bash` — or steer it with natural language.
- **"`type: prompt` hooks inject reminders."** They don't. A prompt hook sends a single-turn yes/no decision request to a fresh model and expects a JSON response back. For reminders that must survive compaction, use `SessionStart` with `matcher: "compact"` and print to stdout.
- **"Exit code 2 always blocks."** It only blocks on events that support blocking (`PreToolUse`, `UserPromptSubmit`, `Stop`, `PreCompact`, `TaskCreated`, `TaskCompleted`, and a few more). On `PostToolUse`, `Notification`, `SessionStart`, `CwdChanged`, `FileChanged`, `PostCompact`, `StopFailure`, `PermissionDenied`, and others, exit 2 just surfaces stderr — the action still proceeds.
- **"Agent teams recommend 2–3 teammates."** Anthropic's recommendation is 3–5.
- **"`opusplan` is a subagent model value."** `opusplan` is a `/model` CLI alias; subagent frontmatter documents `sonnet` / `opus` / `haiku` / `inherit` / full model IDs.

## Requirements

- Python 3.6+ (for `scripts/scaffold.py`, standard library only)
- Claude Code (to use as a skill)
