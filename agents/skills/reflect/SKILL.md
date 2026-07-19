---
name: reflect
description: Run a post-mortem after a task and store lessons in the episodic experience ledger; recall past lessons before starting new work
when_to_use: Use at the end of any significant task (success OR failure), and at the start of a task to recall relevant past experience
short_description: Post-mortem reflection and recall
argument_hint: task summary, or a query to recall past lessons
allowed_tools: [read_file, run_terminal_cmd]
user_invocable: true
disable_model_invocation: false
enabled: true
---

# Reflect (Episodic Memory)

Prevents "session amnesia": lessons survive across sessions in a local SQLite ledger.

## Recall (start of task)
```
python agents/hooks/bin/episodic_memory.py query "<current task keywords>" --limit 5
```
Read the returned lessons FIRST. Do not repeat a documented past mistake.

## Post-Mortem (end of task)
Answer three questions, then store the result:
1. What went wrong (or right)?
2. How was it solved?
3. What must never be repeated?

```
python agents/hooks/bin/episodic_memory.py store \
  --task "<one-line task summary>" \
  --outcome success|failure|partial \
  --lessons "<answers to the three questions, concise>" \
  --tags "<comma,separated,topics>"
```

## Rules
- Keep lessons under 5 lines — they are recalled into future contexts; noise is expensive.
- Store failures too: failed approaches are the most valuable entries.
- Session decisions are auto-captured at SessionEnd by `hooks/bin/episodic_memory.py` (hook mode).
