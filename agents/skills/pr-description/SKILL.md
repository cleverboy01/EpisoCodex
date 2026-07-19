---
name: pr-description
description: Generate a clear, detailed pull request description from git diff and commit history
when_to_use: Use when user wants to create a PR, needs a PR description, or asks to prepare code for review
short_description: Generate PR description
argument_hint: branch or commit range (optional; defaults to current branch vs main)
allowed_tools: [run_terminal_cmd, read_file, grep]
user_invocable: true
disable_model_invocation: false
enabled: true
---

# PR Description Skill

Generates a clear, reviewable PR description from actual code changes.

## Steps
1. Get diff: `git diff main...HEAD` or `git diff <range>`
2. Get commits: `git log main..HEAD --oneline`
3. Read changed files to understand context (briefly)
4. Generate structured description

## Output Format
```markdown
## Summary
[One paragraph: what this PR does and why]

## Changes
- **`src/auth/handler.rs`**: [what changed and why]
- **`src/auth/middleware.rs`**: [what changed and why]
- **`tests/auth_test.rs`**: [what was tested]

## Testing
[How to test this PR: commands, test cases, manual steps]

## Screenshots / Output
[If UI changes or command output is relevant]

## Related Issues
Closes #[issue-number] (if applicable)

## Breaking Changes
[None / describe any breaking API or behavior changes]
```

## Quality Rules
- Write in complete sentences, not bullet fragments
- Explain WHY the change was made, not just WHAT changed
- Mention any trade-offs or alternatives considered
- Keep it concise: reviewers read many PRs
