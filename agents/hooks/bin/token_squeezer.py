#!/usr/bin/env python3
"""
Token Squeezer — Active Token Guard (AGI Cognitive Layer)
=========================================================
Phase: Token Optimization & Guard rails

This hook blocks large, un-targeted file reads before they can burn the agent's
context window. If an agent attempts to view a file without specifying line
ranges, and the file exceeds the line threshold, the squeezer denies execution
and guides the agent to use targeted grep/view tools instead.

Usage (Registered in agent-hooks.json):
    python agents/hooks/bin/token_squeezer.py
"""
import sys
import json
import os

# Maximum number of lines allowed for a full file read
LINE_THRESHOLD = 150
# Maximum line range allowed even with StartLine/EndLine specified
RANGE_LIMIT = 200

def main() -> None:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    event = data.get("hookEventName", "")
    if event not in ("pre_tool_use", "PreToolUse"):
        sys.exit(0)

    tool_name = data.get("toolName", "")
    tool_input = data.get("toolInput", {})

    # Intercept file viewing/reading tools
    if tool_name in ("view_file", "view_file_content", "read_file"):
        path = tool_input.get("AbsolutePath") or tool_input.get("path") or tool_input.get("TargetFile")
        if not path or not os.path.exists(path):
            sys.exit(0)

        # Check if line range is specified
        start_line = tool_input.get("StartLine")
        end_line = tool_input.get("EndLine")

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                line_count = len(lines)
        except Exception:
            sys.exit(0) # Fail-open on read errors

        # Case 1: Full file read attempted on a large file
        if start_line is None and end_line is None:
            if line_count > LINE_THRESHOLD:
                response = {
                    "decision": "deny",
                    "reason": (
                        f"TOKEN BURN GUARD: The file '{os.path.basename(path)}' has {line_count} lines. "
                        f"Reading the entire file is blocked to conserve token budget. "
                        f"Please: \n"
                        f"  1. Use grep_search or symbol lookup to locate specific code.\n"
                        f"  2. Call view_file with specific 'StartLine' and 'EndLine' (max {LINE_THRESHOLD} lines)."
                    )
                }
                print(json.dumps(response))
                sys.exit(2) # Exit code 2 = Deny

        # Case 2: Range read attempted but range is too wide
        elif start_line is not None and end_line is not None:
            try:
                requested_range = int(end_line) - int(start_line) + 1
                if requested_range > RANGE_LIMIT:
                    response = {
                        "decision": "deny",
                        "reason": (
                            f"TOKEN BURN GUARD: The requested range of {requested_range} lines (L{start_line}-L{end_line}) "
                            f"exceeds the limit of {RANGE_LIMIT} lines. Please narrow down your view window to inspect "
                            f"only the relevant functions or blocks."
                        )
                    }
                    print(json.dumps(response))
                    sys.exit(2)
            except ValueError:
                pass

    # Allow all other tool runs
    print(json.dumps({"decision": "allow"}))
    sys.exit(0)

if __name__ == "__main__":
    main()
