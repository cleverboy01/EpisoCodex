# Self-Healing & Proactive Problem Detection Spec
# Pattern distilled from: xai-grok-shell hooks, memory, subagents (xai-org/grok-build)

## What is Self-Healing?
The agent proactively finds issues WITHOUT being asked, then fixes them.
This is the key leap from "reactive tool" to "AGI-like assistant."

## Self-Healing Architecture
```
PostToolUse Hook (passive)
    └─► error_pattern_tracker.py
            └─► writes to: agents/logs/error-patterns.json
                    └─► health_check skill reads this
                            └─► if patterns found → trigger fix subagent
```

## Four Self-Healing Layers

### Layer 1: Continuous Error Pattern Tracking (PostToolUse hook)
Every tool failure is silently logged with:
- Tool name, error type, error message
- File path (if applicable)
- Timestamp, session ID
- Pattern frequency (how often this error recurs)

### Layer 2: Proactive Health Check (runs at session start)
Before any user task, quickly scan for:
- Broken tests (run test suite, check exit code)
- Lint errors (run linter, count errors)
- Type errors (run type checker, count failures)
- Missing dependencies (check package manifest vs installed)
- Stale lock files (check if any process lock files are old)
- Uncommitted changes older than N hours

### Layer 3: Self-Diagnosis (on tool failure)
When a tool fails 2+ times on the same error:
1. Search memory for this error pattern
2. Check error-patterns.json for similar failures
3. Attempt auto-fix from known patterns:
   - `ModuleNotFoundError` → install missing dependency
   - `SyntaxError` → read file, fix syntax
   - `TypeError` → read type annotation, fix mismatch
   - `ENOENT` (file not found) → check path, fix or create
   - `Permission denied` → check file permissions
4. If fixed: write to memory "error X → fix Y"
5. If not fixed: report with full diagnosis

### Layer 4: Requirements Generation (proactive)
At session start or when codebase changes significantly:
1. Scan entrypoints and key files
2. Infer current system behavior
3. Compare to: existing tests, existing docs, existing AGENTS.md
4. Identify gaps:
   - Untested code paths
   - Undocumented functions
   - Functions doing more than their name suggests (scope creep)
   - Missing error handling
5. Write gaps to agents/requirements/REQUIREMENTS.md

## Self-Healing Playbooks (Known Error → Known Fix)

### Missing dependency
```
Error: ModuleNotFoundError: No module named 'requests'
Diagnosis: package in code but not in requirements.txt / pyproject.toml
Fix:
  1. Check what's imported vs what's installed
  2. Add to requirements.txt / pyproject.toml
  3. Run: pip install -r requirements.txt
  4. Re-run failing test to confirm
```

### Test failure after recent edit
```
Error: AssertionError in test_auth.py::test_login
Diagnosis: recent change broke existing test
Fix:
  1. git diff HEAD~1 -- src/auth.py  (find the change)
  2. Read the test to understand expectation
  3. Either: fix the code to match test intent
     Or: update test if behavior change was intentional
  4. Confirm by running test
```

### Import cycle / circular dependency
```
Error: ImportError: cannot import name X from Y (circular import)
Diagnosis: module A imports B which imports A
Fix:
  1. Map the import chain with grep
  2. Extract shared code to a third module C
  3. Have A and B import from C instead
```

### Type mismatch
```
Error: TypeError / mypy error
Fix:
  1. Read the function signature
  2. Read the call site
  3. Add type annotation or fix the type
```

### Stale process / port in use
```
Error: EADDRINUSE: port 3000 already in use
Fix:
  1. lsof -i :3000 (find process)
  2. If it's a stale dev server: kill it
  3. Restart the server
```

## Proactive Scan Checklist
Run this at session start (takes < 5 seconds, near-zero tokens):
```python
checks = [
    ("tests", "run_test_command --dry-run"),      # detect failures
    ("lint", "run_linter --format=count"),         # count errors
    ("types", "run_type_checker --error-only"),    # type errors
    ("deps", "check_lockfile_vs_installed"),       # missing deps
    ("git", "git status --short"),                 # uncommitted
]
# Only report issues, not successes → near-zero output
```

## Requirements Generation Protocol
1. Read: entry points (`main.py`, `src/main.rs`, `index.ts`)
2. Read: existing tests (what behaviors are covered)
3. Read: existing docs (README, docstrings)
4. Analyze: coverage gaps, undocumented functions, missing tests
5. Generate: structured requirements in REQUIREMENTS.md

### Requirements Format
```markdown
# System Requirements

## Functional Requirements (inferred from code)
- FR-001: [verb] [noun] — [source: file.py:function_name]
- FR-002: ...

## Missing Tests (coverage gaps)
- MT-001: [function_name] in [file] has no test
- MT-002: ...

## Missing Documentation
- MD-001: [function_name] has no docstring
- MD-002: ...

## Technical Debt
- TD-001: [description] — [file:line]
```
