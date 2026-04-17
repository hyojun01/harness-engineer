# Context Engineering Best Practices

Updated April 2026 from Anthropic's "Effective context engineering for AI agents" blog (Sep 2025), "Harness design for long-running application development" (Mar 2026), and related documentation.

> **Source labels used in this document:**
> - **Official** — Directly from Anthropic's documentation or blog posts
> - **Interpretation** — Inferred from Anthropic's examples or engineering context
> - **Optional Practice** — Community convention or author recommendation

Context engineering is the set of strategies for curating and maintaining the optimal set of tokens during LLM inference. It is the natural progression of prompt engineering: while prompt engineering focuses on how to write effective prompts, context engineering addresses the broader question of what configuration of context is most likely to generate the desired behavior.

## The golden rule

> **Official**

Find the *smallest possible* set of high-signal tokens that maximize the likelihood of the desired outcome.

More information often makes agents worse, not better. Every token competes with every other token for the model's attention.

## Context rot and the attention budget

> **Official**

LLMs, like humans, lose focus as context grows. Studies show that as token count increases, the model's ability to accurately recall information from that context decreases — this is called **context rot**.

The root cause is architectural: transformer attention creates n² pairwise relationships for n tokens. As context grows, each relationship gets stretched thinner.

Treat context as a **finite resource with diminishing marginal returns**. The model has an "attention budget" — every token added depletes it.

## Progressive disclosure (most important pattern)

> **Official**

Show just enough information to help the agent decide what to do next, then reveal more details as needed.

### Three-tier loading

| Tier | What loads | When | Size budget |
|------|-----------|------|-------------|
| 1. Metadata | Skill name + description | Always (system prompt) | 1-2 sentences each |
| 2. Instructions | SKILL.md body | When skill is triggered | Under 500 lines |
| 3. Resources | references/, scripts/, assets/ | During execution, on demand | Effectively unbounded |

### Why it matters
A project with 50 skills does not consume 50x tokens. Claude scans metadata, identifies the 1-2 relevant skills, and loads only what is necessary.

## Hybrid retrieval strategy

> **Official**

The most effective agents combine upfront context with just-in-time exploration:

**Upfront loading (fast, deterministic):**
- CLAUDE.md is naively dropped into context at session start
- Critical rules and commands are always available
- Progress tracking files are read immediately

**Just-in-time exploration (flexible, agent-driven):**
- Maintain lightweight identifiers (file paths, stored queries, web links)
- Use tools like `glob`, `grep`, `find` to navigate and retrieve data on demand
- Write targeted queries to analyze data without loading full datasets

This mirrors human cognition: we don't memorize entire corpuses but use indexing systems to retrieve information on demand.

**Tradeoff:** Runtime exploration is slower than pre-computed retrieval. The decision boundary for the right level of autonomy depends on the task. As models improve, lean toward letting models act autonomously with progressively less human curation.

## CLAUDE.md design rules

> **Official** (content criteria, what belongs/doesn't belong); **Optional Practice** (line count recommendations)

### Content criteria
For every line, ask: "Would Claude make a mistake without this?" If Claude already does something correctly on its own, the instruction is noise.

### What belongs in CLAUDE.md
- Build/test/run commands
- Coding standards and conventions Claude would not infer
- Architecture decisions that affect how code should be written
- File naming conventions
- Forbidden patterns (things Claude tends to do wrong)
- Stack versions and critical dependencies

### What does NOT belong in CLAUDE.md
- Codebase overviews (agents discover structure on their own)
- Directory listings (agents can use `ls` and `find`)
- Generic best practices Claude already knows
- Detailed domain knowledge (move to skills)
- File-specific rules (move to rules/)
- Hard requirements that must execute 100% of the time (move to hooks)
- Hotfix-style patches for one-off behavior (degrades overall performance)

### Format guidelines
- Under 200 lines total (community best practice: under 60 lines for focused projects)
- Under 150 effective instructions (after system prompt takes ~50)
- Use imperative form: "Use pytest for testing" not "You should use pytest for testing"
- Group related instructions under clear headings
- No redundancy — say it once, in the right place

### The right altitude

> **Official**

System prompts should be specific enough to guide behavior effectively, yet flexible enough to provide strong heuristics. Two failure modes:
- **Too rigid:** Hardcoding complex brittle logic creates fragility and maintenance complexity
- **Too vague:** High-level guidance that fails to give concrete signals or falsely assumes shared context

## Skill description design

> **Official**

The description is the single most important field. It determines whether the skill triggers.

### Problem: Under-triggering
Current models tend to NOT use skills when they should. Combat this by making descriptions "pushy."

### Bad description
```
How to create Excel reports.
```

### Good description
```
Create, format, and analyze Excel spreadsheets. Use this skill whenever the user mentions spreadsheets, Excel, .xlsx, CSV data analysis, pivot tables, charts, data formatting, or wants to organize any tabular data, even if they don't explicitly mention Excel.
```

### Rules for descriptions
- Include exact trigger phrases users would say
- List related concepts that should also trigger the skill
- Use "even if they don't explicitly ask for X" phrasing
- Keep it under 3-4 sentences (it is always in context)
- Include both what the skill does AND when to use it

## Skill body (SKILL.md) design

> **Official** (structure and approach); **Optional Practice** (specific format recommendations)

### Write for another Claude instance
The skill will be consumed by a different Claude instance. Include:
- Procedural knowledge that is not obvious
- Domain-specific details
- Decision frameworks
- Output format specifications
- Concrete examples (positive and negative)

### Imperative voice
Write "Do X" or "To accomplish X, do Y" — not "You should do X."

### Size guideline

> **Official:** Keep SKILL.md **under 500 lines**. Move detailed domain knowledge, large reference tables, and extended examples into `references/` files that are loaded on demand.

### Structure
1. Brief purpose statement
2. Step-by-step workflow
3. Rules and constraints
4. Output format specification
5. Examples (if helpful)

### Negative examples matter
"Do NOT use bullet points in the report body" is as valuable as positive instructions. Negative examples define boundaries.

## Subagent context design

> **Official**

### System prompt
The subagent's system prompt replaces the default Claude Code system prompt entirely. Subagents receive only this prompt plus basic environment details (no full Claude Code system prompt). It should include:
- Role definition
- Specific process to follow
- Output format
- Rules and constraints

### Information transfer
The only channel from parent to subagent is the Agent tool's prompt string. Include:
- All file paths the subagent needs
- Relevant error messages or decisions
- Enough context to work independently

### Tool restriction
Apply least privilege. Two mechanisms exist:

- `tools:` is an **allowlist**. Omitting it inherits all tools.
- `disallowedTools:` is a **denylist** applied before `tools`. Use it to inherit most tools but drop a few.

Common presets:
- Read-only agents: `tools: Read, Grep, Glob`
- Research agents: `tools: Read, Grep, Glob, WebFetch, WebSearch`
- Write agents: `tools: Read, Write, Edit, Bash`
- Coordinator agents (main-thread only, via `claude --agent`): `tools: Agent(worker_a, worker_b), Read, Bash` — the `Agent(type)` syntax is an allowlist of subagent types the coordinator may spawn

### Skills and MCP preloading
- `skills:` injects full skill content into the subagent's context at startup. Subagents do NOT inherit skills from the parent conversation.
- `mcpServers:` scopes MCP servers to the subagent — tool descriptions don't consume parent context. Not supported in plugin subagents.

### Persistent memory
`memory: user | project | local` gives the subagent a memory directory (`~/.claude/agent-memory/<n>/`, `.claude/agent-memory/<n>/`, or `.claude/agent-memory-local/<n>/`). Claude Code auto-injects the first 200 lines / 25KB of `MEMORY.md` into the subagent's system prompt, and auto-enables Read/Write/Edit tools for the memory directory. Prompt the subagent to consult and update its memory explicitly for best results.

## Context strategies for long-horizon tasks

### Compaction

> **Official**

Summarize conversation contents and reinitiate with the summary. The art lies in what to keep vs. discard:
- Maximize recall first (capture every relevant piece)
- Then iterate to improve precision (eliminate superfluous content)
- Safest first step: clear tool call results deep in history (tool result clearing)
- Preserve: architectural decisions, unresolved bugs, implementation details
- Discard: redundant tool outputs, verbose logs, resolved issues

### Claude Agent SDK auto-compaction

> **Official**

The Claude Agent SDK handles compaction automatically for SDK-based harnesses. It monitors token usage and compacts when approaching limits. Note: autocompact includes a thrash loop detector — if context refills to the limit immediately after compacting three times in a row, it stops with an actionable error.

### Compaction vs. context reset (model-specific)

> **Official**

**Context anxiety** varies by model:
- **Sonnet 4.5:** Strong context anxiety. Compaction alone NOT sufficient → context resets essential.
- **Opus 4.5:** Mild context anxiety. Compaction sufficient → context resets can be dropped.
- **Opus 4.6:** Negligible context anxiety. SDK auto-compaction handles everything → 2+ hour continuous sessions possible.

Choose compaction strategy based on the target model.

### Structured note-taking (agentic memory)

> **Official**

The agent regularly writes notes persisted outside the context window (to-do lists, NOTES.md, progress files). These get pulled back into context at later times.

Benefits:
- Persistent memory with minimal overhead
- Tracks progress across complex tasks
- Maintains dependencies that would be lost across tool calls
- Enables multi-hour strategies (as demonstrated by Claude playing Pokémon)

### Sub-agent architectures for context management

> **Official**

The main agent coordinates with a high-level plan while subagents perform deep work. Each subagent explores extensively (10,000+ tokens) but returns only a condensed summary (1,000-2,000 tokens).

Choose based on task characteristics:
- **Compaction** — Best for tasks requiring extensive back-and-forth
- **Note-taking** — Best for iterative development with clear milestones
- **Multi-agent** — Best for complex research/analysis where parallel exploration pays dividends

## Rules design

> **Official**

### Glob patterns
Rules activate only when Claude works on files matching the glob pattern.

```yaml
---
globs: ["src/**/*.ts", "src/**/*.tsx"]
---
```

### When to use rules vs. CLAUDE.md vs. hooks
- **Rule:** Applies to specific file types only → rules/
- **Universal:** Applies to all work in the project → CLAUDE.md
- **Occasional:** Applies to specific workflows → skills/
- **Mandatory:** Must execute 100% of the time → hooks

### Common patterns
- `["src/**"]` — source code rules
- `["tests/**"]` — testing conventions
- `["docs/**"]` — documentation standards
- `["output/**"]` — output formatting rules
- `["**/*.py"]` — language-specific rules

## State tracking design

> **Official**

### Use JSON, not Markdown
Anthropic's experiments found models treat JSON as code and modify it more carefully. Markdown files get inappropriately rewritten, overwritten, or edited.

### Minimal viable state
```json
{
  "status": "in-progress",
  "current_task": "description",
  "completed": ["task1", "task2"],
  "remaining": ["task3", "task4"],
  "notes": "any context the next session needs",
  "updated_at": "ISO timestamp"
}
```

### Rules for state files
- Use strongly-worded instructions: "Do NOT remove or modify completed items"
- Keep the schema flat and simple
- Include a timestamp so the next session knows how fresh the data is
- Place at project root for easy discovery

## Anti-patterns to avoid

> Sources vary per item. Items without labels are **Interpretation**.

1. **Stuffing everything into CLAUDE.md** — Use skills, rules, and hooks instead (**Official**)
2. **Auto-generating CLAUDE.md** — Hand-crafted files outperform LLM-generated ones (**Official**)
3. **Too many MCP tools** — Each tool description consumes instruction budget; audit regularly (**Official**)
4. **No verification step** — Always include a verify/test phase in the workflow (**Official**)
5. **Vague skill descriptions** — Causes under-triggering; be pushy and specific (**Official**)
6. **Duplicating instructions** — Say something once, in the right place
7. **Markdown for state tracking** — Use JSON (**Official**)
8. **Skipping negative examples** — They are as important as positive ones
9. **Deep nesting in skills** — Keep SKILL.md focused; use references/ for depth
10. **Ignoring the instruction budget** — ~150-200 max; every line costs (**Official**)
11. **Using CLAUDE.md for hard requirements** — CLAUDE.md is ~80% compliance; use hooks for 100% (**Official**)
12. **Never auditing the harness** — Components encode model assumptions that go stale; re-test after model upgrades (**Official**)
13. **Self-evaluation without separation** — Models praise their own work; separate generator from evaluator for quality-critical tasks (**Official**)
14. **Compaction without testing** — Overly aggressive compaction loses subtle but critical context; tune carefully on complex agent traces
15. **Using hooks/mcpServers/permissionMode in plugin subagents** — Not supported; will fail silently or error (**Official**)
16. **Hardcoding model-specific harness behavior** — Context resets needed for Sonnet 4.5 are unnecessary overhead on Opus 4.6; document which model the harness targets
17. **Agent teams lead implementing tasks itself** — The lead will pick up work instead of delegating. Correct fixes: restrict its tools declaratively with `tools: Agent(worker_a, worker_b), Read, Bash` when running via `claude --agent`, or steer it with natural language ("Wait for your teammates to complete their tasks before proceeding"). **There is no Shift+Tab "Delegate mode" in Claude Code** — that shortcut does not exist. (**Official**)
18. **Ignoring subagent memory scope** — Without persistent memory, subagents lose insights across conversations; set memory scope intentionally