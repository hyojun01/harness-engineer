# Harness Examples

Complete worked examples showing different complexity levels and patterns.

> **Legend:** Examples marked ✅ are minimal working examples safe to copy directly. Examples marked 📐 are conceptual pseudocode illustrating a pattern — adapt before use.

---

## Example 1: Simple — Code review agent

A single-agent harness with no subagents. Just CLAUDE.md + rules + one command.

### When to use this pattern
- Task fits in one context window
- No specialized phases requiring different tools
- Linear workflow

### Structure
```
code-reviewer/
├── CLAUDE.md
├── .claude/
│   ├── settings.json
│   ├── commands/
│   │   └── review.md
│   └── rules/
│       ├── typescript-rules.md
│       └── testing-rules.md
└── output/
```

### ✅ CLAUDE.md (48 lines)
```markdown
# Code Review Agent

## Purpose
Review code for quality, security, and adherence to team standards.

## Workflow
1. Read the file(s) to review
2. Check against the applicable rules (auto-loaded by file type)
3. Write a review report to output/review-{filename}.md
4. Summarize findings with severity: critical / warning / suggestion

## Rules
- Never modify the source files. Read-only analysis.
- Always check for: security vulnerabilities, error handling, type safety, test coverage.
- Rate overall code quality: A (ship it) / B (minor fixes) / C (needs rework) / D (rewrite).
- If no issues found, say so clearly. Do not invent problems.

## Output format
Markdown report with: summary, findings by severity, and an overall grade.
```

### ✅ Command: .claude/commands/review.md
```markdown
---
name: review
description: Review code files for quality and security
argument-hint: [file or directory path]
---
# /review Command
1. Read the specified file(s)
2. Apply all relevant rules
3. Produce a review report in output/
```

---

## Example 2: Medium — Content pipeline agent

Two subagents + one skill + two commands + hooks for formatting. Handles research and writing as separate phases.

### When to use this pattern
- Task has 2-3 distinct phases
- Different phases benefit from tool isolation
- Moderate complexity

### Structure
```
content-pipeline/
├── CLAUDE.md
├── content-progress.json
├── .claude/
│   ├── settings.json
│   ├── agents/
│   │   ├── researcher.md
│   │   └── writer.md
│   ├── skills/
│   │   └── brand-voice/
│   │       ├── SKILL.md
│   │       └── references/
│   │           └── style-guide.md
│   ├── commands/
│   │   ├── article.md
│   │   └── brief.md
│   └── rules/
│       └── output-standards.md
├── research/
├── drafts/
└── output/
```

### Key design decisions
- **researcher** subagent gets WebSearch + WebFetch + Read (no Write to main project). Saves notes to research/ directory.
- **writer** subagent gets Read + Write + Edit (no web tools). Reads research notes, writes drafts.
- **brand-voice** skill loads the style guide only when writing phase begins.
- Progress tracked in JSON at project root.
- **Hooks** auto-run markdown formatter after every Write to output/. Hook scripts receive tool input as JSON via stdin.

### ✅ Subagent: .claude/agents/researcher.md
```markdown
---
name: researcher
description: Search the web and gather source material for content creation. Invoke when research notes are needed before writing, or when the user asks to "research", "find sources", or "gather information" on a topic.
tools: Read, Write, Grep, Glob, WebSearch, WebFetch
model: sonnet
---
You are a research specialist. Gather information from authoritative sources and produce structured research notes.

## Process
1. Receive the topic and angle from the orchestrator
2. Execute 3-8 web searches with short, specific queries
3. Fetch full pages for the 3-5 most relevant results
4. Extract key facts, quotes, and data points
5. Save structured notes to research/topic-{slug}.md

## Output format
Markdown file with: key findings, source list with URLs, and identified gaps.

## Rules
- Paraphrase everything. Never copy text from sources.
- Record URL, title, and date for every source.
- Flag when evidence is thin or conflicting.
- Discard low-quality sources (SEO farms, forums, undated content).
```

### ✅ Hooks in settings.json

> **Official:** Hook commands receive tool context as **JSON via stdin**, not via environment variables like `$FILE`. Parse stdin with `jq` or similar to extract file paths and other details.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "input=$(cat); file=$(echo \"$input\" | jq -r '.tool_input.file_path // empty'); if [ -n \"$file\" ] && echo \"$file\" | grep -q 'output/'; then prettier --write \"$file\" 2>/dev/null; fi"
          }
        ]
      }
    ]
  }
}
```

---

## Example 3: Complex — Full software development harness

Four subagents (including evaluator) + two skills + three commands + hooks + multiple rules. The pattern Anthropic uses for long-running coding agents.

### When to use this pattern
- Task spans multiple sessions/context windows
- Complex software project with multiple subsystems
- Quality verification is critical and self-evaluation fails

### Structure
```
dev-harness/
├── CLAUDE.md
├── feature-list.json
├── dev-progress.json
├── init.sh
├── .claude/
│   ├── settings.json
│   ├── agents/
│   │   ├── planner.md           # Expands spec from short prompt
│   │   ├── implementer.md       # Writes code in sprints
│   │   ├── evaluator.md         # QA via Playwright (independent)
│   │   └── reviewer.md          # Code quality check
│   ├── skills/
│   │   ├── feature-workflow/
│   │   │   ├── SKILL.md
│   │   │   └── scripts/
│   │   │       └── run-tests.sh
│   │   └── deploy-check/
│   │       └── SKILL.md
│   ├── commands/
│   │   ├── implement.md         # Work on the next feature
│   │   ├── verify.md            # Run full verification
│   │   └── status.md            # Show current progress
│   └── rules/
│       ├── code-style.md        # globs: ["src/**"]
│       ├── test-conventions.md  # globs: ["tests/**"]
│       └── commit-rules.md      # globs: ["**"]
├── src/
└── tests/
```

### Key pattern: Initializer + Worker

The first session uses a different prompt than subsequent sessions:

**First session (initializer):**
1. Analyze the high-level requirement
2. Expand into a comprehensive feature-list.json (mark all as `"passes": false`)
3. Write init.sh (sets up dev environment)
4. Create initial directory structure
5. Make first git commit

**Subsequent sessions (worker):**
1. Run `pwd`, read dev-progress.json and git log
2. Run init.sh to start dev server
3. Run basic smoke test to verify app is not broken
4. Pick the highest-priority unfinished feature
5. Implement and verify it
6. Update feature-list.json and commit

### Evaluator agent pattern

> **Interpretation:** The three-agent architecture (planner / generator / evaluator) is a **recommended pattern** described by Anthropic, not a mandatory structure. Adapt it to your task's complexity and quality requirements.

The evaluator operates independently from the implementer:

1. **Sprint contract negotiation:** Before coding, the implementer proposes what it will build and how success is verified. The evaluator reviews and agrees. Communication via files.
2. **Independent QA:** After implementation, the evaluator uses Playwright to interact with the running application — clicking through features, testing API endpoints, probing database states.
3. **Grading with thresholds:** Each criterion has a hard score threshold. If any falls below, the sprint fails and the implementer gets detailed feedback.
4. **Skepticism prompt:** The evaluator is explicitly told to be skeptical and not approve mediocre work.

### ✅ Evaluator: .claude/agents/evaluator.md
```markdown
---
name: evaluator
description: Independently test and grade completed features by interacting with the running application. Invoke after implementer finishes a feature, or when the orchestrator asks to "QA", "evaluate", "test the build", or "grade the sprint".
tools: Read, Grep, Glob, Bash
model: opus
---
You are an independent QA specialist. Test the running application as a real user would.

## Process
1. Read the sprint contract from sprint-contract-{n}.md
2. Start the application via init.sh
3. For each test criterion in the contract:
   a. Interact with the running application
   b. Verify the expected behavior occurs
   c. Score the criterion 1-10
4. Write findings to qa-report-{n}.md

## Grading criteria
- Feature completeness (threshold: 7)
- Functionality (threshold: 8)
- Visual design (threshold: 6)
- Code quality (threshold: 6)

If ANY criterion falls below its threshold, the sprint FAILS.

## Rules
- Be skeptical. If something feels wrong, it is wrong.
- Test end-to-end as a user, not by reading source code.
- Every FAIL must include the specific file, line, and fix suggestion.
- Do not read the implementer's self-evaluation before forming your own.
- Distinguish between bugs (FAIL) and polish items (note but pass).
```

### ✅ Hooks in settings.json

> **Official:** Hook exit codes: `0` = allow, `1` = warning (logged, not blocked), `2` = block the action. The `matcher` field targets **tool names** (e.g., `"Bash"`, `"Write"`, `"Edit|Write"`). Use conditional logic inside the hook script for finer command-level filtering. Hook commands receive input as **JSON via stdin**.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "input=$(cat); cmd=$(echo \"$input\" | jq -r '.tool_input.command // empty'); if echo \"$cmd\" | grep -qE '^rm\\s+-rf\\s'; then echo 'Destructive rm -rf blocked' >&2; exit 2; fi; exit 0"
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
            "command": "input=$(cat); file=$(echo \"$input\" | jq -r '.tool_input.file_path // empty'); if [ -n \"$file\" ] && echo \"$file\" | grep -qE '\\.(ts|tsx|js|jsx)$'; then npx eslint --fix \"$file\" 2>/dev/null; fi"
          }
        ]
      }
    ],
    "PostToolUseFailure": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "The previous command failed. Check the error output and try a different approach."
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
            "prompt": "Reminder: read dev-progress.json and feature-list.json before starting work. Work on ONE feature at a time. Commit after each feature."
          }
        ]
      }
    ]
  }
}
```

### ✅ Feature list format (JSON, not Markdown)
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

---

## Example 4: Plugin — Reusable research workflow

Package a research workflow as a shareable plugin with skills, subagents, and hooks.

### When to use this pattern
- The workflow is reusable across projects
- Multiple team members need the same configuration
- You want version control and easy installation

### Structure
```
research-workflow/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── deep-research/
│       ├── SKILL.md
│       └── references/
│           └── search-strategies.md
├── agents/
│   ├── searcher.md
│   └── synthesizer.md
├── commands/
│   └── research.md
├── hooks/
│   └── hooks.json
└── README.md
```

### ✅ Plugin manifest: .claude-plugin/plugin.json
```json
{
  "name": "research-workflow",
  "description": "Multi-agent research pipeline with search, synthesis, and citation tracking",
  "version": "1.0.0",
  "author": {
    "name": "Your Team"
  }
}
```

### ✅ Hooks: hooks/hooks.json

> **Official:** Plugin hooks must use `${CLAUDE_PLUGIN_ROOT}` for file paths. Hook scripts receive input as JSON via stdin.

```json
{
  "description": "Citation and output validation hooks",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate-citations.sh"
          }
        ]
      }
    ]
  }
}
```

### Installation
```bash
# From local directory
/plugin install --dir ./research-workflow

# From marketplace (after publishing)
/plugin install your-team/research-workflow@marketplace-name
```

### Usage
```
> /research-workflow:research "quantum computing advances in 2026"
```

Skills are namespaced: the `deep-research` skill becomes `research-workflow:deep-research`.

---

## Complexity calibration guide

| Task type | CLAUDE.md | Subagents | Evaluator | Skills | Commands | Rules | Hooks |
|-----------|-----------|-----------|-----------|--------|----------|-------|-------|
| Simple script/utility | Yes (short) | 0 | No | 0 | 0-1 | 0-1 | 0 |
| Research + report | Yes | 2-4 | Optional | 1-2 | 1-2 | 1-3 | 0-1 |
| Content pipeline | Yes | 2-3 | Optional | 1-2 | 2-3 | 1-2 | 1-2 |
| Full web app | Yes | 3-5 | Yes | 2-3 | 2-4 | 3-5 | 2-4 |
| Data pipeline | Yes | 2-3 | Optional | 1-2 | 1-2 | 2-3 | 1-2 |
| DevOps automation | Yes | 2-4 | Optional | 2-3 | 3-5 | 2-4 | 2-3 |
| Reusable workflow | Plugin | 1-3 | Optional | 1-2 | 1-3 | 0-2 | 1-2 |

**Rule of thumb:** Start with just CLAUDE.md. Add components only when you can articulate WHY the current structure fails without them. After every model upgrade, audit components: would the model now handle this on its own?