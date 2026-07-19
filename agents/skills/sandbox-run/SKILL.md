---
name: sandbox-run
description: Execute a risky or untested command in a throwaway copy of the workspace and report the outcome before touching the real project
when_to_use: Use before running any state-changing, destructive-looking, or unverified command; also used by the critic agent to demand simulation evidence
short_description: Simulate a command safely first
argument_hint: the shell command to test
allowed_tools: [read_file, run_terminal_cmd]
user_invocable: true
disable_model_invocation: false
enabled: true
---

# Sandbox-Run (Imagination Layer)

Hypothesis-testing before real-world action: copy → run → observe → decide.

## Usage
```
python agents/hooks/bin/sandbox_runner.py --cmd "<command>"
python agents/hooks/bin/sandbox_runner.py --cmd "<command>" --include src --include tests
python agents/hooks/bin/sandbox_runner.py --cmd "<command>" --keep    # inspect sandbox afterwards
```

## Decision Protocol
1. Run the command in the sandbox.
2. Verdict `ok` → safe to apply the same change to the real workspace.
3. Verdict `failed` → read stdout/stderr in the report, fix the approach, re-simulate.
4. Verdict `blocked` → the command matches a destructive pattern; find an alternative. NEVER bypass the guard.

## Rules
- Anything irreversible (migrations, deletions, bulk rewrites) MUST be sandbox-tested first.
- Attach the sandbox JSON report as evidence when asking the critic for approval.
- Sandboxes are auto-deleted unless `--keep` is passed; never leave stale sandboxes around.
