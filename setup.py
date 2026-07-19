#!/usr/bin/env python3
"""
Antigravity AGI Harness -- One-Click Bootstrapper
==================================================
Run this once after cloning the repo.

    python setup.py

Creates all required directories, databases, and indexes in under 3 seconds.
"""
import sys
import os
import json
import sqlite3
import subprocess
from pathlib import Path

# Force UTF-8 output on all platforms (fixes Windows cp1252 issues)
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

ROOT = Path(__file__).resolve().parent
AGENTS = ROOT / "agents"
LOGS = AGENTS / "logs"
BIN = AGENTS / "hooks" / "bin"

# ANSI color helpers (no dependencies required)
G = "\033[92m"
Y = "\033[93m"
C = "\033[96m"
R = "\033[91m"
B = "\033[1m"
E = "\033[0m"

def step(msg: str) -> None:
    print(f"  {C}·{E} {msg}...")

def ok(msg: str) -> None:
    print(f"  {G}✓{E} {msg}")

def fail(msg: str, err: str = "") -> None:
    print(f"  {R}✗{E} {msg}" + (f": {err}" if err else ""))

def banner():
    print(f"""
{B}{C}=============================================================
   ANTIGRAVITY -- AGI Harness Bootstrapper
   Proto-AGI Framework for Autonomous Software Engineering
============================================================={E}
""")

def create_directories():
    step("Creating directory structure")
    dirs = [
        LOGS,
        LOGS / "patches",
        LOGS / "backups",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    ok(f"Directories ready ({len(dirs)} created/verified)")

def init_json_files():
    step("Initializing JSON data files")
    files = {
        LOGS / "error-patterns.json": {
            "patterns": [], "summary": {}, "total_errors": 0, "updated_at": ""
        },
        LOGS / "session-decisions.json": {
            "decisions": [], "session_id": "", "cleared_at": ""
        },
        LOGS / "token-ledger.json": {
            "session_limit": 100000,
            "daily_limit": 300000,
            "session_usage": 0,
            "daily_usage": 0,
            "last_reset_day": "",
            "current_session_id": "",
            "locked": False
        },
    }
    created = 0
    for path, default in files.items():
        if not path.exists():
            path.write_text(json.dumps(default, indent=2, ensure_ascii=False), encoding="utf-8")
            created += 1
    ok(f"JSON files ready ({created} created, {len(files)-created} already existed)")

def init_sqlite_dbs():
    step("Initializing SQLite databases")
    # RLHF memory DB
    rlhf_db = LOGS / "rlhf-memory.db"
    conn = sqlite3.connect(str(rlhf_db))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS error_memory (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          TEXT    NOT NULL,
            session_id  TEXT    NOT NULL DEFAULT '',
            category    TEXT    NOT NULL DEFAULT 'unknown',
            tool_name   TEXT    NOT NULL DEFAULT '',
            file_path   TEXT    NOT NULL DEFAULT '',
            error_text  TEXT    NOT NULL,
            context     TEXT    NOT NULL DEFAULT '',
            resolved    INTEGER NOT NULL DEFAULT 0,
            solution    TEXT    NOT NULL DEFAULT '',
            resolved_at TEXT    NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS resolution_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            error_id    INTEGER NOT NULL,
            ts          TEXT    NOT NULL,
            strategy    TEXT    NOT NULL,
            FOREIGN KEY (error_id) REFERENCES error_memory(id)
        );
    """)
    conn.close()

    # Episodic memory DB
    ep_db = LOGS / "episodic-memory.db"
    conn2 = sqlite3.connect(str(ep_db))
    conn2.executescript("""
        CREATE TABLE IF NOT EXISTS experiences (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          TEXT NOT NULL,
            session_id  TEXT NOT NULL DEFAULT '',
            task        TEXT NOT NULL,
            outcome     TEXT NOT NULL DEFAULT '',
            lessons     TEXT NOT NULL DEFAULT '',
            tags        TEXT NOT NULL DEFAULT ''
        );
    """)
    conn2.close()
    ok("SQLite databases initialized (rlhf-memory.db, episodic-memory.db)")

def build_skill_index():
    step("Building skill index (agents/logs/skill-index.json)")
    try:
        result = subprocess.run(
            [sys.executable, str(BIN / "skill_indexer.py")],
            capture_output=True, text=True, timeout=10, cwd=str(ROOT)
        )
        if result.returncode == 0 or (LOGS / "skill-index.json").exists():
            idx = json.loads((LOGS / "skill-index.json").read_text(encoding="utf-8"))
            ok(f"Skill index built: {idx.get('skill_count', 0)} skills indexed")
        else:
            fail("Skill index build failed", result.stderr[:100])
    except Exception as e:
        fail("Skill index build error", str(e))

def check_python_deps():
    print(f"{C}Step 4: Checking Python dependencies...{E}")
    deps = {
        "rich": "rich",
        "customtkinter": "customtkinter"
    }
    for module, pkg in deps.items():
        try:
            __import__(module)
            print(f"  {G}✓{E} {pkg} is already installed.")
        except ImportError:
            print(f"  {Y}!{E} {pkg} is missing. Installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])
                print(f"  {G}✓{E} {pkg} installed successfully.")
            except Exception as e:
                print(f"  {R}✗ Failed to install {pkg}: {e}{E}")

def print_summary():
    print(f"""
{B}{G}============================================================
   Setup Complete!
============================================================{E}

{B}Quick Start:{E}
  {C}python agicli.py{E}                         Open live dashboard
  {C}python agicli.py run "your task here"{E}    Auto-route a task
  {C}python agicli.py loop{E}                    Start AGI loop
  {C}python agicli.py scan{E}                    Code health scan
  {C}python agicli.py tokens{E}                  Token budget stats
  {C}python agicli.py memory "task"{E}           RLHF preflight check
  {C}python agicli.py skills{E}                  List all skills

{B}IDE Integration:{E}
  Copy the agents/ folder and .cursorrules file to any project.
  Works with Cursor, Windsurf, Antigravity IDE, and any AI assistant.

{B}GitHub:{E} Star the repo and share your AGI experience!
""")


if __name__ == "__main__":
    banner()
    create_directories()
    init_json_files()
    init_sqlite_dbs()
    build_skill_index()
    check_python_deps()
    print_summary()
