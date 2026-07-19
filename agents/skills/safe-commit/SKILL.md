---
name: safe-commit
description: Stage all changes, run tests, and create a conventional commit
when_to_use: Use when the user wants to commit code, save progress, or says "commit", "save changes", "push"
short_description: Safe git commit with tests
argument_hint: commit message (e.g. "feat: add user auth")
compatibility: Requires git, and a test runner (npm test / pytest / cargo test)
allowed_tools: [run_terminal_cmd, read_file, list_dir]
user_invocable: true
disable_model_invocation: false
enabled: true
---

# Safe Commit Skill

Stages changes, runs tests, and commits with a conventional message.

## Steps

1. **Check status**: `git status` to see what changed.
2. **Run tests**: detect and run the project's test command.
   - Node.js: `npm test` or `yarn test`
   - Python: `pytest` or `python -m unittest`
   - Rust: `cargo test`
   - Go: `go test ./...`
3. **If tests pass**: stage all changes with `git add -A`.
4. **Commit** with the provided message using [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` new feature
   - `fix:` bug fix
   - `refactor:` code refactor
   - `docs:` documentation
   - `chore:` maintenance
5. **Report**: show the commit hash and summary.

## Rules
- NEVER commit if tests fail. Report the failure instead.
- NEVER commit secrets or API keys (check with `git diff --staged` first).
- If no message provided, generate one from the diff summary.
