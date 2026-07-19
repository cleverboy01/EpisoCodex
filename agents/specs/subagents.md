# Subagents Spec
# Source: xai-grok-shell/src/agent/subagent/ (xai-org/grok-build)

## What are Subagents?
Subagents are child sessions spawned by the parent agent to handle parallel or isolated tasks.
Each subagent is a full agent instance with its own session, model, and turn loop.

## When to Spawn a Subagent
- Task can run in parallel with other work
- Task needs filesystem isolation (worktree mode)
- Task is complex enough to warrant a dedicated context window
- Task needs a different model or persona

## Subagent Lifecycle
```
Parent Agent
    └─► spawn_subagent(request)
            ├─► PendingSubagent (initializing)
            │       ├─► resolve model config
            │       ├─► create worktree (if isolation=worktree)
            │       └─► spawn session actor
            ├─► SubagentTracker (active/running)
            │       ├─► child runs its own turn loop
            │       ├─► parent polls via signals_handle
            │       └─► SubagentStart hook fires
            └─► CompletedSubagent (finished)
                    ├─► output stored in output.json
                    ├─► SubagentStop hook fires
                    └─► result available for TaskOutputTool polling
```

## Coordinator State Machine
```
pending{}   → promote to active{}  → move to completed{}
             (session ready)         (session exits)
                                     (max: 1024 entries, LRU eviction)
```

## What Subagents INHERIT from Parent
- Filesystem (same LocalFs or AcpSessionFs)
- Terminal runner (same PTY backend)
- Hunk tracker (edits attributed to parent's tracker)
- Environment variables (.envrc + color settings)
- Hooks (PreToolUse gates apply to child too)
- MCP server pool (snapshot at spawn time)
- Memory config (access to same memory store)
- Skills (parent's discovered skills + config)

## What Subagents DO NOT Inherit
- Model (resolved independently, pins > parent inheritance)
- Turn limits (resolved from child's own config)
- Auto-compact threshold (resolved for child's model)

## Model Resolution Priority (highest → lowest)
```
1. config.toml [subagents.models].{agent_name}   → explicit per-agent pin
2. AgentDefinition.model = Override(id)           → skill/agent-definition pin
3. Parent's live sampling config (inherited)      → default
```
Unknown model IDs are ignored (warning logged), resolution falls through.

## Isolation Modes
- `isolation=none` (default): shares parent's working directory
- `isolation=worktree`: creates a fresh git worktree, deleted on completion (or snapshotted to a durable ref if `subagent_worktree_snapshot=true`)

## Blocking vs Background
- `run_in_background=false` (default): parent waits for subagent result
- `run_in_background=true`: parent continues; uses `TaskOutputTool` to poll

## Surface Completion
- `surface_completion=true`: completed result injected as synthetic auto-wake prompt
- Suppressed if parent is in active goal loop (`goal_loop_active=true`)

## Resume Pattern
A subagent can resume from a previously completed peer:
- Child inherits source's transcript, tool state, and model
- System prompt and context freshly rendered from current agent definition

## Subagent Roles & Personas
Configure in `config.toml`:
```toml
[subagents.models]
researcher = "grok-3-mini"  # use cheaper model for research subagent
coder = "grok-3"

[subagents.toggle]
researcher = true
coder = true
```

## SubagentSpawnContext Key Fields
```
parent_session_id     → tracks hierarchy
parent_depth          → prevents infinite recursion
parent_cwd            → base working directory
yolo_mode             → bypass confirmations
hunk_tracker_handle   → shared change tracking
fs / terminal         → shared backends
memory_config         → shared memory store
auto_wake_enabled     → whether completions trigger synthetic prompts
goal_loop_active      → suppress auto-wake during /goal
parent_blocking_wait_depth → routing control for queued prompts
```
