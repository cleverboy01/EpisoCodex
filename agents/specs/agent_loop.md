# Agent Loop Spec
# Source: xai-grok-shell/src/agent/ (xai-org/grok-build)

## Overview
The agent loop is the core reasoning cycle. It runs turns iteratively until:
- The task is complete (model stops calling tools).
- A turn limit is reached.
- The user cancels.
- An unrecoverable error occurs.

## Turn Structure
```
User Prompt
    └─► [System Prompt + Context Build]
            └─► Model Sampling (API call to xAI/OpenAI-compat)
                    └─► Response Parser
                            ├─► Text chunk → stream to UI
                            └─► Tool call → Tool Executor
                                    └─► Tool Result → append to context
                                            └─► [Next Turn or Stop]
```

## Key States
- `New`: fresh session, no history
- `Forked`: child inherits parent history as `<background_context>`
- `Resumed`: child inherits a previously completed peer subagent's transcript

## Self-Correction Pattern
```
attempt = 0
while attempt < 3:
    result = execute_tool(tool_call)
    if result.is_error():
        attempt += 1
        context.append(error_message)
        # Model sees error and self-corrects on next turn
    else:
        break
```

## Context Compaction
When context approaches window limit, compaction fires:
- `PreCompact` hook fires → user scripts can inject summaries.
- Model summarizes conversation history.
- Summary replaces raw history to free tokens.
- `PostCompact` hook fires.
- Threshold: configurable via `auto_compact_threshold_percent` (default ~85%).

## Chat Modes
- **Normal**: standard conversational turns.
- **Plan Mode**: agent enters planning phase, no code edits until plan approved.
- **Goal Mode** (`/goal`): long-running autonomous loop with progress tracking.
- **Headless** (`-p`): non-interactive, single prompt, outputs to stdout.

## Checkpoint / Rollback
- Before any destructive operation: `git stash` or file snapshot.
- On failure: rollback via `xai-grok-workspace` checkpoint system.
- Checkpoint format: blake3 hash of workspace path → scoped storage.
