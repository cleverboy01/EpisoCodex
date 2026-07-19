#!/usr/bin/env python3
"""
RLHF Feedback Loop — Active Learning from Error/Resolution Pairs
================================================================
Phase: Active RLHF / Feedback Loop (AGI Cognitive Layer)

This module forms the core "never repeat a mistake" engine.
It operates in three modes:

1. HOOK MODE (PostToolUse/PostToolUseFailure):
   - Detects errors in tool results
   - Stores them in SQLite with context: file, tool, error text, category
   - Marks them as UNRESOLVED

2. RESOLVE MODE (CLI):
   - When an agent successfully fixes a previous error, it calls this script
     with `resolve` sub-command to log the resolution strategy
   - The error entry is marked RESOLVED with the solution text attached

3. PREFLIGHT MODE (CLI / SessionStart):
   - Called BEFORE starting a new task
   - Queries the DB for similar past errors relevant to the current task
   - Prints a concise "Danger Report" so the agent can avoid those pitfalls

Storage: agents/logs/rlhf-memory.db  (SQLite, zero external dependencies)
Index:   agents/logs/rlhf-summary.json  (lightweight JSON for quick reads)

Usage:
    # Query before a task (PREFLIGHT):
    python agents/hooks/bin/rlhf_feedback_loop.py preflight "refactor auth module"

    # Manually record a resolution after fixing a bug:
    python agents/hooks/bin/rlhf_feedback_loop.py resolve --error-id 7 \
        --solution "Added missing __init__.py and updated sys.path"

    # Show all unresolved errors:
    python agents/hooks/bin/rlhf_feedback_loop.py report --unresolved

    # Show full statistics:
    python agents/hooks/bin/rlhf_feedback_loop.py stats
"""
import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT       = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_FILE    = os.path.join(ROOT, "logs", "rlhf-memory.db")
SUMMARY    = os.path.join(ROOT, "logs", "rlhf-summary.json")

# ── Schema ─────────────────────────────────────────────────────────────────────
SCHEMA = """
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
"""

# ── Error classification (mirrors error_pattern_tracker categories) ────────────
_CATEGORIES = [
    ("missing_dependency",  ["modulenotfounderror", "cannot find module", "no module named"]),
    ("test_failure",         ["assertionerror", "assertion failed"]),
    ("type_mismatch",        ["typeerror", "type error"]),
    ("syntax_error",         ["syntaxerror", "syntax error"]),
    ("file_not_found",       ["enoent", "no such file", "file not found"]),
    ("permission_denied",    ["permission denied", "eacces"]),
    ("port_in_use",          ["eaddrinuse", "address already in use"]),
    ("circular_import",      ["circular", "import cycle"]),
    ("connection_refused",   ["connection refused", "econnrefused"]),
    ("timeout",              ["timeout"]),
    ("import_error",         ["importerror", "cannot import"]),
    ("attribute_error",      ["attributeerror"]),
    ("key_error",            ["keyerror"]),
    ("index_error",          ["indexerror"]),
    ("value_error",          ["valueerror"]),
    ("name_error",           ["nameerror"]),
    ("runtime_error",        ["runtimeerror"]),
    ("git_conflict",         ["conflict", "merge conflict", "rejected"]),
    ("encoding_error",       ["unicodedecodeerror", "unicodeencodeerror", "codec"]),
]


def classify_error(error: str) -> str:
    e = error.lower()
    for category, keywords in _CATEGORIES:
        if any(k in e for k in keywords):
            return category
    return "unknown"


def tokenize(text: str) -> list:
    """Simple keyword tokenizer — dependency-free."""
    stopwords = {
        "a", "an", "the", "to", "of", "for", "and", "or", "in", "on",
        "with", "is", "are", "be", "this", "that", "it", "use", "when",
    }
    return [t for t in re.findall(r"[a-z0-9_]+", text.lower())
            if t not in stopwords and len(t) > 2]


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Database helpers ───────────────────────────────────────────────────────────

def connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.executescript(SCHEMA)
    conn.row_factory = sqlite3.Row
    return conn


def _write_summary(conn: sqlite3.Connection) -> None:
    """Regenerate the lightweight JSON summary for quick agent reads."""
    rows = conn.execute(
        "SELECT category, COUNT(*) as cnt, SUM(resolved) as res "
        "FROM error_memory GROUP BY category"
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM error_memory").fetchone()[0]
    unresolved = conn.execute(
        "SELECT COUNT(*) FROM error_memory WHERE resolved=0"
    ).fetchone()[0]
    summary = {
        "updated_at":      now_utc(),
        "total_errors":    total,
        "unresolved":      unresolved,
        "resolved":        total - unresolved,
        "by_category":     {r["category"]: {"total": r["cnt"], "resolved": r["res"]}
                            for r in rows},
    }
    with open(SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


# ── Core operations ────────────────────────────────────────────────────────────

def record_error(
    error_text: str,
    tool_name: str = "",
    file_path: str = "",
    session_id: str = "",
    context: str = "",
) -> int:
    """
    Store a new error entry.  Returns the row ID so callers can resolve later.
    Deduplicates: if the same (category, tool, file_path) was seen < 24 h ago
    and is still unresolved, bumps a counter instead of inserting a duplicate.
    """
    category = classify_error(error_text)
    ts = now_utc()
    conn = connect()
    with conn:
        # Check for recent duplicate
        existing = conn.execute(
            "SELECT id FROM error_memory "
            "WHERE category=? AND tool_name=? AND file_path=? AND resolved=0 "
            "AND ts >= datetime('now', '-1 day')",
            (category, tool_name, file_path),
        ).fetchone()
        if existing:
            return existing["id"]  # already tracked, skip duplicate

        cur = conn.execute(
            "INSERT INTO error_memory "
            "(ts, session_id, category, tool_name, file_path, error_text, context) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ts, session_id, category, tool_name, file_path,
             error_text[:1000], context[:500]),
        )
        row_id = cur.lastrowid

    _write_summary(conn)
    return row_id


def resolve_error(error_id: int, solution: str) -> bool:
    """Mark an error as resolved and log the solution strategy."""
    conn = connect()
    ts = now_utc()
    with conn:
        conn.execute(
            "UPDATE error_memory SET resolved=1, solution=?, resolved_at=? WHERE id=?",
            (solution[:2000], ts, error_id),
        )
        conn.execute(
            "INSERT INTO resolution_log (error_id, ts, strategy) VALUES (?, ?, ?)",
            (error_id, ts, solution[:2000]),
        )
    _write_summary(conn)
    return True


def preflight_query(task: str, limit: int = 5) -> list:
    """
    Before starting a new task: find relevant past errors + their solutions.
    Returns a ranked list of lessons the agent should be aware of.
    """
    conn = connect()
    rows = conn.execute(
        "SELECT id, category, tool_name, file_path, error_text, resolved, solution "
        "FROM error_memory ORDER BY id DESC LIMIT 300"
    ).fetchall()

    task_tokens = set(tokenize(task))
    scored = []
    for r in rows:
        doc = " ".join([r["category"], r["tool_name"], r["file_path"],
                        r["error_text"], r["solution"]])
        doc_tokens = tokenize(doc)
        overlap = sum(1 for t in doc_tokens if t in task_tokens)
        if overlap > 0:
            scored.append((overlap, r))

    scored.sort(key=lambda x: (-x[0], 0 if x[1]["resolved"] == 0 else 1))

    results = []
    for _, r in scored[:limit]:
        results.append({
            "id":        r["id"],
            "category":  r["category"],
            "tool":      r["tool_name"],
            "file":      r["file_path"],
            "error":     r["error_text"][:200],
            "resolved":  bool(r["resolved"]),
            "solution":  r["solution"][:300] if r["solution"] else None,
        })
    return results


def get_report(unresolved_only: bool = False) -> list:
    conn = connect()
    q = "SELECT * FROM error_memory"
    if unresolved_only:
        q += " WHERE resolved=0"
    q += " ORDER BY id DESC"
    rows = conn.execute(q).fetchall()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    conn = connect()
    total      = conn.execute("SELECT COUNT(*) FROM error_memory").fetchone()[0]
    resolved   = conn.execute("SELECT COUNT(*) FROM error_memory WHERE resolved=1").fetchone()[0]
    by_cat     = conn.execute(
        "SELECT category, COUNT(*) as c FROM error_memory GROUP BY category ORDER BY c DESC"
    ).fetchall()
    top_files  = conn.execute(
        "SELECT file_path, COUNT(*) as c FROM error_memory "
        "WHERE file_path != '' GROUP BY file_path ORDER BY c DESC LIMIT 5"
    ).fetchall()
    return {
        "total":      total,
        "resolved":   resolved,
        "unresolved": total - resolved,
        "by_category": {r["category"]: r["c"] for r in by_cat},
        "top_error_files": [{r["file_path"]: r["c"]} for r in top_files],
    }


# ── Hook mode (reads stdin JSON from Antigravity/Claude hooks) ─────────────────

def hook_mode() -> None:
    """
    Passive PostToolUse hook.
    Reads hook payload from stdin.  Extracts error info and calls record_error.
    Prints nothing (silent hook).  Exits 0 always (fail-open).
    """
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    event = data.get("hookEventName", "")
    if event not in (
        "post_tool_use", "PostToolUse",
        "post_tool_use_failure", "PostToolUseFailure",
    ):
        sys.exit(0)

    # Extract error text
    if event in ("post_tool_use_failure", "PostToolUseFailure"):
        error_text = str(data.get("error", ""))
    else:
        tool_result = data.get("toolResult", {})
        if isinstance(tool_result, dict):
            is_error = tool_result.get("isError", False) or tool_result.get("error")
            error_text = str(tool_result) if is_error else ""
        elif isinstance(tool_result, str):
            is_error = "error" in tool_result.lower() or "failed" in tool_result.lower()
            error_text = tool_result if is_error else ""
        else:
            sys.exit(0)

    if not error_text.strip():
        sys.exit(0)

    tool_name  = data.get("toolName", "unknown")
    tool_input = data.get("toolInput", {})
    session_id = data.get("sessionId", "")[:8]
    file_path  = str(
        tool_input.get("path") or
        tool_input.get("file") or
        tool_input.get("target_file") or
        tool_input.get("TargetFile") or ""
    )

    record_error(
        error_text=error_text,
        tool_name=tool_name,
        file_path=file_path,
        session_id=session_id,
        context=json.dumps(tool_input)[:300] if tool_input else "",
    )
    sys.exit(0)


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

    # Hook mode: no args + stdin is a pipe
    if not sys.stdin.isatty() and len(sys.argv) == 1:
        hook_mode()
        return

    parser = argparse.ArgumentParser(
        description="RLHF Feedback Loop — AGI error memory with resolution tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ── preflight ──
    p_pre = sub.add_parser("preflight", help="query relevant past errors before a task")
    p_pre.add_argument("task", help="describe the upcoming task in plain language")
    p_pre.add_argument("--limit", type=int, default=5)

    # ── record ──
    p_rec = sub.add_parser("record", help="manually record an error")
    p_rec.add_argument("--error",   required=True, help="error text or message")
    p_rec.add_argument("--tool",    default="",    help="tool that caused the error")
    p_rec.add_argument("--file",    default="",    help="file path involved")
    p_rec.add_argument("--session", default="",    help="session ID")
    p_rec.add_argument("--context", default="",    help="extra context")

    # ── resolve ──
    p_res = sub.add_parser("resolve", help="mark an error as resolved with the solution")
    p_res.add_argument("--error-id", type=int, required=True, dest="error_id")
    p_res.add_argument("--solution", required=True, help="describe how the error was fixed")

    # ── report ──
    p_rep = sub.add_parser("report", help="list errors in the memory")
    p_rep.add_argument("--unresolved", action="store_true", help="show only unresolved errors")
    p_rep.add_argument("--json", action="store_true", dest="as_json")

    # ── stats ──
    sub.add_parser("stats", help="show aggregate statistics")

    args = parser.parse_args()

    if args.cmd == "preflight":
        results = preflight_query(args.task, args.limit)
        if not results:
            print(json.dumps({"status": "clean", "message": "No relevant past errors found. Proceed safely."}))
            return
        print("\n⚠️  PREFLIGHT DANGER REPORT — Relevant past errors for this task:\n")
        for r in results:
            status = "✅ RESOLVED" if r["resolved"] else "🔴 UNRESOLVED"
            print(f"  [{status}] #{r['id']} | Category: {r['category']} | Tool: {r['tool']}")
            if r["file"]:
                print(f"    File: {r['file']}")
            print(f"    Error: {r['error']}")
            if r["solution"]:
                print(f"    Solution: {r['solution']}")
            print()

    elif args.cmd == "record":
        rid = record_error(args.error, args.tool, args.file, args.session, args.context)
        print(json.dumps({"recorded": rid, "category": classify_error(args.error)}))

    elif args.cmd == "resolve":
        ok = resolve_error(args.error_id, args.solution)
        print(json.dumps({"resolved": ok, "error_id": args.error_id}))

    elif args.cmd == "report":
        rows = get_report(args.unresolved)
        if args.as_json:
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        else:
            for r in rows:
                status = "✅" if r["resolved"] else "🔴"
                print(f"{status} #{r['id']} [{r['category']}] {r['ts']} | {r['tool_name']} | {r['file_path']}")
                print(f"   Error: {r['error_text'][:120]}")
                if r["solution"]:
                    print(f"   Fix: {r['solution'][:120]}")
                print()

    elif args.cmd == "stats":
        print(json.dumps(get_stats(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
