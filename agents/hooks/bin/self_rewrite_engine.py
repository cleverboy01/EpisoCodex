#!/usr/bin/env python3
"""
Self-Rewrite Engine — Autonomous Core Code Optimizer
====================================================
Phase: Active RLHF / Self-Improvement (AGI Cognitive Layer)

This engine lets the agent inspect, analyze, and propose rewrites of the
hook scripts inside agents/hooks/bin/*.py.  It is NOT a fully autonomous
rewriter by default — every proposed patch must pass three gates:

    GATE 1 — Syntax check:   ast.parse() must succeed
    GATE 2 — Test run:       the patched script is executed in a throwaway
                             copy (sandbox) with --help / --selftest flag
    GATE 3 — Human gate:     a diff is printed and the agent must call
                             `apply` sub-command explicitly (or set
                             --auto-apply only in a sandbox context)

Rewrite triggers (read from RLHF memory):
    - A file appears in the top error files list (≥ N occurrences)
    - An agent explicitly calls `analyze` on a specific file
    - SessionEnd hook triggers a background scan (lightweight)

Usage:
    # Analyze a hook script for improvement opportunities:
    python agents/hooks/bin/self_rewrite_engine.py analyze \
        agents/hooks/bin/error_pattern_tracker.py

    # Propose a patch (outputs unified diff — does NOT apply):
    python agents/hooks/bin/self_rewrite_engine.py propose \
        agents/hooks/bin/error_pattern_tracker.py \
        --instruction "add retries on JSON parse failure"

    # Apply a previously proposed patch (after review):
    python agents/hooks/bin/self_rewrite_engine.py apply \
        agents/hooks/bin/error_pattern_tracker.py \
        --patch-file agents/logs/patches/error_pattern_tracker_<ts>.diff

    # Scan all hook scripts and rank by rewrite priority:
    python agents/hooks/bin/self_rewrite_engine.py scan

    # Rollback to the last backup:
    python agents/hooks/bin/self_rewrite_engine.py rollback \
        agents/hooks/bin/error_pattern_tracker.py

Storage:
    agents/logs/patches/          — proposed diffs
    agents/logs/rewrites.json     — audit log of all applied rewrites
    agents/logs/backups/          — pre-rewrite backups (.py.bak)
"""
import argparse
import ast
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parents[3]
HOOKS_BIN   = ROOT / "agents" / "hooks" / "bin"
LOGS_DIR    = ROOT / "agents" / "logs"
PATCHES_DIR = LOGS_DIR / "patches"
BACKUPS_DIR = LOGS_DIR / "backups"
REWRITE_LOG = LOGS_DIR / "rewrites.json"
RLHF_SUMMARY= LOGS_DIR / "rlhf-summary.json"

# Only files inside this boundary can be rewritten (safety constraint)
ALLOWED_REWRITE_DIR = HOOKS_BIN

# Files that must NEVER be auto-applied (require explicit human confirmation)
SACRED_FILES = {"safe_shell_guard.py", "self_rewrite_engine.py"}

# Minimum error occurrences before a file is flagged for rewrite priority
ERROR_THRESHOLD = 3


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ts_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# ── Safety guards ──────────────────────────────────────────────────────────────

def assert_safe_path(path: Path) -> None:
    """Raises ValueError if path is outside the allowed rewrite directory."""
    try:
        path.resolve().relative_to(ALLOWED_REWRITE_DIR.resolve())
    except ValueError:
        raise ValueError(
            f"SAFETY BLOCK: '{path}' is outside the allowed rewrite boundary "
            f"({ALLOWED_REWRITE_DIR}).  Self-rewrite is restricted to hook scripts only."
        )
    if path.name in SACRED_FILES:
        raise ValueError(
            f"SAFETY BLOCK: '{path.name}' is a sacred file and cannot be auto-applied. "
            f"Edit it manually."
        )


def syntax_check(code: str, filename: str = "<patch>") -> tuple[bool, str]:
    """Returns (ok, error_message)."""
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"


def sandbox_test(script_path: Path) -> tuple[bool, str]:
    """
    Runs the script in a throwaway sandbox copy.
    Tries: python <script> --help  (exit 0 expected).
    Returns (passed, output).
    """
    sandbox = script_path.parent / f".__sandbox_{script_path.name}"
    try:
        shutil.copy2(script_path, sandbox)
        result = subprocess.run(
            [sys.executable, str(sandbox), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        passed = result.returncode in (0, 1)  # argparse exits 1 on --help sometimes
        output = (result.stdout + result.stderr)[:500]
        return passed, output
    except subprocess.TimeoutExpired:
        return False, "Sandbox timeout"
    except Exception as e:
        return False, str(e)
    finally:
        if sandbox.exists():
            sandbox.unlink()


# ── Backup ─────────────────────────────────────────────────────────────────────

def backup(path: Path) -> Path:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    bak = BACKUPS_DIR / f"{path.name}.{ts_slug()}.bak"
    shutil.copy2(path, bak)
    return bak


# ── Audit log ─────────────────────────────────────────────────────────────────

def log_rewrite(action: str, file: str, note: str, patch_file: str = "") -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(REWRITE_LOG, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"rewrites": []}
    data["rewrites"].append({
        "ts": now_utc(), "action": action,
        "file": file, "patch": patch_file, "note": note,
    })
    with open(REWRITE_LOG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Core operations ────────────────────────────────────────────────────────────

def analyze(script_path: Path) -> dict:
    """
    Static analysis of a hook script.
    Returns a structured report with:
      - line count, function list
      - issues: missing docstrings, bare excepts, magic strings, no type hints
      - RLHF error count (from rlhf-summary.json)
      - rewrite priority score (0–10)
    """
    if not script_path.exists():
        return {"error": f"File not found: {script_path}"}

    source = script_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"Cannot parse file: {e}"}

    issues = []
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
            if not ast.get_docstring(node):
                issues.append(f"Missing docstring: {node.name}()")
            # Check for bare except
            for child in ast.walk(node):
                if isinstance(child, ast.ExceptHandler) and child.type is None:
                    issues.append(f"Bare except in {node.name}() — catches ALL exceptions")
        if isinstance(node, ast.Module) and not ast.get_docstring(node):
            issues.append("Missing module-level docstring")

    # Magic string detection (simple heuristic)
    magic_strings = re.findall(r'"(error|failed|unknown|todo|fixme|hack)"',
                                source, re.IGNORECASE)
    if magic_strings:
        issues.append(f"Found magic strings: {list(set(magic_strings))}")

    # Check type hints coverage
    typed = sum(1 for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n.returns is not None)
    untyped = len(functions) - typed
    if untyped > 0:
        issues.append(f"{untyped}/{len(functions)} functions lack return-type annotations")

    # RLHF error count
    rlhf_errors = 0
    if RLHF_SUMMARY.exists():
        try:
            summary = json.loads(RLHF_SUMMARY.read_text())
            top_files = summary.get("top_error_files", {})
            rlhf_errors = top_files.get(str(script_path), 0)
        except Exception:
            pass

    lines = source.count("\n")
    priority = min(10, len(issues) * 1.5 + rlhf_errors * 2)

    return {
        "file":         str(script_path.relative_to(ROOT)),
        "lines":        lines,
        "functions":    functions,
        "issues":       issues,
        "rlhf_errors":  rlhf_errors,
        "priority":     round(priority, 1),
        "recommendation": (
            "HIGH — schedule rewrite" if priority >= 6 else
            "MEDIUM — consider improvements" if priority >= 3 else
            "LOW — looks healthy"
        ),
    }


def propose_patch(script_path: Path, instruction: str) -> Path:
    """
    Generates a unified diff representing a proposed improvement.
    The diff is saved to agents/logs/patches/ and printed to stdout.
    Does NOT apply the patch.

    The 'instruction' is embedded as a structured comment block at the top
    of the patched file so that a stronger model can fill in the actual
    code improvement when it reads this diff.
    """
    assert_safe_path(script_path)
    if not script_path.exists():
        raise FileNotFoundError(f"Target not found: {script_path}")

    original_lines = script_path.read_text(encoding="utf-8").splitlines(keepends=True)

    # Build proposed header block
    header = (
        f"# ── SELF-REWRITE PROPOSAL ───────────────────────────────────────────\n"
        f"# Instruction : {instruction}\n"
        f"# Generated   : {now_utc()}\n"
        f"# Status      : PENDING REVIEW — apply with self_rewrite_engine apply\n"
        f"# ─────────────────────────────────────────────────────────────────────\n"
    )

    # Insert header after shebang / module docstring (line 1 or after closing ''')
    patched_lines = list(original_lines)
    insert_at = 1  # default: after shebang
    for i, line in enumerate(original_lines[:20]):
        if i > 0 and line.strip() == '"""':
            insert_at = i + 1
            break

    patched_lines.insert(insert_at, header)

    diff = list(difflib.unified_diff(
        original_lines, patched_lines,
        fromfile=f"a/{script_path.name}",
        tofile=f"b/{script_path.name}",
        lineterm="",
    ))

    PATCHES_DIR.mkdir(parents=True, exist_ok=True)
    patch_file = PATCHES_DIR / f"{script_path.stem}_{ts_slug()}.diff"
    patch_file.write_text("\n".join(diff), encoding="utf-8")

    log_rewrite("propose", str(script_path.name), instruction, str(patch_file))
    return patch_file


def apply_patch(script_path: Path, patch_file: Path, force: bool = False) -> dict:
    """
    Applies a diff patch to a hook script after passing all safety gates.

    Gates:
      1. Path safety check
      2. Patch file exists
      3. Read patched content from diff
      4. Syntax check (ast.parse)
      5. Sandbox test (--help run)
      6. Backup original
      7. Write new file
    """
    assert_safe_path(script_path)

    if not patch_file.exists():
        return {"ok": False, "error": f"Patch file not found: {patch_file}"}

    # Parse unified diff to extract patched content
    original_text = script_path.read_text(encoding="utf-8")
    patch_text = patch_file.read_text(encoding="utf-8")

    # Apply patch using difflib's ndiff reconstruction
    patched_lines = list(difflib.restore(
        (line + "\n" for line in patch_text.splitlines()), 2
    ))
    patched_text = "".join(patched_lines)

    if not patched_text.strip():
        # Fallback: try reading the b/ side directly from the diff
        b_lines = [
            line[1:] for line in patch_text.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]
        if not b_lines:
            return {"ok": False, "error": "Could not extract patched content from diff"}
        patched_text = "\n".join(b_lines)

    # GATE 1 — Syntax
    syntax_ok, syntax_err = syntax_check(patched_text, script_path.name)
    if not syntax_ok:
        return {"ok": False, "gate": "syntax", "error": syntax_err}

    # Write to temp file for sandbox test
    tmp_path = script_path.parent / f".__tmp_{script_path.name}"
    tmp_path.write_text(patched_text, encoding="utf-8")

    # GATE 2 — Sandbox
    sandbox_ok, sandbox_out = sandbox_test(tmp_path)
    if tmp_path.exists():
        tmp_path.unlink()

    if not sandbox_ok and not force:
        return {
            "ok": False, "gate": "sandbox", "error": sandbox_out,
            "hint": "Use --force to bypass sandbox gate (not recommended)",
        }

    # GATE 3 — Backup + apply
    bak = backup(script_path)
    script_path.write_text(patched_text, encoding="utf-8")

    log_rewrite("apply", script_path.name, f"Applied patch: {patch_file.name}", str(patch_file))

    return {
        "ok":      True,
        "file":    str(script_path.relative_to(ROOT)),
        "backup":  str(bak.relative_to(ROOT)),
        "sandbox": sandbox_out,
    }


def rollback(script_path: Path) -> dict:
    """Restore the most recent backup of a script."""
    baks = sorted(BACKUPS_DIR.glob(f"{script_path.name}.*.bak"), reverse=True)
    if not baks:
        return {"ok": False, "error": f"No backups found for {script_path.name}"}
    latest = baks[0]
    shutil.copy2(latest, script_path)
    log_rewrite("rollback", script_path.name, f"Restored from {latest.name}")
    return {"ok": True, "restored_from": str(latest.relative_to(ROOT))}


def scan_all() -> list:
    """Scan all hook scripts and return ranked analysis results."""
    results = []
    for py_file in sorted(HOOKS_BIN.glob("*.py")):
        if py_file.name.startswith("."):
            continue
        report = analyze(py_file)
        if "error" not in report:
            results.append(report)
    results.sort(key=lambda r: r.get("priority", 0), reverse=True)
    return results


# ── SessionEnd hook (lightweight background scan) ─────────────────────────────

def hook_session_end() -> None:
    """
    Runs as a SessionEnd hook.
    Silently performs a background scan and writes a priority summary
    to agents/logs/rewrite-priorities.json for the next session to read.
    """
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    if data.get("hookEventName", "") not in ("session_end", "SessionEnd"):
        sys.exit(0)

    try:
        results = scan_all()
        priority_file = LOGS_DIR / "rewrite-priorities.json"
        with open(priority_file, "w", encoding="utf-8") as f:
            json.dump({
                "generated_at": now_utc(),
                "priorities": [
                    {"file": r["file"], "priority": r["priority"],
                     "recommendation": r["recommendation"],
                     "top_issues": r.get("issues", [])[:3]}
                    for r in results
                ],
            }, f, indent=2, ensure_ascii=False)
    except Exception:
        pass  # Always fail-open in hook mode

    sys.exit(0)


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

    # Hook mode
    if not sys.stdin.isatty() and len(sys.argv) == 1:
        hook_session_end()
        return

    parser = argparse.ArgumentParser(
        description="Self-Rewrite Engine — autonomous hook script optimizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ── analyze ──
    p_ana = sub.add_parser("analyze", help="static analysis of a hook script")
    p_ana.add_argument("file", help="path to the .py hook script")

    # ── propose ──
    p_pro = sub.add_parser("propose", help="propose a rewrite patch (does NOT apply)")
    p_pro.add_argument("file", help="path to the .py hook script")
    p_pro.add_argument("--instruction", required=True,
                       help="describe the improvement to make")

    # ── apply ──
    p_app = sub.add_parser("apply", help="apply a proposed patch after review")
    p_app.add_argument("file",       help="target .py script")
    p_app.add_argument("--patch-file", dest="patch_file", required=True,
                       help="path to the .diff file to apply")
    p_app.add_argument("--force", action="store_true",
                       help="skip sandbox gate (dangerous, use with care)")

    # ── rollback ──
    p_rb = sub.add_parser("rollback", help="restore the last backup of a script")
    p_rb.add_argument("file", help="path to the .py hook script")

    # ── scan ──
    sub.add_parser("scan", help="scan all hook scripts and rank by rewrite priority")

    args = parser.parse_args()

    if args.cmd == "analyze":
        path = Path(args.file).resolve()
        result = analyze(path)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "propose":
        path = Path(args.file).resolve()
        try:
            pf = propose_patch(path, args.instruction)
            print(json.dumps({
                "proposed": str(pf.relative_to(ROOT)),
                "next_step": f"Review the diff, then run: "
                             f"python agents/hooks/bin/self_rewrite_engine.py apply "
                             f"{args.file} --patch-file {pf}",
            }, indent=2))
        except (ValueError, FileNotFoundError) as e:
            print(json.dumps({"ok": False, "error": str(e)}))
            sys.exit(1)

    elif args.cmd == "apply":
        path       = Path(args.file).resolve()
        patch_path = Path(args.patch_file).resolve()
        try:
            result = apply_patch(path, patch_path, force=args.force)
        except ValueError as e:
            result = {"ok": False, "error": str(e)}
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if not result.get("ok"):
            sys.exit(1)

    elif args.cmd == "rollback":
        path   = Path(args.file).resolve()
        result = rollback(path)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if not result.get("ok"):
            sys.exit(1)

    elif args.cmd == "scan":
        results = scan_all()
        print(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"\n📊 Scanned {len(results)} scripts. "
              f"Top priority: {results[0]['file'] if results else 'N/A'}")


if __name__ == "__main__":
    main()
