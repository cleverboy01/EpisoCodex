# Hooks Spec
# Source: xai-grok-hooks/src/ (xai-org/grok-build)

## What are Hooks?
Hooks are scripts/commands that fire at key lifecycle events in the agent.
They can BLOCK tool execution (PreToolUse) or passively observe events.

## Hook Event Names
```
Session Lifecycle:
  SessionStart        → fires on new session
  SessionEnd          → fires when session ends (reason: normal/cancelled/error)
  Stop                → fires when agent turn ends
  StopFailure         → fires when turn ends due to API error

Tool Events:
  PreToolUse          → fires BEFORE tool executes [BLOCKING — can deny]
  PostToolUse         → fires AFTER tool succeeds [passive]
  PostToolUseFailure  → fires AFTER tool throws error [passive]
  PermissionDenied    → fires when tool denied by permission system [passive]

User/Notification Events:
  UserPromptSubmit    → fires when user submits a prompt [passive]
  Notification        → fires on agent notifications [passive]

Subagent Events:
  SubagentStart       → fires when a subagent is spawned [passive]
  SubagentStop        → fires when a subagent completes [passive]

Compaction Events:
  PreCompact          → fires before context compaction [passive]
  PostCompact         → fires after context compaction [passive]
```

## Hook File Format (JSON)
Place in `~/.grok/hooks/` (global) or `<project>/.grok/hooks/` (project-scoped):
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "run_terminal_cmd",
        "hooks": [
          { "type": "command", "command": "bin/safe-shell-guard.sh", "timeout": 5 }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          { "type": "command", "command": "bin/session-log.sh", "timeout": 3 }
        ]
      }
    ]
  }
}
```

## Hook Event Envelope (sent to script via stdin as JSON)
```json
{
  "hookEventName": "pre_tool_use",
  "sessionId": "abc-123",
  "cwd": "/workspace",
  "workspaceRoot": "/workspace",
  "timestamp": "2025-01-01T00:00:00Z",
  "toolName": "run_terminal_cmd",
  "toolUseId": "tool-456",
  "toolInput": { "command": "rm -rf /" },
  "toolInputTruncated": false,
  "permissionMode": "default"
}
```

## Script Response (PreToolUse — Blocking)
```json
{ "decision": "allow" }
```
or:
```json
{ "decision": "deny", "reason": "Destructive command blocked by safe-shell guard" }
```
Exit codes: `0` = allow, `2` = deny, other = fail-open (allow).

## Safe Shell Guard Pattern
```bash
#!/bin/bash
# Read JSON from stdin
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('toolInput',{}).get('command',''))")

# Block destructive patterns
if echo "$COMMAND" | grep -qE 'rm\s+-rf\s+/|sudo\s+rm\s+-rf|mkfs|fork\s*bomb|:\(\)\{.*\}'; then
  echo '{"decision":"deny","reason":"Destructive command blocked"}'
  exit 2
fi

echo '{"decision":"allow"}'
```

## Matcher Patterns
- Regex on tool name
- Claude-style names (`Bash`, `Read`, `Edit`) auto-expand to Grok names
- Lifecycle events (`SessionStart`, `SessionEnd`, `Stop`, `UserPromptSubmit`) do NOT support matchers — fire on every occurrence
- All other events support matcher-based filtering

## Payload Size Limit
- `toolInput` and `toolResult` are truncated at **128 KB** with `[truncated]` suffix.
