#!/usr/bin/env python3
"""
Episodic & Reflective Memory (Phase 3) — SessionEnd hook + CLI
A local, dependency-free experience ledger (SQLite) that stores post-mortem
reflections after each task and lets agents query past lessons BEFORE starting
new work, preventing repeated mistakes across sessions.

Usage:
    # Store a reflection (post-mortem) after a task
    python agents/hooks/bin/episodic_memory.py store \
        --task "fix flaky auth test" --outcome failure \
        --lessons "mock the clock; test depended on real time" --tags tests,auth

    # Query lessons relevant to a new task (run at session start)
    python agents/hooks/bin/episodic_memory.py query "auth tests failing" --limit 5

    (also runs as a SessionEnd hook: converts session decisions into a reflection)
"""
import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_FILE = os.path.join(ROOT, "logs", "experience-ledger.db")
SESSION_LOG_FILE = os.path.join(ROOT, "logs", "session-decisions.json")

SCHEMA = """
CREATE TABLE IF NOT EXISTS reflections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    task TEXT NOT NULL,
    outcome TEXT NOT NULL DEFAULT 'success',
    lessons TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT ''
);
"""


def connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.execute(SCHEMA)
    return conn


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def store(task: str, outcome: str, lessons: str, tags: str = "") -> int:
    conn = connect()
    with conn:
        cur = conn.execute(
            "INSERT INTO reflections (ts, task, outcome, lessons, tags) VALUES (?, ?, ?, ?, ?)",
            (now(), task, outcome, lessons, tags),
        )
    return cur.lastrowid


def tokenize(text: str) -> list:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2]


def query(text: str, limit: int = 5) -> list:
    """Keyword-ranked recall. Swap the ranking for embeddings later without
    changing the storage layer."""
    conn = connect()
    rows = conn.execute(
        "SELECT id, ts, task, outcome, lessons, tags FROM reflections ORDER BY id DESC LIMIT 500"
    ).fetchall()
    q_tokens = set(tokenize(text))
    scored = []
    for row in rows:
        doc_tokens = tokenize(" ".join([row[2], row[4], row[5]]))
        overlap = sum(1 for t in doc_tokens if t in q_tokens)
        if overlap > 0:
            scored.append((overlap, row))
    scored.sort(key=lambda x: (x[0], x[1][0]), reverse=True)
    return [
        {"id": r[0], "ts": r[1], "task": r[2], "outcome": r[3], "lessons": r[4], "tags": r[5]}
        for _, r in scored[:limit]
    ]


def hook_session_end():
    """SessionEnd hook: persist this session's decisions as a reflection so the
    Dream/consolidation layer and future sessions can recall them."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        sys.exit(0)
    if data.get("hookEventName", "") not in ("session_end", "SessionEnd"):
        sys.exit(0)

    decisions = []
    try:
        with open(SESSION_LOG_FILE, "r", encoding="utf-8") as f:
            decisions = json.load(f).get("decisions", [])
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    if not decisions:
        sys.exit(0)

    session_id = data.get("sessionId", "unknown")[:8]
    lessons = "\n".join(
        f"[{d.get('category', 'Note')}] {d.get('content', '')}" for d in decisions
    )
    store(task=f"session {session_id}", outcome="session_end", lessons=lessons, tags="session")


def main():
    if not sys.stdin.isatty() and len(sys.argv) == 1:
        hook_session_end()
        return

    parser = argparse.ArgumentParser(description="Episodic experience ledger")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_store = sub.add_parser("store", help="store a post-mortem reflection")
    p_store.add_argument("--task", required=True)
    p_store.add_argument("--outcome", choices=["success", "failure", "partial", "session_end"], default="success")
    p_store.add_argument("--lessons", required=True)
    p_store.add_argument("--tags", default="")

    p_query = sub.add_parser("query", help="recall relevant past lessons")
    p_query.add_argument("text")
    p_query.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()
    if args.cmd == "store":
        rid = store(args.task, args.outcome, args.lessons, args.tags)
        print(json.dumps({"stored": rid}))
    elif args.cmd == "query":
        print(json.dumps(query(args.text, args.limit), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
