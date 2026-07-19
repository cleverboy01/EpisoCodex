#!/usr/bin/env python3
"""
Antigravity Manager — Dynamic Token Budget & Safety Manager
===========================================================
Phase: Advanced Token Controls & Loop-Prevention (AGI Safety)

This manager tracks token consumption across tools, sessions, and days.
It maintains a ledger, checks limits, and blocks execution if limits are
exceeded to prevent runaway loops (infinite tool invocations).

Usage:
    # Show stats:
    python agents/hooks/bin/antigravity_manager.py stats

    # Set limits:
    python agents/hooks/bin/antigravity_manager.py set-limit --session 50000 --daily 200000

    # Run check as a blocking hook (PreToolUse):
    python agents/hooks/bin/antigravity_manager.py check
"""
import sys
import os
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

# ── Paths & Defaults ───────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[3]
LEDGER_FILE = ROOT / "agents" / "logs" / "token-ledger.json"

DEFAULT_LIMITS = {
    "session_limit": 100000,   # Max tokens per session (100k)
    "daily_limit": 300000,     # Max tokens per day (300k)
    "session_usage": 0,
    "daily_usage": 0,
    "last_reset_day": "",
    "current_session_id": "",
    "locked": False
}

def get_utf8_terminal():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

def load_ledger() -> dict:
    if not LEDGER_FILE.exists():
        os.makedirs(LEDGER_FILE.parent, exist_ok=True)
        return DEFAULT_LIMITS.copy()
    try:
        data = json.loads(LEDGER_FILE.read_text(encoding="utf-8"))
        # Ensure all default keys exist
        for k, v in DEFAULT_LIMITS.items():
            if k not in data:
                data[k] = v
        return data
    except Exception:
        return DEFAULT_LIMITS.copy()

def save_ledger(data: dict) -> None:
    os.makedirs(LEDGER_FILE.parent, exist_ok=True)
    LEDGER_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def estimate_tokens(text: str) -> int:
    """Fast, offline character-based token estimation (approx 4 chars = 1 token)."""
    if not text:
        return 0
    return max(1, int(len(text) / 4))

def reset_daily_if_new_day(ledger: dict) -> dict:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if ledger["last_reset_day"] != today:
        ledger["daily_usage"] = 0
        ledger["last_reset_day"] = today
        ledger["locked"] = False
    return ledger

def update_usage(payload: dict) -> None:
    # 1. Update live-session.json for Co-Pilot
    try:
        state_file = ROOT / "agents" / "logs" / "live-session.json"
        state = {}
        if state_file.exists():
            state = json.loads(state_file.read_text(encoding="utf-8"))
        
        tool_name = payload.get("toolName", "")
        # If toolResult exists, it's PostToolUse, so the tool finished
        is_finished = "toolResult" in payload or "error" in payload
        
        state["active_tool"] = "" if is_finished else tool_name
        if not is_finished and tool_name:
            state["active_tool_time"] = datetime.now(timezone.utc).isoformat()
            
        state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

    # 2. Update token ledger
    ledger = load_ledger()
    ledger = reset_daily_if_new_day(ledger)

    session_id = payload.get("sessionId", "unknown")[:8]
    if ledger["current_session_id"] != session_id:
        ledger["current_session_id"] = session_id
        ledger["session_usage"] = 0 # Reset session count

    # Estimate input tokens
    input_str = json.dumps(payload.get("toolInput", {}))
    # Estimate output tokens if available (PostToolUse)
    result_str = ""
    tool_result = payload.get("toolResult", {})
    if tool_result:
        result_str = json.dumps(tool_result)

    input_tokens = estimate_tokens(input_str)
    output_tokens = estimate_tokens(result_str)
    total_new_tokens = input_tokens + output_tokens

    ledger["session_usage"] += total_new_tokens
    ledger["daily_usage"] += total_new_tokens

    # Auto-lock if threshold reached
    if ledger["session_usage"] >= ledger["session_limit"] or ledger["daily_usage"] >= ledger["daily_limit"]:
        ledger["locked"] = True

    save_ledger(ledger)

def run_check() -> None:
    ledger = load_ledger()
    ledger = reset_daily_if_new_day(ledger)

    if ledger["locked"]:
        response = {
            "decision": "deny",
            "reason": (
                f"ANTIGRAVITY SAFETY LOCK: Token budget exceeded!\n"
                f"  Session usage: {ledger['session_usage']} / {ledger['session_limit']} tokens\n"
                f"  Daily usage: {ledger['daily_usage']} / {ledger['daily_limit']} tokens\n"
                f"  Locked status: LOCKED 🔴\n"
                f"To reset or increase limits, run:\n"
                f"  python agents/hooks/bin/antigravity_manager.py set-limit --session <limit>"
            )
        }
        print(json.dumps(response))
        sys.exit(2)

    print(json.dumps({"decision": "allow"}))
    sys.exit(0)

def print_stats() -> None:
    ledger = load_ledger()
    ledger = reset_daily_if_new_day(ledger)
    
    session_rem = max(0, ledger["session_limit"] - ledger["session_usage"])
    daily_rem = max(0, ledger["daily_limit"] - ledger["daily_usage"])
    
    session_pct = min(100.0, (ledger["session_usage"] / ledger["session_limit"]) * 100)
    daily_pct = min(100.0, (ledger["daily_usage"] / ledger["daily_limit"]) * 100)

    print("\n=============================================")
    print("      🚀 ANTIGRAVITY TOKEN MANAGER 🚀        ")
    print("=============================================")
    print(f"Session ID     : {ledger['current_session_id']}")
    print(f"Status         : {'🔴 LOCKED' if ledger['locked'] else '🟢 ACTIVE'}")
    print(f"Ledger File    : {os.path.relpath(LEDGER_FILE, ROOT)}")
    print("---------------------------------------------")
    print(f"Session Usage  : {ledger['session_usage']:,} / {ledger['session_limit']:,} tokens ({session_pct:.1f}%)")
    print(f"Session Remain : {session_rem:,} tokens")
    print(f"Daily Usage    : {ledger['daily_usage']:,} / {ledger['daily_limit']:,} tokens ({daily_pct:.1f}%)")
    print(f"Daily Remain   : {daily_rem:,} tokens")
    print("=============================================\n")

def hook_handler() -> None:
    """Entry point for passive PostToolUse logging."""
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    update_usage(payload)
    sys.exit(0)

def main():
    get_utf8_terminal()
    parser = argparse.ArgumentParser(description="Antigravity Token Budget & Safety Manager")
    sub = parser.add_subparsers(dest="cmd")

    # Stats command
    sub.add_parser("stats", help="Show token consumption stats")

    # Set limits command
    p_lim = sub.add_parser("set-limit", help="Set token limits and unlock budget")
    p_lim.add_argument("--session", type=int, help="Session limit in tokens")
    p_lim.add_argument("--daily", type=int, help="Daily limit in tokens")
    p_lim.add_argument("--unlock", action="store_true", help="Unlock budget manually")

    # Check command (runs as a blocking hook)
    sub.add_parser("check", help="Verify if token budget is within limits")

    # Handle direct pipe hooks (no arguments, piped stdin)
    if len(sys.argv) == 1 and not sys.stdin.isatty():
        hook_handler()
        return

    args = parser.parse_args()

    if args.cmd == "stats" or args.cmd is None:
        print_stats()
    elif args.cmd == "set-limit":
        ledger = load_ledger()
        if args.session:
            ledger["session_limit"] = args.session
        if args.daily:
            ledger["daily_limit"] = args.daily
        if args.unlock or args.session or args.daily:
            ledger["locked"] = False
            # Recalculate lock
            ledger = reset_daily_if_new_day(ledger)
            if ledger["session_usage"] < ledger["session_limit"] and ledger["daily_usage"] < ledger["daily_limit"]:
                ledger["locked"] = False
        save_ledger(ledger)
        print("Limits updated successfully.")
        print_stats()
    elif args.cmd == "check":
        run_check()

if __name__ == "__main__":
    main()
