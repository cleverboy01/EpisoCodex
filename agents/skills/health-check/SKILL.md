---
name: health-check
description: Proactively scan the project for broken tests, lint errors, missing deps, type errors, and other issues WITHOUT being asked
when_to_use: Use at session start or when user says "check the project", "is everything ok?", "run health check", "find problems". Also invoke automatically before major changes.
short_description: Proactive project health scan
argument_hint: (optional) specific area to check: tests | lint | types | deps | all
allowed_tools: [run_terminal_cmd, read_file, list_dir, grep]
user_invocable: true
disable_model_invocation: false
enabled: true
---

# Health Check Skill

Proactively scans the project for problems WITHOUT being asked.
Near-zero token cost — only reports issues, not successes.

## Scan Protocol (Run in Parallel)

### 1. Check error patterns log (1 tool call, instant)
```
read_file("agents/logs/error-patterns.json")
```
If recurring errors exist (count > 2) → report them first.

### 2. Run test suite
```
detect test command:
  package.json → "test" script? → npm test
  pytest.ini / pyproject.toml → pytest
  Cargo.toml → cargo test
  go.mod → go test ./...
  Makefile → make test
```
Show ONLY: failure count, failed test names, first error line.
Skip all passing tests output.

### 3. Run linter
```
detect linter:
  .eslintrc* → npx eslint . --format=compact
  .ruff.toml / ruff.toml → ruff check . --output-format=concise
  Cargo.toml → cargo clippy -- -D warnings 2>&1 | grep "^error"
  .golangci* → golangci-lint run --concise-output
```
Show ONLY: error count + first 5 errors.

### 4. Check types (if applicable)
```
tsconfig.json → tsc --noEmit 2>&1 | grep "error TS"
mypy.ini / .mypy.ini → mypy src/ --no-error-summary
```

### 5. Check dependencies
```
package.json → node -e "require('./package.json')" (basic check)
requirements.txt → pip check 2>&1 | head -5
Cargo.toml → cargo check 2>&1 | grep "^error"
```

### 6. Check git state
```
git status --short | wc -l  → count uncommitted files
git stash list | wc -l      → count stashed changes
```

## Output Format (Minimal — Only Issues)
```
## Health Check — [timestamp]

### 🔴 Critical Issues (N)
- [issue]: [brief description]

### 🟡 Warnings (N)  
- [issue]: [brief description]

### 📊 Stats
- Tests: N passed, N failed
- Lint: N errors, N warnings
- Uncommitted: N files

### 🔄 Recurring Error Patterns
- [category]: N occurrences → suggest: [fix]
```

If no issues: output exactly:
```
✅ Project healthy — 0 issues found.
```

## Self-Healing Actions
After reporting issues, optionally auto-fix if user consents or if fix is trivially safe:
- Missing dev dependency → offer to install
- Formatting error → run formatter
- Stale process lock → offer to clear
