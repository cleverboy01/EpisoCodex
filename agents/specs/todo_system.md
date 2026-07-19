# Todo System Spec
# Source: xai-grok-shell/src/agent/system_reminder.rs (xai-org/grok-build)

## What is the Todo System?
A built-in task tracking mechanism that persists across tool calls within a session.
The model is EXPECTED to use `todo_write` for multi-step tasks.
The harness monitors todo usage and reminds the model to update it.

## Todo Item States
```
pending    → not started yet
in-progress → currently working on (only ONE at a time)
completed  → done
deferred   → moved to later (with reason)
```

## todo_write Protocol
```json
{
  "todos": [
    { "id": "1", "text": "Read auth module", "state": "completed" },
    { "id": "2", "text": "Write unit tests for login handler", "state": "in-progress" },
    { "id": "3", "text": "Update documentation", "state": "pending" }
  ]
}
```

## When to Use todo_write

### ALWAYS use for tasks that have ≥ 3 steps:
```
User: "Refactor the auth module to use JWT"
Agent: [calls todo_write with step breakdown]
  1. Read current auth implementation
  2. Design JWT token structure
  3. Update login handler
  4. Update middleware
  5. Update tests
  6. Verify all tests pass
```

### Update as you work:
- When starting a step: mark it `in-progress`
- When done with a step: mark it `completed`
- When you can't complete a step: mark it `deferred` with reason

## TodoNudge System Reminder
The harness fires this reminder when todo_write hasn't been called in 3+ turns:
```
<system-reminder>
Consider updating your task list if you have multi-step work in progress.
</system-reminder>
```
**React by calling todo_write immediately.**

## TodoGate System Reminder
When enabled, fires at turn-end if todos are still pending:
```
<system-reminder>
You have incomplete todo items. Continue working until all are done or deferred.
</system-reminder>
```
**React by continuing work on the next pending item.**

## Benefits
1. **Visibility**: User can see your progress in the IDE sidebar
2. **Self-accountability**: Prevents stopping mid-task
3. **Recovery**: If context is compacted, todo list survives as persistent state
4. **Orchestration**: Parent agents can read subagent todo state

## Anti-patterns
- ❌ Doing a 10-step refactor with NO todo list (invisible progress)
- ❌ Marking all items complete at once (signals the list wasn't used)
- ❌ Never updating state (stale list is misleading)
- ❌ Using free-form text when structure is needed
