---
name: auto-fix
description: Automatically find and fix all detectable issues in the codebase — broken tests, lint errors, type errors, missing imports
when_to_use: Use when user says "fix all errors", "clean up the code", "fix everything", "auto-fix"
short_description: Auto-detect and fix all issues
argument_hint: (optional) area to fix: tests | lint | types | imports | all
allowed_tools: [read_file, grep, list_dir, search_replace, write_file, run_terminal_cmd]
user_invocable: true
disable_model_invocation: false
enabled: true
---

# Auto-Fix Skill

Systematically finds and fixes all detectable issues.
Runs health-check first, then fixes in priority order.

## Fix Protocol

### Phase 1: Detect (token-efficient scan)
```
1. Run test suite → collect failing tests
2. Run linter → collect lint errors
3. Run type checker → collect type errors
4. Read agents/logs/error-patterns.json → check recurring patterns
```
Count total issues. If > 20, ask user which area to focus on.

### Phase 2: Prioritize
Fix in this order:
1. 🔴 Build failures (can't run anything until fixed)
2. 🔴 Test failures (broken correctness)
3. 🟡 Type errors (latent bugs)
4. 🟡 Lint errors (code quality)
5. 🟢 Style/formatting (cosmetic)

### Phase 3: Fix Loop (for each issue)
```
FOR each issue:
  1. READ the failing file (only relevant lines)
  2. UNDERSTAND root cause (don't guess)
  3. APPLY minimal fix (search_replace, not full rewrite)
  4. RUN the specific test/check that failed
  5. IF still failing: try once more, then move to next issue
  6. UPDATE todo list (mark done)
```

### Known Auto-Fix Playbooks

**Unused import** (lint):
```python
# Remove the import line
search_replace("from foo import Bar\n", "")
```

**Missing type annotation** (mypy/tsc):
```python
# Add annotation based on usage context
def func(x) → def func(x: int)
```

**Unreachable code** (after return):
```python
# Remove dead code lines
```

**Deprecated API** (lint warning):
```python
# Replace with current API from docs
requests.get(url, verify=False) → requests.get(url, verify=certifi.where())
```

**Test import error** (test can't import):
```python
# Fix import path based on project structure
from app import X → from src.app import X
```

**Missing __init__.py** (Python import error):
```python
# Create empty __init__.py
write_file("src/module/__init__.py", "")
```

### Phase 4: Report
```
## Auto-Fix Results

### Fixed (N)
- [issue description] → [fix applied]

### Skipped (N) — requires manual review
- [issue]: [why it needs human decision]

### Stats
Before: N tests failing, N lint errors, N type errors
After:  N tests failing, N lint errors, N type errors
```

## Safety Rules
- NEVER fix a failing test by deleting the test (fix the code instead)
- NEVER change behavior to make a test pass (understand what the test expects)
- NEVER auto-fix if the fix requires a design decision — report and ask user
- ALWAYS run tests after fixing to confirm no regression
