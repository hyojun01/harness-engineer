# File Templates

Copy and customize these templates for each component type.

## CLAUDE.md template

```markdown
# {Project Name}

## Purpose

{One sentence: what this agent does.}

## Core workflow

{Numbered steps of the main workflow. 3-7 steps. Each step is one sentence.}

## Architecture

{List subagents with one-line descriptions, prefixed with @.}

## Rules (always apply)

{5-10 bullet points. Only rules that would prevent mistakes if absent.}

## Output formats

{What the agent produces, what format, where it saves.}

## File conventions

{Where each type of working file goes: plans, sources, output, etc.}

## Context management

{Instructions for long tasks: where to save progress, how to resume.}
```

**Checklist:** Under 200 lines? Every line prevents a mistake? No duplicated info from skills/rules? Hard requirements moved to hooks?

---

## settings.json template

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Write",
      "Edit",
      "Bash(ls *)",
      "Bash(cat *)",
      "Bash(mkdir *)",
      "Bash(cp *)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(sudo *)"
    ]
  }
}
```

Add tool-specific permissions based on the task:
- Web research: add `"WebSearch"`, `"WebFetch"`
- Code execution: add `"Bash(python3 *)"`, `"Bash(node *)"` etc.
- File management: add `"Bash(mv *)"`, `"Bash(find *)"` etc.

---

## Subagent template (.claude/agents/{name}.md)

```markdown
---
name: {agent-name}
description: {When this agent should be invoked. Be specific about trigger conditions. Include exact phrases users or the orchestrator might use.}
tools: {Comma-separated list: Read, Write, Edit, Bash, Grep, Glob, WebSearch, WebFetch, Agent}
model: {inherit (default, matches main conversation), sonnet, opus, haiku, or a full model ID like claude-opus-4-7}
---

You are a {role description} specialist. Your job is to {primary objective}.

## Process

1. {First step}
2. {Second step}
3. {Continue as needed}

## Output format

{Specify exactly what the subagent should produce and where to save it.}

```
{Show the exact structure of expected output}
```

## Rules

- {Rule 1}
- {Rule 2}
- {Keep to 3-7 rules}
```

### All supported frontmatter fields (April 2026)

> **Source:** All fields in this table are documented in Anthropic's Claude Code subagent reference. Only `name` and `description` are required.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | **Required.** Unique identifier using lowercase letters and hyphens. |
| `description` | string | **Required.** When Claude should delegate to this agent. Be pushy with trigger phrases. |
| `tools` | list | Allowlist of tools the subagent can use. Inherits all tools if omitted. For `Agent`, use `Agent(worker, researcher)` to restrict which subagent types can be spawned (main-thread agents only). |
| `disallowedTools` | list | Denylist — tools removed from the inherited or specified list. Applied before `tools`. |
| `model` | string | `inherit` (default — uses main conversation's model), `sonnet`, `opus`, `haiku`, or a full model ID (e.g. `claude-opus-4-7`). `opusplan` is a valid `/model` CLI alias but is not explicitly documented as valid in subagent frontmatter — prefer `opus` there. |
| `permissionMode` | string | One of: `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, `plan`. Not supported in plugin subagents. If the parent uses `bypassPermissions`, `acceptEdits`, or `auto`, the parent's mode wins. |
| `maxTurns` | integer | Maximum number of agentic turns before the subagent stops. |
| `skills` | list | Skills to preload into the subagent's context at startup. The full skill content is injected. Subagents do NOT inherit skills from the parent conversation. |
| `mcpServers` | list | MCP server configurations. Each entry is a string (referencing an already-configured server) or an inline definition `- server-name: {type, command, args, ...}`. Not supported in plugin subagents. |
| `hooks` | object | Lifecycle hooks scoped to this subagent. Cleaned up when it finishes. All hook events supported. `Stop` in frontmatter is auto-converted to `SubagentStop` at runtime. Not supported in plugin subagents. |
| `memory` | string | Persistent memory scope: `user` (`~/.claude/agent-memory/<name>/`), `project` (`.claude/agent-memory/<name>/`, shareable via VCS), or `local` (`.claude/agent-memory-local/<name>/`, not VCS). Enables cross-session learning. |
| `background` | boolean | If `true`, always run as a background task. Default: `false`. |
| `effort` | string | Reasoning depth. One of `low`, `medium`, `high`, `xhigh`, `max`. Available levels depend on the model. Overrides session effort. |
| `isolation` | string | Set to `worktree` to run the subagent in a temporary git worktree (isolated copy of the repo). Cleaned up if no changes are made. |
| `color` | string | UI color. One of `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`. |
| `initialPrompt` | string | Auto-submitted as the first user turn when this agent runs as the main session agent via `claude --agent <name>` or the `agent` setting in `.claude/settings.json`. Commands and skills are processed. Does NOT fire when the agent is invoked as a subagent via the Agent tool. |
| `prompt` | string | System prompt. Used only in the CLI `--agents` JSON flag format, equivalent to the markdown body in file-based subagents. |

### Using subagents as the main session agent

> **Official:** You can run an entire session as a specific subagent instead of spawning it via the Agent tool:

```bash
# Replace the default Claude Code system prompt with the subagent's
claude --agent code-reviewer

# Or for a plugin-provided subagent:
claude --agent my-plugin:code-reviewer
```

To make it the default for a project, add to `.claude/settings.json`:

```json
{ "agent": "code-reviewer" }
```

The CLI flag overrides the setting. CLAUDE.md still loads normally. Frontmatter `initialPrompt` fires automatically as the first user turn.

### Invoking subagents from prompts

- **Natural language**: name the subagent in the prompt (`"Use the test-runner subagent to fix failing tests"`)
- **@-mention**: `@"code-reviewer (agent)"` guarantees that subagent runs for the next task. Plugin subagents appear as `@agent-<plugin-name>:<agent-name>`.

### Restricting which subagents the lead can spawn

When running a main-thread agent with `claude --agent`, use `Agent(...)` syntax in `tools` to limit spawning:

```yaml
tools: Agent(worker, researcher), Read, Bash   # allowlist
```

This is the correct way to force a "coordinator-only" lead — not a keyboard shortcut. Subagents cannot spawn other subagents, so this only matters for the main thread. To block specific agents globally, use `permissions.deny: ["Agent(Explore)"]` in `settings.json`.

### Security constraints for plugin subagents

> **Official:** Plugin subagents do NOT support `hooks`, `mcpServers`, or `permissionMode`. These fields are silently ignored when loaded from a plugin. This prevents third-party plugins from modifying permission enforcement or injecting hooks. Copy the agent into `.claude/agents/` or `~/.claude/agents/` if you need those fields.

### Subagent with hooks example

```markdown
---
name: db-reader
description: Execute read-only database queries safely.
tools: Bash
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/validate-readonly-query.sh"
---

You are a database query specialist. Only execute SELECT queries.
```

The PreToolUse hook validates that every Bash command is a read-only query before execution. Claude Code passes hook input as **JSON via stdin** to hook commands — the script should read from stdin and parse the JSON to inspect the command.

### Subagent configuration formats

> **Official:** Subagents can be defined in two ways:

**File-based** (`.claude/agents/{name}.md`): Markdown files with YAML frontmatter. This is the standard approach for Claude Code projects.

**JSON-based** (CLI `--agents` flag): JSON objects passed via the command line. Uses the `prompt` field instead of a markdown body. This is for programmatic or CI/CD usage.

These are two interfaces to the same underlying agent system. Do not mix them in the same project.

**Checklist:** Tools follow least privilege? Description includes trigger phrases? Output format is explicit? Hooks enforce hard constraints? Memory scope chosen intentionally?

---

## Evaluator agent template (.claude/agents/evaluator.md)

> **Interpretation:** The evaluator pattern is a recommended approach when self-evaluation fails — the generator consistently marks mediocre work as good. It is not required for every harness.

```markdown
---
name: evaluator
description: Quality-check completed work by interacting with the running output as a real user would. Invoke after the generator finishes a sprint or feature, or when the orchestrator needs independent QA. Trigger phrases include "evaluate", "QA", "review the build", "test the feature", "grade the output".
tools: Read, Grep, Glob, Bash, WebFetch
model: opus
mcpServers:
  - playwright:
      type: stdio
      command: npx
      args: ["-y", "@playwright/mcp@latest"]
---

You are a quality assurance specialist. Your job is to independently evaluate completed work against agreed-upon criteria, testing as a real user would.

## Process

1. Read the sprint contract or task specification
2. Start the application/artifact under test
3. Interact with it as a user: navigate, click, submit forms, probe edge cases
4. Grade each criterion against the hard threshold
5. Write a detailed findings report

## Grading criteria

For each criterion, score 1-10 and FAIL if below threshold:

- **Completeness** (threshold: 7): Does the implementation cover all specified features?
- **Functionality** (threshold: 8): Do features work correctly end-to-end?
- **Quality** (threshold: 6): Is the code/design clean and professional?
- **Edge cases** (threshold: 5): How does it handle unexpected inputs?

## Output format

Write findings to `qa-report-{sprint}.md`:
```
## Sprint {N} QA Report

### Overall: PASS / FAIL

### Criterion scores
| Criterion | Score | Threshold | Result |
|-----------|-------|-----------|--------|

### Issues found
| Feature | Expected | Actual | Severity |
|---------|----------|--------|----------|

### Recommendations
{Specific, actionable feedback for the generator}
```

## Rules

- Be skeptical. Do not approve mediocre work.
- Test the running application, not just the source code.
- If you catch yourself wanting to approve something that feels wrong, write down what feels wrong.
- Every FAIL must include specific, actionable feedback.
- Do not read or reference the generator's self-evaluation. Form your own assessment first.
```

**Checklist:** Criteria have hard thresholds? Evaluator uses runtime testing (Playwright, browser, API calls)? Skepticism is explicitly prompted?

> **Plugin warning:** If this evaluator is packaged in a plugin, `mcpServers` is silently ignored. Either move the evaluator to `.claude/agents/` or restrict it to shell-based testing (curl, headless browsers invoked from Bash).

---

## Skill template (.claude/skills/{name}/SKILL.md)

```markdown
---
name: {skill-name}
description: {What this skill does and when to use it. Be pushy: include specific trigger phrases, related concepts, and "even if they don't explicitly mention X" phrasing. 2-4 sentences max.}
---

# {Skill Name}

{One sentence: what this skill does.}

## Workflow

### Phase 1: {Name}
{Instructions for phase 1. Reference subagents with @name if they should be invoked.}

### Phase 2: {Name}
{Instructions for phase 2.}

{Continue as needed.}

## Error handling

- {What to do when X fails}
- {What to do when Y is missing}

## Scope calibration

| User signal | Scope | Expected behavior |
|------------|-------|-------------------|
| {Simple request} | {Light} | {Brief output} |
| {Standard request} | {Standard} | {Full output} |
| {Comprehensive request} | {Deep} | {Extensive output} |
```

> **Official:** Keep SKILL.md **under 500 lines**. Move detailed domain knowledge, large reference tables, and extended examples into `references/` files that are loaded on demand.

**Checklist:** Description is "pushy"? Under 500 lines? Detailed knowledge in references/ not in SKILL.md?

### Skill with bundled resources

```
skill-name/
├── SKILL.md              # Core instructions (under 500 lines)
├── scripts/
│   └── process.py        # Deterministic/repetitive tasks as code
├── references/
│   ├── domain-guide.md   # Detailed domain knowledge
│   └── schema.md         # Data structures, APIs, formats
└── assets/
    └── template.html     # Templates for output generation
```

Reference from SKILL.md: "Read `references/domain-guide.md` for detailed specifications."

---

## Command template (.claude/commands/{name}.md)

```markdown
---
name: {command-name}
description: {What the command does}
argument-hint: [{argument description}]
---

# /{command-name} Command

{One sentence: what this command triggers.}

## Steps

1. {What happens first}
2. {What happens next}
3. {Final step}

## Usage examples

```
/{command-name} {example argument 1}
/{command-name} {example argument 2}
```

## Notes

- {When to use this vs. alternatives}
- {Any prerequisites}
```

---

## Rule template (.claude/rules/{name}.md)

```markdown
---
globs: ["{pattern1}", "{pattern2}"]
---

# {Rule Name}

These rules apply to all files matching the glob patterns above.

## {Category 1}

- {Rule. Be specific and actionable.}
- {Rule.}

## {Category 2}

- {Rule.}
- {Rule.}
```

Common glob patterns:
- `["src/**/*.ts"]` — TypeScript files
- `["**/*.py"]` — Python files
- `["output/**"]` — Output directory
- `["docs/**", "*.md"]` — Documentation
- `["tests/**"]` — Test files
- `["*.json"]` — JSON config files

---

## Hooks template (.claude/settings.json or hooks/hooks.json for plugins)

### Hook input model

> **Official:** Hook commands receive context as **JSON via stdin**. Do NOT rely on environment variables like `$FILE`. Use `cat` to read stdin and `jq` (or equivalent) to parse the JSON structure. The JSON contains fields such as `tool_name`, `tool_input`, `session_id`, `cwd`, `permission_mode`, `hook_event_name`, and other event-specific data.

### Hook handler types (4 types, not 3)

> **Official:** Every hook entry has a `type` field. There are **four** handler types:

| Type | Purpose | When to use |
|------|---------|-------------|
| `command` | Run a shell command. Input on stdin, output via stdout + exit code. | Local validation, formatting, logging. The workhorse. |
| `http` | POST the JSON input to a URL. Response body uses the same JSON output schema. | CI/CD integration, external services, centralized policy. |
| `prompt` | Send a prompt to a Claude model for **single-turn yes/no evaluation**. Model returns a JSON decision. | Multi-criteria Stop hooks, quality gates that need reasoning. NOT for reminder injection. |
| `agent` | Spawn a subagent with access to Read/Grep/Glob-style tools to verify a condition before returning a decision. | Complex checks that need to inspect files. |

> **Common mistake to avoid:** `type: prompt` is NOT a way to inject reminder text into Claude's context. It sends a prompt to a fresh model for a yes/no decision. For context injection, use `type: command` and either (a) print text to stdout from `SessionStart` / `UserPromptSubmit` hooks, or (b) return `{"hookSpecificOutput": {"additionalContext": "..."}}` as JSON on stdout from events that support it.

### Common fields (all hook types)

| Field | Purpose |
|-------|---------|
| `type` | `"command"`, `"http"`, `"prompt"`, or `"agent"` |
| `if` | Permission-rule syntax filter — the hook only runs if the tool call matches. Examples: `"Bash(git *)"`, `"Edit(*.ts)"`. Only evaluated on tool events (PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, PermissionDenied). **Prefer `if` over reparsing stdin in the script** — it avoids spawning the process when filter fails. |
| `timeout` | Seconds before cancel. Defaults: 600 (command), 30 (prompt/http), 60 (agent) |
| `statusMessage` | Custom spinner message shown while hook runs |
| `once` | `true` runs only once per session then removes itself (skills only, not agents) |

Command hooks also accept `async` (run in background without blocking) and `asyncRewake` (background + wake Claude on exit 2).

### Matcher evaluation rules

> **Official:** How the `matcher` string is evaluated depends on its contents:

| Matcher value | Evaluated as | Example |
|---------------|--------------|---------|
| `"*"`, `""`, or omitted | Matches everything | fires on every occurrence |
| Only letters/digits/`_`/`|` | Exact string, or `|`-separated exact list | `Bash`, `Edit|Write` |
| Contains any other character | **JavaScript regular expression** | `^Notebook`, `mcp__memory__.*`, `mcp__.*__write.*` |

The matcher filters a different field per event (tool name for tool events, session source for `SessionStart`, compaction trigger for `PreCompact`, agent type for `SubagentStart`, etc.). Some events (`UserPromptSubmit`, `Stop`, `TeammateIdle`, `TaskCreated`, `TaskCompleted`, `WorktreeCreate`, `WorktreeRemove`, `CwdChanged`) do not support matchers — any `matcher` field is silently ignored.

### Hook exit codes and JSON output

> **Official — exit code basics:**
> - `0` — Allow the action to proceed. Stdout may be parsed as JSON for structured control (SessionStart/UserPromptSubmit also add stdout as context).
> - `1` — Non-blocking error. Claude Code logs the failure and proceeds.
> - `2` — Blocking error (for events that support blocking). Stderr is fed back to Claude or the user.
> - Any other non-zero — Non-blocking error.

> **Official — exit code 2 behavior is event-specific.** Not every event blocks on exit 2:

| Blocks on exit 2 | Does NOT block (stderr shown but action proceeds) |
|------------------|--------------------------------------------------|
| `PreToolUse` | `PostToolUse` |
| `PermissionRequest` | `PostToolUseFailure` |
| `UserPromptSubmit` | `PermissionDenied` (exit code ignored) |
| `Stop`, `SubagentStop` | `Notification` |
| `TeammateIdle` | `SubagentStart`, `SessionStart`, `SessionEnd` |
| `TaskCreated`, `TaskCompleted` | `CwdChanged`, `FileChanged`, `PostCompact` |
| `ConfigChange` (except `policy_settings`) | `StopFailure` (output ignored), `InstructionsLoaded` |
| `PreCompact` | `WorktreeRemove` |
| `Elicitation`, `ElicitationResult` | — |
| `WorktreeCreate` (any non-zero fails creation) | — |

Beyond exit codes, hooks can return a JSON object on stdout for richer control (only processed when exit is 0). Universal fields: `continue: false` stops Claude entirely, `systemMessage` shows a warning to the user, `suppressOutput: true` hides the stdout from debug logs. Event-specific decision schemas are documented per event in Anthropic's hooks reference.

### Modern PreToolUse decision format

> **Official — April 2026:** PreToolUse's top-level `decision: "block"` is **deprecated**. Use `hookSpecificOutput.permissionDecision` instead, which supports four outcomes: `allow`, `deny`, `ask`, `defer`.

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Database writes are not allowed outside migrations"
  }
}
```

Extras: `updatedInput` modifies the tool's input before execution, `additionalContext` injects context for Claude. `permissionDecision: "defer"` is for headless SDK callers (`claude -p`) — the tool is paused and can resume with `--resume` (v2.1.89+).

### Hooks in settings.json (project-level)

```json
{
  "permissions": {
    "allow": ["Read", "Write", "Edit"]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "if": "Bash(rm -rf *)",
            "command": "echo 'Destructive rm -rf blocked' >&2; exit 2"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "input=$(cat); file=$(echo \"$input\" | jq -r '.tool_input.file_path // empty'); if [ -n \"$file\" ]; then ./scripts/format.sh \"$file\"; fi"
          }
        ]
      }
    ],
    "PostToolUseFailure": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -n '{hookSpecificOutput:{hookEventName:\"PostToolUseFailure\",additionalContext:\"The previous command failed. Check the error output and try a different approach.\"}}'"
          }
        ]
      }
    ],
    "PermissionDenied": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "input=$(cat); echo \"$input\" >> /tmp/denied-actions.log"
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/validate-subagent-output.sh"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Read progress.json before starting. Work on ONE task at a time. Do not modify migration files.'"
          }
        ]
      }
    ]
  }
}
```

> **Note on reminders that must survive compaction:** `SessionStart` fires on `source=compact` after auto-compaction, so a `SessionStart` hook with `matcher: "compact"` (or the broader `"startup|resume|clear|compact"`) is the correct place to re-inject must-survive reminders. `PreCompact` only supports blocking compaction, not context injection. `PostCompact` has no decision control at all.

### All hook events reference (April 2026)

> **Source:** All events below are documented in Anthropic's official hooks reference. The event surface is stable but may grow; consult the Claude Code hooks docs for the latest schemas.

**Session lifecycle:**

| Event | Fires | Can block? | Notes |
|-------|-------|------------|-------|
| `SessionStart` | Session begins/resumes | No | Matches on `startup\|resume\|clear\|compact`. Stdout becomes context. |
| `SessionEnd` | Session terminates | No | Matches on exit reason. Default timeout 1.5s. |
| `InstructionsLoaded` | A CLAUDE.md or `.claude/rules/*.md` loads into context | No | Matches on load reason (`session_start`, `nested_traversal`, `path_glob_match`, `include`, `compact`). Useful for audit logging. |

**User input:**

| Event | Fires | Can block? | Notes |
|-------|-------|------------|-------|
| `UserPromptSubmit` | User submits prompt, before Claude processes | Yes | Stdout becomes context. Can inject `additionalContext` or set `sessionTitle`. |

**Tool lifecycle:**

| Event | Fires | Can block? | Notes |
|-------|-------|------------|-------|
| `PreToolUse` | Before tool runs | Yes | Use `hookSpecificOutput.permissionDecision` (allow/deny/ask/defer). Supports `updatedInput` and `additionalContext`. |
| `PostToolUse` | After tool succeeds | No | Exit 2 doesn't block (tool already ran) — only shows stderr to Claude. |
| `PostToolUseFailure` | After tool fails | No | Receives `error` and optional `is_interrupt`. |
| `PermissionRequest` | Permission dialog about to show | Yes | Use `hookSpecificOutput.decision.behavior` (allow/deny). Can return `updatedPermissions`. |
| `PermissionDenied` | Auto-mode classifier denied a call | No | Return `hookSpecificOutput.retry: true` to let the model retry. |

**Agent & team lifecycle:**

| Event | Fires | Can block? | Notes |
|-------|-------|------------|-------|
| `SubagentStart` | Subagent spawned via Agent tool | No | Matches on agent type. Can inject `additionalContext` into the subagent. |
| `SubagentStop` | Subagent finishes | Yes | Same schema as `Stop`. Frontmatter `Stop` is auto-converted to `SubagentStop`. |
| `Stop` | Main agent finishes responding | Yes | `decision: "block"` + `reason` forces Claude to continue. Check `stop_hook_active` to avoid infinite loops. |
| `StopFailure` | Turn ends due to API error | No | Output and exit code ignored. Matches on error type (`rate_limit`, `authentication_failed`, etc.). |
| `TaskCreated` | A task is being created (TaskCreate tool) | Yes | Exit 2 rolls back creation with feedback. |
| `TaskCompleted` | A task is being marked completed | Yes | Exit 2 prevents completion with feedback. Enforce quality gates here. |
| `TeammateIdle` | An agent team teammate is about to go idle | Yes | Exit 2 keeps teammate working. |

**Compaction & config:**

| Event | Fires | Can block? | Notes |
|-------|-------|------------|-------|
| `PreCompact` | Before compaction | Yes | Matches on `manual\|auto`. Blocking auto-compaction at context limit surfaces the underlying API error. |
| `PostCompact` | After compaction completes | No | Receives `compact_summary`. No decision control. |
| `ConfigChange` | Settings or skill file changed during session | Yes (except `policy_settings`) | Matches on source (`user_settings`, `project_settings`, etc.). |
| `Notification` | Claude Code sends a notification | No | Matches on notification type. Can inject `additionalContext`. |

**Filesystem & worktrees:**

| Event | Fires | Can block? | Notes |
|-------|-------|------------|-------|
| `CwdChanged` | Working directory changes (e.g., Claude `cd`s) | No | Can persist env vars via `CLAUDE_ENV_FILE`. Pairs with direnv. |
| `FileChanged` | A watched file changes on disk | No | `matcher` lists literal filenames (e.g., `.envrc\|.env`). Regex watches literal filenames, not patterns. |
| `WorktreeCreate` | `--worktree` or `isolation: "worktree"` | Yes (any non-zero) | Replaces default git behavior. Hook must print absolute worktree path on stdout. |
| `WorktreeRemove` | Worktree being removed | No | Receives `worktree_path`. |

**MCP elicitation:**

| Event | Fires | Can block? | Notes |
|-------|-------|------------|-------|
| `Elicitation` | MCP server requests user input | Yes (accept/decline/cancel) | Matches on MCP server name. Can respond programmatically, skipping the dialog. |
| `ElicitationResult` | User has responded to an MCP elicitation | Yes | Matches on MCP server name. Last chance to modify the response. |

### Hooks in plugin format (hooks/hooks.json)

```json
{
  "description": "Quality and security hooks",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/cleanup.sh"
          }
        ]
      }
    ]
  }
}
```

### Common hook patterns

**✅ Auto-format after every edit (declarative filter via `if`):**
```json
{
  "matcher": "Edit|Write",
  "hooks": [{ "type": "command", "if": "Edit(*.ts)|Edit(*.tsx)|Write(*.ts)|Write(*.tsx)",
              "command": "input=$(cat); file=$(echo \"$input\" | jq -r '.tool_input.file_path // empty'); prettier --write \"$file\" 2>/dev/null" }]
}
```

**✅ Block dangerous commands (modern PreToolUse JSON decision):**
```json
{
  "matcher": "Bash",
  "hooks": [{ "type": "command", "command": "input=$(cat); cmd=$(echo \"$input\" | jq -r '.tool_input.command // empty'); if echo \"$cmd\" | grep -qE 'DROP TABLE|TRUNCATE'; then jq -n '{hookSpecificOutput:{hookEventName:\"PreToolUse\",permissionDecision:\"deny\",permissionDecisionReason:\"Destructive SQL blocked\"}}'; else exit 0; fi" }]
}
```

**✅ Re-inject context after compaction (use SessionStart, NOT PreCompact):**
```json
{
  "matcher": "compact",
  "hooks": [{ "type": "command",
              "command": "echo 'Current task: implement auth flow. Do not modify migration files.'" }]
}
```

**✅ Prompt-based quality gate (correct use of type: prompt):**
```json
{
  "matcher": "",
  "hooks": [{ "type": "prompt",
              "prompt": "Given the last assistant message: $ARGUMENTS\n\nDecide if the work is complete. Respond with JSON: {\"decision\": \"block\" | \"allow\", \"reason\": \"...\"}" }]
}
```

**✅ Match all MCP tools from a server (regex matcher):**
```json
{
  "matcher": "mcp__memory__.*",
  "hooks": [{ "type": "command", "command": "echo 'Memory op initiated' >> ~/mcp-operations.log" }]
}
```

**Checklist:** Hard requirements use hooks, not CLAUDE.md? Exit codes correct for the event (check blocks-on-exit-2 table)? Hook scripts read stdin JSON (not `$FILE`)? Plugin hooks use `${CLAUDE_PLUGIN_ROOT}`? `type: "prompt"` only used for yes/no model decisions, not reminder injection? Reminders placed in `SessionStart` with appropriate matcher?

---

## Plugin manifest template (.claude-plugin/plugin.json)

```json
{
  "name": "{plugin-name}",
  "description": "{What this plugin provides. 1-2 sentences.}",
  "version": "1.0.0",
  "author": {
    "name": "{Your Name or Organization}"
  }
}
```

Optional fields: `homepage`, `repository`, `license`.

### Full plugin directory structure

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json           # Manifest (required)
├── skills/                    # Agent skills (optional)
│   └── skill-name/
│       ├── SKILL.md
│       └── references/
├── agents/                    # Subagents (optional)
│   └── agent-name.md
├── commands/                  # Slash commands (optional)
│   └── command-name.md
├── hooks/                     # Event hooks (optional)
│   └── hooks.json
├── .mcp.json                  # MCP server configs (optional)
└── README.md                  # Documentation
```

**Checklist:** Manifest has name, description, version? Skills are namespaced? Hooks reference `${CLAUDE_PLUGIN_ROOT}` for file paths?

---

## Progress tracking template

```json
{
  "project": "{project-name}",
  "status": "idle",
  "current_task": "",
  "tasks_total": 0,
  "tasks_completed": 0,
  "completed": [],
  "remaining": [],
  "notes": "",
  "started_at": "",
  "updated_at": ""
}
```

**Rules to include in CLAUDE.md or relevant skill:**
- "Update {progress-file} after completing each task."
- "Do NOT remove items from the completed list."
- "Set status to 'complete' only after all tasks pass verification."

---

## Feature list template (for long-running agents)

```json
[
  {
    "id": "F001",
    "category": "core",
    "description": "User can create a new account with email and password",
    "priority": 1,
    "passes": false,
    "verification_steps": [
      "Navigate to /signup",
      "Fill in email and password",
      "Submit the form",
      "Verify account is created",
      "Verify can log in with new credentials"
    ]
  }
]
```

**Rules:**
- Use strongly-worded instructions: "It is unacceptable to remove or edit tests because this could lead to missing or buggy functionality."
- Only change the `passes` field; never remove or rewrite feature descriptions.
- JSON format so the model treats it as code and modifies it carefully.

---

## README template

```markdown
# {Project Name}

{One sentence description.}

## Quick start

```bash
# 1. Copy to your project
cp -r {project-name}/ ~/your-project/

# 2. Start Claude Code
cd ~/your-project && claude

# 3. Run the main workflow
> /{main-command} [argument]
```

## Structure

| Component | Location | Role |
|-----------|----------|------|
| CLAUDE.md | `./CLAUDE.md` | Project rules (loaded every session) |
| Subagents | `.claude/agents/` | Specialized agents ({count}) |
| Skills | `.claude/skills/` | On-demand workflows ({count}) |
| Commands | `.claude/commands/` | Entry points ({count}) |
| Rules | `.claude/rules/` | Auto-applied rules ({count}) |
| Hooks | `.claude/settings.json` | Deterministic enforcement ({count}) |

## Architecture

{Brief description of how components connect. Reference docs/architecture.md for details.}
```