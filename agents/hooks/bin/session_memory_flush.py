#!/usr/bin/env python3
"""
Session Memory Flush — SessionEnd passive hook
At session end, writes a concise session log for the Dream system to consolidate.
Source pattern: xai-grok-memory/src/dream.rs DREAM_SYSTEM_PROMPT

The Dream system reads these logs every 5+ sessions / 24+ hours and
merges them into MEMORY.md (the permanent knowledge store).
"""
import sys
import json
import os
from datetime import datetime, timezone

MEMORY_DIR = os.path.join(os.path.expanduser("~"), ".grok", "memory")
WORKSPACE_HASH_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "logs", ".workspace-hash")
SESSION_LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "session-decisions.json")

def get_workspace_hash(cwd: str) -> str:
    """Simple 8-char hash of workspace path for scoped memory storage."""
    import hashlib
    return hashlib.blake2b(cwd.encode(), digest_size=8).hexdigest()

def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    hook_event = data.get("hookEventName", "")
    if hook_event not in ("session_end", "SessionEnd"):
        sys.exit(0)

    cwd = data.get("cwd", "")
    session_id = data.get("sessionId", "unknown")[:8]
    ts = datetime.now(timezone.utc)
    date_str = ts.strftime("%Y-%m-%d")
    ts_str = ts.strftime("%Y-%m-%dT%H:%M:%SZ")

    turn_count = data.get("turnCount", 0)
    tool_call_count = data.get("toolCallCount", 0)
    reason = data.get("reason", "normal")

    # Read any decisions logged during this session
    decisions = []
    try:
        with open(SESSION_LOG_FILE, "r", encoding="utf-8") as f:
            session_data = json.load(f)
            decisions = session_data.get("decisions", [])
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # Write session log for Dream consolidation
    if cwd and decisions:
        ws_hash = get_workspace_hash(cwd)
        sessions_dir = os.path.join(MEMORY_DIR, ws_hash, "sessions")
        os.makedirs(sessions_dir, exist_ok=True)

        slug = os.path.basename(cwd).replace(" ", "-")[:20]
        log_name = f"{date_str}-{slug}-{session_id}"
        log_path = os.path.join(sessions_dir, f"{log_name}.md")

        content_lines = [
            f"# Session: {session_id} — {date_str}",
            f"Workspace: {cwd}",
            f"Turns: {turn_count}, Tools: {tool_call_count}, End: {reason}",
            "",
        ]
        for d in decisions:
            content_lines.append(f"## {d.get('category', 'Note')}")
            content_lines.append(d.get("content", ""))
            content_lines.append("")

        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content_lines))

    # Clear session decisions log
    if os.path.exists(SESSION_LOG_FILE):
        with open(SESSION_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump({"decisions": [], "session_id": session_id, "cleared_at": ts_str}, f)

if __name__ == "__main__":
    main()
