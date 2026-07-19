# Skills Spec
# Source: xai-grok-tools/src/implementations/skills/ (xai-org/grok-build)

## What is a Skill?
A Skill is a markdown file (`SKILL.md`) that defines a reusable slash command.
Users invoke it as `/skill-name [arguments]`. The model can also auto-invoke skills.

## Directory Structure
```
~/.grok/skills/            # User-global skills (Scope: User)
<repo>/.grok/skills/       # Repo-level skills (Scope: Repo)
<cwd>/.grok/skills/        # Project-local skills (Scope: Local) ← highest priority
~/.grok/server-skills/     # Synced from skill store (Scope: Server)
<platform>/bundled/        # Platform built-in (Scope: Bundled) ← lowest priority
<plugin>/skills/           # Plugin-provided (Scope: Plugin) ← lowest for bare-name
```

## Priority Order (lower number = higher priority)
```
Local (0) > Repo (1) > User (2) > Server (3) > Bundled (4) > Plugin (5)
```

## SKILL.md Format
```markdown
---
name: deploy
description: Deploy the current project to production
when_to_use: Use when the user asks to deploy, ship, or push to production
short_description: Deploy to prod
author: Your Name
argument_hint: environment name (e.g. staging, production)
compatibility: Requires git, docker, kubectl
allowed_tools: [run_terminal_cmd, read_file]
model: grok-3  # optional model override
effort: high   # optional reasoning effort
user_invocable: true
disable_model_invocation: false
enabled: true
---

# Deploy Skill

This skill deploys the project. Steps:
1. Run tests
2. Build Docker image
3. Push to registry
4. Apply k8s manifests
```

## Key SkillInfo Fields
```
name             → slash command identity (/name)
display_name     → UI label (falls back to name)
description      → shown in listing, used for model matching
when_to_use      → trigger phrases for auto-invocation
paths            → glob patterns; skill hidden until matching file is touched
allowed_tools    → restrict which tools this skill can use
model            → override the active model for this skill's execution
user_invocable   → if false, not shown in /skill listing
disable_model_invocation → if true, ONLY user can trigger (not auto-invoked)
enabled          → if false, excluded from system prompt and tool
```

## Skill Name Resolution
- Path: `skills/<name>/SKILL.md`
- Name extracted from parent directory (e.g. `/skills/deploy/SKILL.md` → `deploy`)
- Plugin skills keyed as `plugin:<name>` to prevent namespace collision
- Same-scope collision: loser gets directory basename, winner keeps frontmatter name

## Best Practices
1. Write clear `when_to_use` for reliable auto-invocation.
2. Use `allowed_tools` to restrict blast radius.
3. Use `paths` to conditionally show skills (e.g. only show docker skill if Dockerfile exists).
4. Keep skill body concise — it goes into system prompt (token cost!).
5. Set `disable_model_invocation: true` for dangerous skills.
