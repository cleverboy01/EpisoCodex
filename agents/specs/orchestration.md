# Prompt Queue & Task Orchestration Spec
# Source: xai-prompt-queue/src/, xai-grok-shell/src/agent/ (xai-org/grok-build)

## Prompt Queue Architecture
The prompt queue manages concurrent user inputs and agent turns.
User-visible prompts are queued; synthetic inputs (auto-wake, nudges) are invisible.

## Queue Entry Structure
```json
{
  "id": "prompt-uuid",
  "version": 3,              // monotonic, bumped on in-place edit
  "owner": "client-id",      // who enqueued it (never overwritten)
  "lastEditor": "client-id", // most recent editor
  "kind": "prompt",          // display kind
  "text": "fix the bug",     // plain text for queue display
  "position": 0              // 0-based position among pending
}
```

## Queue State Broadcast (x.ai/queue/changed)
```json
{
  "sessionId": "sess-abc",
  "entries": [...],                    // pending (not yet running) prompts
  "runningPromptId": "prompt-uuid"     // currently executing (null if idle)
}
```

## Queue Behavior Rules
1. **FIFO within session**: prompts run in order they were queued.
2. **In-place edit**: user can edit a queued prompt before it runs (version++).
3. **Cancellation**: pending prompts can be cancelled before they start.
4. **Single active turn**: only one prompt runs at a time per session.
5. **Synthetic inputs**: auto-wake and system nudges bypass the queue, invisible to user.

## Blocking Wait Pattern (for subagents)
When parent blocks on a subagent (`block=true`):
```
parent.blocking_wait_depth++
    └─► prompts sent during wait → routed to send-now (not queued)
        (prevents deadlock when user sends input during a blocking wait)
parent.blocking_wait_depth--
```

## Auto-Wake Pattern
When a background subagent completes:
```
subagent finishes
    └─► surface_completion=true? → inject synthetic prompt
            └─► goal_loop_active? → SUPPRESS (don't interrupt /goal)
                    └─► else: wake parent with completion summary
```

## Goal Mode (/goal) Orchestration
Long-running autonomous loop:
```
/goal "build a REST API for user management"
    │
    ├─► Goal registered in GoalState
    │
    ├─► Turn loop:
    │       ├─► Model plans next step
    │       ├─► Executes tools (edits, tests, shell)
    │       ├─► Updates goal progress via goal_update tool
    │       └─► Spawns subagents for parallelizable work
    │
    └─► Terminates when:
            ├─► Model calls goal_complete tool
            ├─► User cancels (/cancel)
            └─► Turn limit reached
```

## Plan Mode Orchestration
Prevents any edits until plan is approved:
```
enter_plan tool called
    └─► Agent outputs plan (no file edits allowed)
        └─► User reviews and approves/modifies
            └─► exit_plan tool called
                └─► Agent proceeds with implementation
```

## Multi-Agent Pipeline Pattern
```
Orchestrator Agent (parent)
    │
    ├─► spawn researcher_subagent(task="research API patterns")
    │       background=true (non-blocking)
    │
    ├─► spawn tester_subagent(task="write unit tests for auth module")
    │       background=true (non-blocking)
    │
    ├─► [continues other work]
    │
    ├─► block_wait(subagent_ids=[researcher, tester])
    │       └─► resume when both complete
    │
    └─► synthesis turn (combine results, write implementation)
```

## Turn Limit & Token Budget
```
max_turns: configurable per session/subagent
  → enforced by session actor
  → subagent inherits from parent (resolved independently)

auto_compact_threshold: 85% of context window
  → triggers compaction: history summary replaces raw history
  → PreCompact/PostCompact hooks fire around it

inference_idle_timeout_secs: per session
  → session terminates if model API is unresponsive for N seconds
```
