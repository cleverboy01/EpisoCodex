---
name: proactive-scan
description: Autonomously scan the codebase for technical debt, likely bugs, outdated dependencies and missing tests, then generate a prioritized task queue
when_to_use: Use when the system is idle, on a schedule, or when the user asks the workspace to find its own work
short_description: Find work autonomously
argument_hint: optional focus area (e.g. "tests", "deps", "security")
allowed_tools: [read_file, grep, list_dir, run_terminal_cmd, todo_write]
user_invocable: true
disable_model_invocation: false
enabled: true
---

# Proactive-Scan (Autonomous Goal Generation)

Turns the system from reactive to self-directed: it defines its own tasks.

## Scan Order (cheapest signals first)
1. `agents/logs/error-patterns.json` — recurring runtime failures
2. `python agents/hooks/bin/episodic_memory.py query "recurring failure"` — known dead-ends
3. `/health-check` — tests, lint, build
4. `grep -rn "TODO\|FIXME\|HACK" --include="*.py"` — declared debt
5. Dependency manifests — stale or vulnerable pins
6. Source files without matching test files — coverage gaps

## Task Queue Output
For each finding produce:
```
Goal: <one sentence>
Evidence: <file:line or log entry>
Priority: build > tests > security > debt > optimization
Risk: safe-auto | needs-approval
```
Write the queue via `todo_write`, max 10 tasks per cycle.

## Autonomy Boundaries
- `safe-auto` (docs, tests, formatting): may run through the autonomous-agi loop, sandbox-first.
- `needs-approval` (API changes, deletions, upgrades): present to the user, do NOT execute.
- Every task must pass critic review before execution.
