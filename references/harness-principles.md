# Harness Engineering Principles

Consolidated from Anthropic's engineering blog, platform documentation, and community best practices (updated April 2026).

> **Source labels used in this document:**
> - **Official** — Directly from Anthropic's documentation or blog posts
> - **Interpretation** — Inferred from Anthropic's examples, observed behavior, or engineering context
> - **Optional Practice** — Community convention or author recommendation; not from Anthropic

## Foundational principle

> **Official:** "Find the simplest solution possible, and only increase complexity when needed." — Anthropic, Building Effective Agents

Reliable AI agents are built through better harness design, not better models. The harness is everything outside the model: tool access, context management, safety rules, feedback loops, and observability.

## The two core problems

> **Official** (from Anthropic's harness blog)

### 1. One-shotting
Agents try to do everything at once, exhaust the context window mid-implementation, and leave the next session with broken, undocumented work.

**Solution:** Prompt the agent to work on one feature/task at a time. Use a structured task list (JSON format) so the agent always knows what to do next and what's already done.

### 2. Premature completion
After some progress, the agent sees existing work and declares the project done.

**Solution:** Maintain a feature/task list file where items are only marked complete after verification. Use strongly-worded instructions: "It is unacceptable to remove or edit tasks unless they have been verified."

## The agent loop

> **Official**

All effective agents follow: **gather context → take action → verify work → repeat**

This loop must be explicitly designed into the harness:
- Gather: Read progress files, git logs, task lists at session start
- Act: Work on one task at a time, make incremental changes
- Verify: Test the work end-to-end (not just unit tests), use browser automation for web apps
- Repeat: Commit progress, update tracking files, move to next task

## Harness evolution stages

> **Interpretation:** These stages are derived from Anthropic's examples. They represent a common progression, not a mandatory ladder.

| Stage | Architecture | When to use |
|-------|-------------|-------------|
| 1 | Single agent + rich CLAUDE.md | Default starting point. Works for most tasks. |
| 2 | Initializer + Worker | Tasks spanning multiple sessions. Initializer sets up environment. |
| 3 | Planner + Generator + Evaluator | Subjective quality matters or self-evaluation fails. |

### Stage 3: The three-agent architecture (March 2026)

> **Official** (from Anthropic's harness blog). Note: this is a **recommended pattern** that Anthropic used for long-running application development, not a mandatory structure for all harnesses. Adapt or simplify based on your task's complexity.

Anthropic's harness for long-running application development uses three specialized agents inspired by Generative Adversarial Networks (GANs):

**Planner:** Takes a short 1-4 sentence prompt and expands it into a full product spec. Prompted to be ambitious about scope and focus on product context rather than granular technical implementation. If the planner over-specifies technical details and gets something wrong, errors cascade into downstream implementation.

**Generator:** Works in sprints (or continuously for capable models), implementing one feature at a time. Self-evaluates before handing off to QA. Has git for version control.

**Evaluator:** Uses Playwright MCP to interact with the *running application* as a real user would — clicking through features, testing API endpoints, probing database states. Grades against concrete criteria with hard thresholds per sprint.

**Sprint contracts:** Before each sprint, the generator and evaluator negotiate what "done" looks like. The generator proposes what it will build and how success is verified; the evaluator reviews to ensure correctness. Communication happens via files — one agent writes, another reads.

> **Official** (key finding on self-evaluation): Models systematically praise their own work, even when quality is mediocre. Separating generator from evaluator is far more tractable than making a generator self-critical. The evaluator must be tuned to be skeptical — this takes multiple rounds of reading evaluator logs, finding where its judgment diverges from yours, and updating the prompt.

### Evolving with models

> **Official**

Every component in a harness encodes an assumption about what the model cannot do on its own. These assumptions must be stress-tested regularly because they go stale as models improve.

Concrete example: Moving from Opus 4.5 to Opus 4.6 allowed Anthropic to:
- Remove the sprint decomposition entirely (the model sustained coherent work for 2+ hours without it)
- Drop context resets in favor of automatic compaction
- Move the evaluator to a single pass at the end rather than per-sprint grading

In the March 2026 browser DAW experiment, Opus 4.6 ran for ~3 hours 50 minutes at $124.70 without the older sprint structure. The earlier retro game maker experiment with Opus 4.5 used the full sprint harness and ran 6 hours at $200.

**Model-specific harness configurations:**

| Model | Context anxiety | Recommended strategy | Sprint structure |
|-------|----------------|---------------------|-----------------|
| Sonnet 4.5 | Strong | Context resets required | Per-sprint evaluation |
| Opus 4.5 | Mild | Compaction sufficient | Sprint-based, can simplify |
| Opus 4.6 | Negligible | SDK auto-compaction | Continuous session, single evaluation pass |

The evaluator's value depends on where the task sits relative to what the model can do reliably solo. For tasks within the model's baseline capability, the evaluator is unnecessary overhead. For tasks at the edge, it provides critical lift.

**Rule:** After every model upgrade, audit each harness component. Ask: "Does the model now handle this on its own?" If yes, remove the component.

### Claude Agent SDK orchestration

> **Official**

Anthropic's three-agent architecture is built on the Claude Agent SDK. The SDK provides:
- **Automatic compaction** — handles context growth transparently, eliminating manual context reset logic
- **Agent loop management** — structured tool-use loops with built-in error recovery
- **Multi-agent coordination** — programmatic spawning and communication between agents via files
- **Session persistence** — state transfer between sessions without custom serialization

When building harnesses programmatically (outside Claude Code's `.claude/` directory structure), use the Claude Agent SDK for orchestration. The SDK handles the plumbing (compaction, tool routing, permission enforcement) while the harness defines the behavior (agent prompts, evaluation criteria, task decomposition).

**When to use `.claude/` structure vs. SDK:**
- `.claude/` structure: Interactive Claude Code sessions, team workflows, plugin distribution
- Claude Agent SDK: Programmatic pipelines, CI/CD integration, custom multi-agent systems, production deployments

## Session continuity

> **Official**

Each new context window starts with zero memory. Bridge sessions with:

1. **Progress tracking file (JSON)** — Current status, completed items, next steps. JSON because models treat it as code and modify it more carefully than Markdown.

2. **Git commits** — Descriptive commit messages let the next session run `git log --oneline -20` to understand recent work.

3. **Standardized startup sequence:**
   - Check current directory (`pwd`)
   - Read progress file and git logs
   - Read task/feature list, pick the next item
   - Run basic verification (dev server, smoke test)
   - Begin work on the next task

4. **Clean state at session end** — Code that would be appropriate for merging: no major bugs, orderly, well-documented.

## Context window management

### Context rot and attention budget

> **Official**

Context accuracy degrades as token count increases (context rot). Every token competes with every other token for the model's attention — the "attention budget." This means more information often makes agents worse, not better.

### Instruction budget

> **Official** (~150-200 instructions); **Interpretation** (community recommends CLAUDE.md under 60 lines)

~150-200 instructions before compliance drops. The Claude Code system prompt consumes ~50. Community best practice: keep CLAUDE.md under 60 lines when possible.

### Compaction vs. context reset

> **Official**

**Compaction:** Summarize earlier parts of the conversation and reinitiate with the summary. Preserves continuity but does not give the agent a clean slate. Good for: tasks requiring back-and-forth dialogue.

**Context reset:** Clear the context entirely, start a fresh agent with a structured handoff artifact. Provides a clean slate but requires robust state transfer. Good for: long tasks where context anxiety occurs.

**Context anxiety:** Some models (notably Sonnet 4.5) begin wrapping up work prematurely as they approach what they believe is the context limit. Compaction alone does not fix this — context resets are needed. Opus 4.6 largely eliminated this behavior, making compaction sufficient.

### Subagents as context firewalls

> **Official**

Use subagents to isolate exploration noise. Each subagent explores extensively (10,000+ tokens) but returns only a condensed summary (1,000-2,000 tokens) to the main agent.

### Long task prompting

> **Optional Practice**

For lengthy tasks: "This is a very long task, so plan your work clearly. Don't run out of context with significant uncommitted work."

## Tool design principles

> **Official** (Anthropic blog + Vercel case study)

- Fewer tools often lead to better performance (Vercel removed 80% and improved).
- If a CLI is well-represented in training data (git, docker, psql), prompt the agent to use the CLI directly rather than adding an MCP server.
- Too many MCP tools fill the context window with descriptions, pushing into the "dumb zone."
- Dynamic tool loading (`ENABLE_TOOL_SEARCH=auto`) defers tool descriptions until needed.
- Classify actions by risk: read-only (auto-approve) vs. write (require review) vs. destructive (require confirmation).
- If a human engineer cannot definitively say which tool to use in a given situation, the agent cannot be expected to do better.

## Verification loops

> **Official**

The most common failure: marking work complete without proper end-to-end testing.

- Provide testing tools appropriate to the domain (Playwright for web, pytest for Python, etc.)
- Prompt the agent to test as a human user would, not just run unit tests
- Separate the evaluator from the generator when self-evaluation fails (subjective tasks like design, complex QA)
- Use concrete grading criteria with hard thresholds — not vague "is this good?"
- Calibrate the evaluator with few-shot examples showing detailed score breakdowns

### Evaluation criteria example (frontend design)

> **Interpretation** (derived from Anthropic's DAW experiment scoring)

- **Design quality:** Does the design feel like a coherent whole rather than a collection of parts?
- **Originality:** Evidence of custom decisions, or just template layouts and library defaults?
- **Craft:** Typography hierarchy, spacing consistency, color harmony, contrast ratios.
- **Functionality:** Can users understand the interface and complete tasks without guessing?

Weight criteria by what the model struggles with (design quality, originality) over what it does well naturally (craft, functionality).

## Hooks: deterministic enforcement

> **Official**

Hooks are event-driven automation scripts that execute at specific points in Claude Code's lifecycle. Unlike CLAUDE.md instructions (advisory, ~80% compliance), hooks are deterministic (100% execution).

### When to use hooks vs. CLAUDE.md
- **Hooks:** Hard requirements that must happen every time — formatting, linting, security scanning, permission enforcement.
- **CLAUDE.md:** Guidance that Claude should consider — coding style, architectural preferences, workflow suggestions.

### Hook input model

> **Official:** Hook commands receive context as **JSON via stdin**. Do NOT use environment variables like `$FILE` — they are not provided. Parse stdin with `jq` or a script to extract tool input fields such as `file_path`, `command`, etc.

### Hook exit codes

> **Official:**
> - `0` — Allow the action to proceed
> - `1` — Log a warning (action is NOT blocked)
> - `2` — Block the action / prompt Claude to reconsider

### Hook events (April 2026)

> **Official** events are from Anthropic's documentation. **Observed** events have been seen in practice.

**Session lifecycle:**
- `SessionStart` — When session begins. Good for environment setup, context priming.
- `SessionEnd` — When session ends. Good for cleanup, saving state.

**User input:**
- `UserPromptSubmit` — Before processing user input. Good for input validation, routing.

**Permission:**
- `PermissionRequest` — When a permission decision is needed. Can auto-approve or deny.
- `PermissionDenied` — After auto mode classifier denials. Return `{retry: true}` to let the model retry.

**Tool lifecycle:**
- `PreToolUse` — Before any tool runs. Can approve, deny, defer, or modify tool calls. Highest-priority control mechanism in the stack. Supports "defer" for headless sessions (pause and resume later with `-p --resume`).
- `PostToolUse` — After tool completes successfully. Good for formatting, logging, notifications.
- `PostToolUseFailure` — After a tool call fails. Good for error recovery, fallback strategies.

**Agent lifecycle:**
- `SubagentStart` — When a subagent spawns. Good for logging, resource allocation.
- `SubagentStop` — When a subagent finishes. Good for cleanup, result validation.
- `Stop` — When the main agent finishes. Good for final validation, cleanup.

**Task and team:**
- `TaskCompleted` — When a task is marked complete. Blocking — can trigger follow-up actions.
- `TeammateIdle` — When an agent team member becomes idle. Good for reassigning work.

**Context management:**
- `PreCompact` — Before compaction. Good for injecting reminders that must survive compaction.
- `PostCompact` (Observed) — After compaction completes. Good for verifying critical context survived.
- `Notification` — For injecting context after events like compaction or other system events.

**Other observed events:**
- `TaskCreated` (Observed) — When a new task is created. Useful for logging and routing.
- `ConfigChange` (Observed) — When configuration changes at runtime. Useful for dynamic reconfiguration.

> **Note:** The event surface may expand over time. Check the official Claude Code documentation for the latest list.

### Hook types
- **Command hooks:** Execute shell scripts. Best for local validation and formatting. Receive hook input as JSON via stdin.
- **HTTP hooks:** Call external services. Best for CI/CD integration, external APIs.
- **Prompt hooks:** Modify Claude's behavior without external processes. Best for context injection and reminders.

### Hook matcher

> **Official:** The `matcher` field targets **tool names** (e.g., `"Bash"`, `"Write"`, `"Edit|Write"`). For finer filtering (e.g., blocking specific shell commands), parse the stdin JSON inside the hook script and apply conditional logic there.

### Hook priority
PreToolUse hooks override the permission system entirely — they are the highest-priority control mechanism. A PreToolUse hook returning deny will block a tool call even if permissions explicitly allow it.

## Plugins: shareable harness packages

> **Official**

Plugins bundle skills, subagents, hooks, MCP servers, and settings into a single installable unit. A plugin is your `.claude/` directory packaged up with a manifest.

### When to create a plugin
- The harness should be shared across projects or teams
- You want versioning and easy installation (`/plugin install`)
- The workflow is reusable and not project-specific

### Plugin structure
```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # Manifest: name, version, description
├── skills/                   # Skills (namespaced as plugin-name:skill-name)
│   └── skill-name/
│       └── SKILL.md
├── agents/                   # Subagents
│   └── agent-name.md
├── commands/                 # Slash commands
│   └── command-name.md
├── hooks/                    # Event hooks
│   └── hooks.json
├── .mcp.json                 # MCP server configurations
└── README.md
```

### Plugin rules

> **Official:**

- Skills are namespaced: `plugin-name:skill-name` (prevents conflicts)
- Use `${CLAUDE_PLUGIN_ROOT}` to reference files within the plugin
- `/reload-plugins` picks up changes without restarting
- Local `--plugin-dir` overrides installed marketplace plugins for testing
- **Security constraint:** Plugin subagents do NOT support `hooks`, `mcpServers`, or `permissionMode` frontmatter fields. This is a deliberate security restriction — plugins from third parties cannot modify permission enforcement or inject hooks.
- **Managed subagents** (deployed by organization admins) take precedence over project and user subagents with the same name. Place them in `.claude/agents/` inside the managed settings directory.
- Plugin marketplaces are git repos with a `marketplace.json` file. The official marketplace is available by default at `claude.ai/settings/plugins/submit`.

## Agent teams: parallel multi-agent coordination

> **Official**

Agent teams coordinate multiple Claude Code instances working simultaneously. One session acts as team lead; teammates work independently in their own context windows and communicate via a shared task list and mailbox system.

### When to use agent teams vs. subagents
- **Subagents:** Quick, focused workers that report back to a single parent. No inter-worker communication.
- **Agent teams:** Workers that need to share findings, challenge each other, and coordinate independently. Each has its own full context window.

### Best use cases for agent teams
- Research and review: multiple teammates investigate different aspects simultaneously
- New modules or features: teammates own separate pieces without stepping on each other
- Debugging with competing hypotheses: teammates test different theories in parallel
- Cross-layer coordination: changes spanning frontend, backend, and tests

### Practical guidelines
- 2-3 focused teammates consistently outperform larger teams
- Beyond 4-5 active agents, coordination overhead exceeds productivity gains
- Agent teams use ~7x the tokens of a single session in plan mode (Anthropic's cost documentation)
- File system serves as the primary coordination mechanism
- Git synchronization prevents two agents from working on the same task
- **Delegate mode** (Shift+Tab): Restricts the lead agent's tools to spawning teammates, sending messages, managing task list, and shutting down teammates. Prevents the lead from implementing tasks itself. This is the correct mode for team coordination.
- Known limitations: No session resumption for in-process teammates, one team per session, no nested teams.
- Communication via inbox-based messaging system — teammates are peers, not hierarchical workers.

### Enabling agent teams
```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```
Or add to `.claude/settings.json`.

## Architecture decision guide

> **Interpretation:** This decision guide synthesizes Anthropic's published guidance into a quick-reference format.

**Use a single agent when:**
- The task fits within one context window
- No specialized tool restrictions needed
- The workflow is linear

**Add subagents when:**
- Exploration/research noise would pollute the main context
- Different phases need different tool access (read-only vs. read-write)
- Tasks can be parallelized
- You need a "context firewall"

**Add an evaluator agent when:**
- Self-evaluation consistently fails (subjective quality, complex QA)
- The task requires testing a running application, not just reviewing code
- You need concrete grading criteria with hard thresholds

**Add skills when:**
- Domain-specific knowledge is needed but not always
- The same workflow repeats across different projects
- You want progressive disclosure (load knowledge on demand)

**Add rules when:**
- Constraints apply only to specific file types or directories
- CLAUDE.md is getting too long
- You want automatic enforcement without relying on CLAUDE.md

**Add hooks when:**
- A requirement must be enforced 100% of the time (not ~80%)
- You need to validate, lint, or format after every edit
- You want to inject context that survives compaction
- Security scanning must happen before any file write

**Use commands when:**
- You want an explicit, named entry point for a workflow
- The workflow has a clear trigger phrase
- You want discoverability via `/slash-command` autocomplete

**Use agent teams when:**
- Multiple workers need to communicate and coordinate
- The task benefits from parallel exploration with shared findings
- Different perspectives or hypotheses should be tested simultaneously

**Package as a plugin when:**
- The harness should be shared across projects or teams
- You want version-controlled, installable configuration
- The workflow is reusable beyond a single project