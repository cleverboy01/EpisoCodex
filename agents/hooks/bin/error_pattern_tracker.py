#!/usr/bin/env python3
"""
Error Pattern Tracker — PostToolUse passive hook
Silently tracks tool failures and writes patterns to agents/logs/error-patterns.json
Used by the health-check skill and self-healing agents.
Source pattern: xai-grok-hooks/examples + self_healing spec
"""
import sys
import json
import os
from datetime import datetime, timezone
from collections import defaultdict

PATTERNS_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "logs", "error-patterns.json"
)

def classify_error(tool_name: str, error: str) -> str:
    """Classify an error into a known category for pattern matching."""
    e = error.lower()
    if "modulenotfounderror" in e or "cannot find module" in e or "no module named" in e:
        return "missing_dependency"
    if "assertionerror" in e or "assertion failed" in e:
        return "test_failure"
    if "typeerror" in e or "type error" in e:
        return "type_mismatch"
    if "syntaxerror" in e or "syntax error" in e:
        return "syntax_error"
    if "enoent" in e or "no such file" in e or "file not found" in e:
        return "file_not_found"
    if "permission denied" in e or "eacces" in e:
        return "permission_denied"
    if "eaddrinuse" in e or "address already in use" in e or "port" in e and "use" in e:
        return "port_in_use"
    if "circular" in e or "circular import" in e or "import cycle" in e:
        return "circular_import"
    if "connection refused" in e or "econnrefused" in e:
        return "connection_refused"
    if "timeout" in e:
        return "timeout"
    return "unknown"

def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    # Only track failures
    hook_event = data.get("hookEventName", "")
    if hook_event not in ("post_tool_use_failure", "PostToolUseFailure"):
        # Check if PostToolUse has error in result
        if hook_event not in ("post_tool_use", "PostToolUse"):
            sys.exit(0)
        tool_result = data.get("toolResult", {})
        if isinstance(tool_result, dict):
            is_error = tool_result.get("isError", False) or tool_result.get("error")
        elif isinstance(tool_result, str):
            is_error = "error" in tool_result.lower() or "failed" in tool_result.lower()
        else:
            sys.exit(0)
        if not is_error:
            sys.exit(0)
        error_text = str(tool_result)
    else:
        error_text = str(data.get("error", ""))

    tool_name = data.get("toolName", "unknown")
    tool_input = data.get("toolInput", {})
    session = data.get("sessionId", "unknown")[:8]
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    category = classify_error(tool_name, error_text)

    # Load existing patterns
    os.makedirs(os.path.dirname(PATTERNS_FILE), exist_ok=True)
    try:
        with open(PATTERNS_FILE, "r", encoding="utf-8") as f:
            patterns = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        patterns = {"patterns": [], "summary": {}}

    # Find existing pattern or add new
    found = False
    for p in patterns["patterns"]:
        if p["category"] == category and p["tool"] == tool_name:
            p["count"] += 1
            p["last_seen"] = ts
            p["last_session"] = session
            # Keep last 3 error samples
            if len(p["samples"]) < 3:
                p["samples"].append(error_text[:200])
            found = True
            break

    if not found:
        # Extract file path from tool input if available
        file_path = (
            tool_input.get("path") or
            tool_input.get("file") or
            tool_input.get("target_file") or
            ""
        )
        patterns["patterns"].append({
            "category": category,
            "tool": tool_name,
            "count": 1,
            "first_seen": ts,
            "last_seen": ts,
            "last_session": session,
            "file_path": str(file_path),
            "samples": [error_text[:200]],
        })

    # Update summary
    patterns["summary"] = {
        cat: sum(1 for p in patterns["patterns"] if p["category"] == cat)
        for cat in set(p["category"] for p in patterns["patterns"])
    }
    patterns["total_errors"] = sum(p["count"] for p in patterns["patterns"])
    patterns["updated_at"] = ts

    with open(PATTERNS_FILE, "w", encoding="utf-8") as f:
        json.dump(patterns, f, indent=2)

if __name__ == "__main__":
    main()
