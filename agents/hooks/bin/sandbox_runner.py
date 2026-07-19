#!/usr/bin/env python3
"""
Sandbox Runner (Phase 4: Imagination / Hypothesis Testing)
Runs risky or untested shell commands in a throwaway COPY of the workspace,
so agents can simulate consequences before touching the real project.

Usage:
    python agents/hooks/bin/sandbox_runner.py --cmd "pytest -q"
    python agents/hooks/bin/sandbox_runner.py --cmd "python migrate.py" --include src --include tests
    python agents/hooks/bin/sandbox_runner.py --cmd "..." --keep   # keep sandbox for inspection

Output (JSON): {"verdict": "ok|failed|blocked", "exit_code": ..., "sandbox": ..., "stdout": ..., "stderr": ...}
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
EXCLUDE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".sandbox"}

# Same destructive patterns as safe_shell_guard.py — even a sandbox refuses these.
DESTRUCTIVE_PATTERNS = [
    r'rm\s+-[a-zA-Z]*r[a-zA-Z]*f\s+/',
    r'rm\s+-[a-zA-Z]*f[a-zA-Z]*r\s+/',
    r'sudo\s+rm\s+-r',
    r'mkfs\.',
    r'dd\s+.*of=/dev/[sh]d',
    r':\(\)\{.*\}',
    r'>\s*/etc/passwd',
    r'chmod\s+-R\s+777\s+/',
    r'>\s*/dev/[sh]d',
    r'shred\s+.*/',
]


def is_blocked(command: str) -> bool:
    return any(re.search(p, command, re.IGNORECASE) for p in DESTRUCTIVE_PATTERNS)


def copy_workspace(includes: list) -> str:
    sandbox = tempfile.mkdtemp(prefix="agent-sandbox-")
    sources = includes if includes else [
        n for n in os.listdir(WORKSPACE) if n not in EXCLUDE_DIRS
    ]
    for name in sources:
        src = os.path.join(WORKSPACE, name)
        dst = os.path.join(sandbox, name)
        if os.path.isdir(src):
            shutil.copytree(
                src, dst,
                ignore=shutil.ignore_patterns(*EXCLUDE_DIRS),
                dirs_exist_ok=True,
            )
        elif os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
    return sandbox


def main():
    parser = argparse.ArgumentParser(description="Run a command in an isolated workspace copy")
    parser.add_argument("--cmd", required=True, help="shell command to test")
    parser.add_argument("--include", action="append", default=[], help="limit copy to specific top-level paths")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--keep", action="store_true", help="do not delete the sandbox afterwards")
    args = parser.parse_args()

    if is_blocked(args.cmd):
        print(json.dumps({"verdict": "blocked", "reason": "destructive command pattern", "cmd": args.cmd[:100]}))
        sys.exit(2)

    sandbox = copy_workspace(args.include)
    try:
        proc = subprocess.run(
            args.cmd, shell=True, cwd=sandbox, capture_output=True,
            text=True, timeout=args.timeout,
        )
        report = {
            "verdict": "ok" if proc.returncode == 0 else "failed",
            "exit_code": proc.returncode,
            "sandbox": sandbox if args.keep else None,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
        }
    except subprocess.TimeoutExpired:
        report = {"verdict": "failed", "exit_code": -1, "sandbox": sandbox if args.keep else None,
                  "stdout": "", "stderr": f"timeout after {args.timeout}s"}
    finally:
        if not args.keep:
            shutil.rmtree(sandbox, ignore_errors=True)

    print(json.dumps(report, ensure_ascii=False))
    sys.exit(0 if report["verdict"] == "ok" else 1)


if __name__ == "__main__":
    main()
