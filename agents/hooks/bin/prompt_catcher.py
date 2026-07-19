#!/usr/bin/env python3
"""
Intercepts UserPromptSubmit to feed the AGI Co-Pilot CLI dashboard.
"""
import sys
import json
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
STATE_FILE = ROOT / "agents" / "logs" / "live-session.json"

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    prompt = payload.get("userPrompt", "")
    if not prompt:
        sys.exit(0)

    # Initialize or load state
    os.makedirs(STATE_FILE.parent, exist_ok=True)
    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass

    state["session_id"] = payload.get("sessionId", "unknown")
    state["last_prompt"] = prompt
    state["prompt_time"] = datetime.now(timezone.utc).isoformat()
    state["active_tool"] = ""  # Reset active tool on new prompt
    state["active_tool_time"] = ""

    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    sys.exit(0)

if __name__ == "__main__":
    main()
