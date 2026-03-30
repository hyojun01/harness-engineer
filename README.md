# harness-engineer

A Claude Code skill for designing and generating production-ready agent harnesses. Give it a task description and it produces a complete `.claude/` directory with all necessary files — CLAUDE.md, subagents, skills, commands, rules, hooks, plugin manifests, and progress tracking — following Anthropic's harness engineering best practices.

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

# Code pipeline with evaluator
python3 scripts/scaffold.py code-pipeline ./output \
  --agents implementer \
  --evaluator \
  --hooks \
  --rules code-style,testing

# Reusable plugin
python3 scripts/scaffold.py team-tools ./output \
  --plugin \
  --skills code-review \
  --hooks
```

Run `python3 scripts/scaffold.py --help` for all options.

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

| File | What it covers |
|------|---------------|
| `harness-principles.md` | The agent loop, harness evolution stages (single → two-agent → GAN-inspired three-agent), session continuity, verification loops, tool design, hooks, and the architecture decision framework |
| `context-engineering.md` | Context rot, attention budgets, progressive disclosure, CLAUDE.md design rules, skill/subagent context design, and 13 anti-patterns to avoid |
| `file-templates.md` | Copy-paste templates for CLAUDE.md, settings.json, subagents, evaluators, skills, commands, rules, hooks, plugins, progress tracking, and feature lists |
| `examples.md` | Four complete examples — a simple code reviewer, a two-agent content pipeline, a four-agent development harness, and a reusable research plugin |

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

## Requirements

- Python 3.6+ (for `scripts/scaffold.py`, standard library only)
- Claude Code (to use as a skill)
