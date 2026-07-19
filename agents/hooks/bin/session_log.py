#!/usr/bin/env python3
"""
Session Audit Logger — SessionStart / SessionEnd passive hook
Source pattern: xai-grok-hooks/examples/hooks/bin/session-log.sh
Appends session metadata to agents/logs/session-audit.log
"""
import sys
import json
import os
from datetime import datetime, timezone

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "session-audit.log")

def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    event = data.get("hookEventName", "unknown")
    session = data.get("sessionId", "unknown")
    cwd = data.get("cwd", "unknown")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Extra fields per event type
    extra = ""
    if event == "session_end":
        reason = data.get("reason", "unknown")
        turns = data.get("turnCount", "?")
        tools = data.get("toolCallCount", "?")
        extra = f" reason={reason} turns={turns} tools={tools}"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ts} {event} session={session[:16]} cwd={cwd}{extra}\n")

if __name__ == "__main__":
    main()
