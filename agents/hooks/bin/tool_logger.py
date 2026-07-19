#!/usr/bin/env python3
"""
Tool Activity Logger — PostToolUse passive hook
Source pattern: xai-grok-hooks/examples/hooks/bin/tool-logger.sh
Logs all tool calls to agents/logs/tool-activity.log
"""
import sys
import json
import os
from datetime import datetime, timezone

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "tool-activity.log")

def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    event = data.get("hookEventName", "unknown")
    tool = data.get("toolName", "unknown")
    session = data.get("sessionId", "unknown")[:8]
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    backgrounded = data.get("isBackgrounded", False)
    duration = data.get("durationMs", "?")

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ts} [{session}] {event} tool={tool} bg={backgrounded} dur={duration}ms\n")

if __name__ == "__main__":
    main()
