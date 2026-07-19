---
name: agi-loop
description: Start the continuous AGI self-improvement loop. The agent will find problems, generate requirements, fix issues, and optimize the codebase autonomously.
when_to_use: Use when user types /agi-loop or asks for autonomous self-improvement and fixing.
short_description: Start autonomous AGI loop
argument_hint: (optional) maximum number of iterations
allowed_tools: [run_terminal_cmd, read_file, list_dir, grep, search_replace, write_file, todo_write]
user_invocable: true
disable_model_invocation: false
enabled: true
---

# AGI Loop Skill

Triggers the fully autonomous Continuous Improvement Loop.
This skill strings together health checks, requirement generation, and auto-fixing into a zero-token-waste engine.

## Execution Sequence

### Step 1: Health & Needs Assessment (Discover)
Run token-efficient scans:
1. `git status -s` (is the tree clean?)
2. Run project test suite.
3. Run project linter.
4. Read `agents/logs/error-patterns.json`.
5. Read `agents/requirements/REQUIREMENTS.md`.

### Step 2: Queue Building
Based on the assessment, call `todo_write` with the prioritized queue:
- **P0**: Fix build/test failures.
- **P1**: Fix recurring runtime errors (from logs).
- **P2**: Implement missing tests (from REQUIREMENTS).
- **P3**: Address technical debt (from REQUIREMENTS).

### Step 3: Autonomous Resolution
For the top item in the queue:
1. Use `grep` to locate the exact code.
2. Edit with `search_replace`.
3. Verify by running the specific test or linter.
4. If it fails, read the error, self-correct, and retry.
5. If it succeeds, mark it `completed` in `todo_write`.

### Step 4: Loop or Terminate
- If there are more pending items in the `todo` list, proceed to the next one.
- If the queue is empty, run a final `/health-check` to ensure the project is green.
- Conclude the turn, reporting the total number of issues fixed.

## Token Optimization Rule
- Do NOT output large chunks of code or thought processes to the user while looping.
- Keep terminal output summarized. Only look at the `grep "error"` or tail of logs.
- The user only wants to see the final summary: "I found 3 broken tests and 1 missing requirement. I fixed them all. Project is 100% healthy."
