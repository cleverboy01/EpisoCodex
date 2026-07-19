#!/usr/bin/env python3
"""
Safe Shell Guard — PreToolUse blocking hook
Source pattern: xai-grok-hooks/examples/hooks/bin/safe-shell-guard.sh
Blocks obviously destructive shell commands before they execute.
"""
import sys
import json
import re

DESTRUCTIVE_PATTERNS = [
    r'rm\s+-[a-zA-Z]*r[a-zA-Z]*f\s+/',    # rm -rf /
    r'rm\s+-[a-zA-Z]*f[a-zA-Z]*r\s+/',    # rm -fr /
    r'sudo\s+rm\s+-r',                     # sudo rm -r
    r'mkfs\.',                             # format disk
    r'dd\s+.*of=/dev/[sh]d',              # dd to disk device
    r':\(\)\{.*\}',                        # fork bomb pattern
    r'>\s*/etc/passwd',                    # overwrite passwd
    r'chmod\s+-R\s+777\s+/',              # permission bomb
    r'>\s*/dev/[sh]d',                    # write to disk device
    r'shred\s+.*/',                        # shred system files
]

def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # fail-open: allow if we can't parse
        print(json.dumps({"decision": "allow"}))
        return

    tool_input = data.get("toolInput", {})
    command = tool_input.get("command", "")

    for pattern in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            print(json.dumps({
                "decision": "deny",
                "reason": f"Blocked: destructive command pattern detected. Command: {command[:100]}"
            }))
            sys.exit(2)

    print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
