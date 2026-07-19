---
name: debug
description: Investigate and fix a bug, error, or test failure systematically
when_to_use: Use when there's a bug, crash, error message, test failure, or unexpected behavior
short_description: Debug and fix issues
argument_hint: error message or description of the bug
allowed_tools: [read_file, grep, list_dir, search_replace, run_terminal_cmd]
user_invocable: true
disable_model_invocation: false
enabled: true
---

# Debug Skill

Investigates bugs using the scientific method.

## Investigation Protocol
1. **Reproduce**: run the failing test/command to confirm the issue
2. **Read error**: parse the full error message (type, message, stack trace, line)
3. **Locate**: find the source code at the error location
4. **Trace**: follow the call chain from entry to failure
5. **Check**: look at recent git changes (`git log --oneline -10`, `git diff HEAD~1`)

## Diagnosis
- Form ONE specific hypothesis about root cause
- Test the hypothesis with a minimal case
- Don't fix until you're confident you understand the cause

## Fix
- Apply the minimal correct fix
- Do NOT fix symptoms — fix the root cause
- If the fix is complex, add a comment explaining WHY

## Verification
- Run the original failing test/command — must pass now
- Run the full test suite — must not regress
- If a test didn't exist for this bug: add a regression test

## Output
```
Root cause: [precise description]
Fix: [what was changed and why]
Verification: [test command + output showing it passes]
```
