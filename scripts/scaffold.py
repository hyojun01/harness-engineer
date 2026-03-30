#!/usr/bin/env python3
"""
Scaffold a Claude Code harness directory structure.

Usage:
    python3 scaffold.py <project_name> <output_dir> [options]

Options:
    --agents a1,a2          Comma-separated agent names
    --skills s1,s2          Comma-separated skill names
    --commands c1,c2        Comma-separated command names
    --rules r1,r2           Comma-separated rule names
    --hooks                 Add hooks template to settings.json
    --evaluator             Add an evaluator agent for independent QA
    --plugin                Package as a plugin (adds manifest)

Examples:
    python3 scaffold.py research-agent ./output --agents planner,researcher,writer --skills deep-research --commands research --rules citations
    python3 scaffold.py code-pipeline ./output --agents implementer --evaluator --hooks --rules code-style,testing
    python3 scaffold.py team-tools ./output --plugin --skills code-review --hooks
"""

import argparse
import json
import os
from pathlib import Path


def create_dir(path: str):
    """Create directory and add .gitkeep if empty."""
    os.makedirs(path, exist_ok=True)


def write_file(path: str, content: str):
    """Write content to file, creating parent dirs if needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Path(path).write_text(content, encoding="utf-8")


def scaffold(args):
    base = os.path.join(args.output_dir, args.project_name)

    if args.plugin:
        # Plugin structure
        create_dir(os.path.join(base, ".claude-plugin"))
        create_dir(os.path.join(base, "skills"))
        create_dir(os.path.join(base, "agents"))
        create_dir(os.path.join(base, "commands"))
        create_dir(os.path.join(base, "hooks"))

        # Plugin manifest
        write_file(os.path.join(base, ".claude-plugin", "plugin.json"), json.dumps({
            "name": args.project_name,
            "description": "{What this plugin provides. 1-2 sentences.}",
            "version": "1.0.0",
            "author": {
                "name": "{Your Name}"
            }
        }, indent=2))
    else:
        # Standard harness structure
        create_dir(os.path.join(base, ".claude", "agents"))
        create_dir(os.path.join(base, ".claude", "skills"))
        create_dir(os.path.join(base, ".claude", "commands"))
        create_dir(os.path.join(base, ".claude", "rules"))

    # Working directories
    for d in ["output"]:
        create_dir(os.path.join(base, d))
        write_file(os.path.join(base, d, ".gitkeep"), "")

    # Determine paths based on plugin vs standard
    def component_path(*parts):
        if args.plugin:
            return os.path.join(base, *parts)
        return os.path.join(base, ".claude", *parts)

    # CLAUDE.md (only for standard harness, not plugins)
    if not args.plugin:
        agents_section = '\n'.join(f'- `@{a}` — {{description}}' for a in args.agents) if args.agents else '- No subagents configured'
        if args.evaluator:
            agents_section += '\n- `@evaluator` — Independent QA via runtime testing'

        write_file(os.path.join(base, "CLAUDE.md"), f"""# {args.project_name.replace('-', ' ').title()}

## Purpose

{{Describe what this agent does in one sentence.}}

## Core workflow

1. {{Step 1}}
2. {{Step 2}}
3. {{Step 3}}

## Architecture

{agents_section}

## Rules (always apply)

- {{Rule 1}}
- {{Rule 2}}

## Output formats

- Default: Markdown in `output/` directory

## File conventions

- Output → `output/`
- Progress → `progress.json`

## Context management

Update `progress.json` after each completed task. Use subagents to isolate long explorations.
""")

    # settings.json with optional hooks
    settings = {
        "permissions": {
            "allow": ["Read", "Write", "Edit", "Bash(ls *)", "Bash(cat *)", "Bash(mkdir *)", "Bash(cp *)"],
            "deny": ["Bash(rm -rf *)", "Bash(sudo *)"]
        }
    }

    if args.hooks and not args.plugin:
        settings["hooks"] = {
            "PostToolUse": [
                {
                    "matcher": "Edit|Write",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "echo 'File modified: $FILE'"
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
                            "prompt": "Reminder: read progress.json before starting work. Work on ONE task at a time."
                        }
                    ]
                }
            ]
        }

    if not args.plugin:
        write_file(os.path.join(base, ".claude", "settings.json"), json.dumps(settings, indent=2))

    # Plugin hooks file
    if args.hooks and args.plugin:
        write_file(os.path.join(base, "hooks", "hooks.json"), json.dumps({
            "description": f"Hooks for {args.project_name}",
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "Edit|Write",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
                            }
                        ]
                    }
                ]
            }
        }, indent=2))
        create_dir(os.path.join(base, "scripts"))
        write_file(os.path.join(base, "scripts", "validate.sh"), """#!/bin/bash
# Validation hook - customize this script
# Exit 0 = allow, Exit 1 = block, Exit 2 = ask Claude to reconsider
input=$(cat)
echo "Validating: $FILE"
exit 0
""")

    # Progress tracker (standard harness only)
    if not args.plugin:
        write_file(os.path.join(base, "progress.json"), json.dumps({
            "project": args.project_name,
            "status": "idle",
            "current_task": "",
            "tasks_total": 0,
            "tasks_completed": 0,
            "completed": [],
            "remaining": [],
            "notes": "",
            "started_at": "",
            "updated_at": ""
        }, indent=2))

    # Agent stubs
    if args.agents:
        for agent in args.agents:
            write_file(os.path.join(component_path("agents"), f"{agent}.md"), f"""---
name: {agent}
description: {{When this agent should be invoked. Include specific trigger phrases.}}
tools: Read, Write, Grep, Glob
model: sonnet
---

You are a {agent.replace('-', ' ')} specialist.

## Process

1. {{Step 1}}
2. {{Step 2}}
3. {{Step 3}}

## Output format

{{Specify output format and file location.}}

## Rules

- {{Rule 1}}
- {{Rule 2}}
""")

    # Evaluator agent
    if args.evaluator:
        write_file(os.path.join(component_path("agents"), "evaluator.md"), """---
name: evaluator
description: Independently test and grade completed work by interacting with the running output. Invoke after a feature is implemented, or when QA, evaluation, or testing is needed.
tools: Read, Grep, Glob, Bash
model: opus
---

You are an independent QA specialist. Test the running application as a real user would.

## Process

1. Read the task specification or sprint contract
2. Start the application under test
3. Interact with it as a user: navigate, click, submit, probe edge cases
4. Grade each criterion against the hard threshold
5. Write detailed findings to qa-report.md

## Grading criteria

- Feature completeness (threshold: 7/10)
- Functionality (threshold: 8/10)
- Quality (threshold: 6/10)
- Edge cases (threshold: 5/10)

If ANY criterion falls below threshold, the sprint FAILS.

## Rules

- Be skeptical. Do not approve mediocre work.
- Test the running application, not just source code.
- Every FAIL must include specific, actionable feedback.
- Do not read the generator's self-evaluation before forming your own.
""")

    # Skill stubs
    if args.skills:
        for skill in args.skills:
            skill_dir = os.path.join(component_path("skills"), skill)
            create_dir(os.path.join(skill_dir, "references"))
            create_dir(os.path.join(skill_dir, "scripts"))
            write_file(os.path.join(skill_dir, "SKILL.md"), f"""---
name: {skill}
description: {{What this skill does. Be pushy: list trigger phrases, related concepts. 2-4 sentences.}}
---

# {skill.replace('-', ' ').title()}

{{One sentence purpose.}}

## Workflow

### Phase 1: {{Name}}
{{Instructions.}}

### Phase 2: {{Name}}
{{Instructions.}}

## Error handling

- {{Fallback behavior}}
""")

    # Command stubs
    if args.commands:
        for cmd in args.commands:
            write_file(os.path.join(component_path("commands"), f"{cmd}.md"), f"""---
name: {cmd}
description: {{What this command does}}
argument-hint: [{{argument}}]
---

# /{cmd} Command

{{One sentence description.}}

## Steps

1. {{Step 1}}
2. {{Step 2}}
3. {{Step 3}}

## Usage

```
/{cmd} {{example}}
```
""")

    # Rule stubs (standard harness only)
    if args.rules and not args.plugin:
        for rule in args.rules:
            write_file(os.path.join(base, ".claude", "rules", f"{rule}.md"), f"""---
globs: ["{{pattern}}"]
---

# {rule.replace('-', ' ').title()}

## {{Category}}

- {{Rule 1}}
- {{Rule 2}}
""")

    # README
    write_file(os.path.join(base, "README.md"), f"""# {args.project_name.replace('-', ' ').title()}

{{One sentence description.}}

## Quick start

```bash
{"# Install as plugin" + chr(10) + f"/plugin install --dir ./{args.project_name}" if args.plugin else f"cp -r {args.project_name}/ ~/your-project/" + chr(10) + "cd ~/your-project && claude"}
```

## Structure

{"Plugin" if args.plugin else "Harness"} with {len(args.agents) if args.agents else 0} agents{" + evaluator" if args.evaluator else ""}, {len(args.skills) if args.skills else 0} skills, {len(args.commands) if args.commands else 0} commands{", hooks" if args.hooks else ""}.
""")

    # Summary
    components = {
        "agents": (len(args.agents) if args.agents else 0) + (1 if args.evaluator else 0),
        "skills": len(args.skills) if args.skills else 0,
        "commands": len(args.commands) if args.commands else 0,
        "rules": len(args.rules) if args.rules else 0,
        "hooks": "yes" if args.hooks else "no",
        "evaluator": "yes" if args.evaluator else "no",
        "plugin": "yes" if args.plugin else "no",
    }

    print(f"Scaffolded: {base}")
    print(f"  Type:      {'Plugin' if args.plugin else 'Standard harness'}")
    print(f"  Agents:    {components['agents']}")
    print(f"  Skills:    {components['skills']}")
    print(f"  Commands:  {components['commands']}")
    print(f"  Rules:     {components['rules']}")
    print(f"  Hooks:     {components['hooks']}")
    print(f"  Evaluator: {components['evaluator']}")
    print(f"\nNext: Fill in the {{placeholder}} values in each file.")


def main():
    parser = argparse.ArgumentParser(description="Scaffold a Claude Code harness")
    parser.add_argument("project_name", help="Project name (kebab-case)")
    parser.add_argument("output_dir", help="Output directory")
    parser.add_argument("--agents", help="Comma-separated agent names", default="")
    parser.add_argument("--skills", help="Comma-separated skill names", default="")
    parser.add_argument("--commands", help="Comma-separated command names", default="")
    parser.add_argument("--rules", help="Comma-separated rule names", default="")
    parser.add_argument("--hooks", help="Add hooks template", action="store_true")
    parser.add_argument("--evaluator", help="Add evaluator agent for independent QA", action="store_true")
    parser.add_argument("--plugin", help="Package as a plugin", action="store_true")
    args = parser.parse_args()

    # Parse comma-separated lists
    args.agents = [a.strip() for a in args.agents.split(",") if a.strip()] if args.agents else []
    args.skills = [s.strip() for s in args.skills.split(",") if s.strip()] if args.skills else []
    args.commands = [c.strip() for c in args.commands.split(",") if c.strip()] if args.commands else []
    args.rules = [r.strip() for r in args.rules.split(",") if r.strip()] if args.rules else []

    scaffold(args)


if __name__ == "__main__":
    main()
