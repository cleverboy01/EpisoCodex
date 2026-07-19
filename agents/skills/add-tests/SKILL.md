---
name: add-tests
description: Add unit tests and integration tests for existing code with coverage
when_to_use: Use when user asks to add tests, improve coverage, or test a specific module
short_description: Write tests with coverage
argument_hint: file or module to test
allowed_tools: [read_file, list_dir, grep, search_replace, write_file, run_terminal_cmd]
user_invocable: true
disable_model_invocation: false
enabled: true
---

# Add Tests Skill

Writes comprehensive tests for existing code, matching project conventions.

## Discovery Phase
1. Identify the target file/module
2. Find existing test files (look for `tests/`, `__tests__/`, `*.test.*`, `*_test.*`, `*_spec.*`)
3. Detect testing framework:
   - JS/TS: Jest, Vitest, Mocha, Jasmine
   - Python: pytest, unittest
   - Rust: built-in `#[test]`, `#[tokio::test]`
   - Go: `testing` package
   - Java: JUnit, TestNG

## Test Writing Protocol
For each public function/method/endpoint:
1. Happy path (expected input → expected output)
2. Edge cases (empty input, max values, boundary conditions)
3. Error cases (invalid input, missing required fields, failure modes)
4. Async behavior (if applicable)

## Conventions
- Match the style and naming of existing tests EXACTLY
- Test names: `should_do_X_when_Y` or `test_X_returns_Y_given_Z`
- No hardcoded values: use constants or fixtures
- Mock external deps (HTTP, DB, FS, time)
- One behavior per test (not "test everything in one test")

## Verification
Run tests after writing. Fix any that fail.
Report: total tests added, coverage delta if measurable.
