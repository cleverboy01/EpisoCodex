# Agent Definition Spec (AGENTS.md system)
# Source: xai-grok-agent/README.md, templates/ (xai-org/grok-build)

## What is an Agent Definition?
A Markdown file with YAML frontmatter that defines a specialized AI agent.
Stored in `.grok/agents/` (project) or `~/.grok/agents/` (user).
Discovered automatically by the harness at session start.

## Discovery Priority (highest → lowest)
```
.grok/agents/*.md        (project-level, closest to cwd wins)
~/.grok/agents/*.md      (user-level)
built-in agents          (grok-build, browser-use)
```
Name-based dedup: highest-priority file wins when names collide.

## File Format
```markdown
---
name: code-reviewer           # REQUIRED: unique ID (lowercase-hyphen)
description: Reviews code for quality and security  # REQUIRED: when/why to use
promptMode: extend            # "extend" (default) or "full"
tools:                        # allowlist; omit = all tools; [] = none
  - read_file
  - grep
  - list_dir
disallowedTools:              # denylist (takes priority over tools)
  - run_terminal_cmd
permissionMode: plan          # "default" | "acceptEdits" | "dontAsk" | "plan"
skills:                       # pre-load specific skills
  - safe-commit
agentsMd: true                # auto-inject AGENTS.md files (default: true)
outputFormat: default         # "default" or "concise"
bash:
  timeoutSecs: 120.0
  outputByteLimit: 200000
completionRequirement:        # tool MUST be called before turn ends
  tool: complete_task
  reminder: "You stopped without calling complete_task."
  recovery:
    maxRetries: 5
    baseDelayMs: 5000
    maxDelayMs: 60000
---

You are a senior code reviewer. Focus on:
- Security vulnerabilities
- Performance bottlenecks
- Code clarity and maintainability
```

## Prompt Modes
### extend (default)
Body is APPENDED to the base template which includes:
- Tool calling conventions
- Action safety rules
- Output formatting rules
- User environment info

### full
Body IS the complete system prompt.
Use MiniJinja template variables `${{ }}` and `${% %}`:

```markdown
---
name: custom-agent
description: Custom full-control agent
promptMode: full
tools: [read_file, search_replace, run_terminal_cmd]
---

You are a custom agent.

Use ${{ tools.read_file }} to read files.
${%- if tools.run_terminal_cmd %}
Use ${{ tools.run_terminal_cmd }} for shell commands.
${%- endif %}

<user_info>
OS: ${{ os_name }}
Shell: ${{ shell_path }}
CWD: ${{ working_directory }}
Date: ${{ current_date }}
</user_info>
```

## Template Variables (full mode)
| Variable | Value |
|----------|-------|
| `${{ tools.read_file }}` | Resolved tool name (empty if disabled) |
| `${{ tools.search_replace }}` | Resolved edit tool name |
| `${{ tools.run_terminal_cmd }}` | Resolved shell tool name |
| `${{ tools.grep }}` | Resolved search tool name |
| `${{ tools.list_dir }}` | Resolved list tool name |
| `${{ tools.skill }}` | Resolved skill tool name |
| `${{ os_name }}` | Operating system |
| `${{ shell_path }}` | Shell path |
| `${{ working_directory }}` | Workspace path |
| `${{ current_date }}` | Today's date (YYYY-MM-DD) |

## Permission Modes
| Mode | Behavior |
|------|----------|
| `default` | Standard permission prompts for destructive ops |
| `acceptEdits` | Auto-approve file edits, still prompt for shell |
| `plan` | No edits until user approves plan |
| `dontAsk` | Skip all confirmations (use carefully) |

## Completion Requirement Pattern (Orchestrated Agents)
For worker agents in multi-agent pipelines that MUST signal completion:
```yaml
completionRequirement:
  tool: complete_task
  reminder: "You stopped without calling complete_task. Continue and call it."
  recovery:
    maxRetries: 5
    baseDelayMs: 5000
    maxDelayMs: 60000
```
The harness injects the reminder as a `<system-reminder>` and forces another turn
if the model stops without calling the required tool.

## AGENTS.md Project Instructions (agentsMd: true)
Any file named `AGENTS.md`, `Agents.md`, `Claude.md`, or `AGENT.md` in the repo
is automatically injected into the system prompt.
- Scope = entire directory tree rooted at the containing folder
- Deeply-nested files take precedence over parent files
- Direct user instructions always override AGENTS.md content

## Built-in Agents
| Name | Mode | Description |
|------|------|-------------|
| `grok-build` | extend | Default software engineering agent |
| `browser-use` | full | Web browsing agent |
