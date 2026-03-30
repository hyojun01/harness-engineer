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
tools: {Comma-separated list: Read, Write, Edit, Bash, Grep, Glob, WebSearch, WebFetch}
model: {sonnet or opus. Use sonnet for most tasks; opus for complex synthesis/writing.}
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

**Checklist:** Tools follow least privilege? Description includes trigger phrases? Output format is explicit?

---

## Evaluator agent template (.claude/agents/evaluator.md)

Use when self-evaluation fails — the generator consistently marks mediocre work as good.

```markdown
---
name: evaluator
description: Quality-check completed work by interacting with the running output as a real user would. Invoke after the generator finishes a sprint or feature, or when the orchestrator needs independent QA. Trigger phrases include "evaluate", "QA", "review the build", "test the feature", "grade the output".
tools: Read, Grep, Glob, Bash, WebFetch
model: opus
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

**Checklist:** Description is "pushy"? Under 5,000 words? Detailed knowledge in references/ not here?

### Skill with bundled resources

```
skill-name/
├── SKILL.md              # Core instructions (under 5,000 words)
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

### Hooks in settings.json (project-level)

```json
{
  "permissions": {
    "allow": ["Read", "Write", "Edit"]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npm run lint --fix $FILE"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/format.sh"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Reminder: the current task is {task}. Modified files: {files}. Do not modify migration files."
          }
        ]
      }
    ]
  }
}
```

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

**Auto-format after every edit:**
```json
{
  "matcher": "Edit|Write",
  "hooks": [{ "type": "command", "command": "prettier --write $FILE" }]
}
```

**Security scan before file writes:**
```json
{
  "matcher": "Write",
  "hooks": [{ "type": "command", "command": "./scripts/security-scan.sh" }]
}
```

**Re-inject context after compaction:**
```json
{
  "matcher": "",
  "hooks": [{ "type": "prompt", "prompt": "Current task: implement auth flow. Do not modify migration files." }]
}
```

**Checklist:** Hard requirements use hooks, not CLAUDE.md? Exit codes are correct (0=allow, 1=block, 2=reconsider)? Plugin hooks use `${CLAUDE_PLUGIN_ROOT}`?

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
