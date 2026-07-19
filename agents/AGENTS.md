# AGENTS.md — AGI Harness Index
# Source: xai-org/grok-build (Apache 2.0)
# Purpose: Zero-token-waste IDE context for AI agents

## How This Kit Works

```
agents/
├── .cursorrules          ← Load into Cursor/Windsurf (always-active harness rules)
├── AGENTS.md             ← This file (for AI agents reading repo structure)
├── specs/                ← Load ON-DEMAND when task requires it
├── skills/               ← Available slash commands
│   ├── safe-commit/      ← /safe-commit [message]
│   ├── explain-code/     ← /explain-code [path]
│   ├── add-tests/        ← /add-tests [file]
│   ├── debug/            ← /debug [issue description]
│   ├── deploy/           ← /deploy [environment]
│   ├── document/         ← /document [file]
│   ├── pr-description/   ← /pr-description [branch]
│   ├── create-skill/     ← /create-skill [capability] (self-evolution)
│   ├── reflect/          ← /reflect [task summary] (episodic memory)
│   ├── sandbox-run/      ← /sandbox-run [command] (simulate before acting)
│   ├── proactive-scan/   ← /proactive-scan [focus] (autonomous goals)
│   └── chunk-optimize/   ← /chunk-optimize [cmd] [file] (AST chunk-based editing)
├── agent-definitions/    ← Specialized sub-agents
│   ├── code-reviewer.md  ← Reviews code quality/security
│   ├── researcher.md     ← Background research (runs in parallel)
│   ├── test-writer.md    ← Writes comprehensive tests
│   ├── debugger.md       ← Systematic bug investigation
│   ├── refactorer.md     ← Safe code restructuring
│   ├── skill-router.md   ← Selects minimal skill set per task (Phase 1)
│   ├── meta-agent.md     ← Synthesizes new skills (Phase 2)
│   ├── critic.md         ← System-2 adversarial plan review (Phase 4)
│   └── goal-generator.md ← Proactive task generation (Phase 5)
└── hooks/                ← Safety guards (PreToolUse)
    ├── agent-hooks.json  ← Hook configuration
    └── bin/
        ├── safe_shell_guard.py  ← Blocks destructive commands
        ├── tool_logger.py       ← Logs tool activity
        ├── session_log.py       ← Session audit log
        ├── skill_indexer.py     ← Builds logs/skill-index.json (Phase 1)
        ├── skill_router.py      ← Ranks relevant skills per task (Phase 1)
        ├── episodic_memory.py   ← SQLite experience ledger (Phase 3)
        └── sandbox_runner.py    ← Runs commands in workspace copy (Phase 4)
```

## Proto-AGI Cognitive Layer

This harness implements five cognitive upgrades on top of the base kit:

1. **Dynamic Skill Retrieval** — Never load all skills. Route first:
   `python agents/hooks/bin/skill_router.py "<task>" --top-k 3`, then read only
   the returned SKILL.md paths. Index auto-rebuilds at SessionStart.
2. **Self-Evolution** — If routing finds no matching skill, invoke the
   meta-agent (`agent-definitions/meta-agent.md`) or `/create-skill` to write,
   test, document, and install a new skill.
3. **Episodic Memory** — Before starting: `python agents/hooks/bin/episodic_memory.py query "<task>"`.
   After finishing: store a post-mortem via `/reflect`. SessionEnd auto-captures decisions.
4. **System-2 Thinking** — Risky plans and commands go through the critic
   (`agent-definitions/critic.md`) and are simulated first with `/sandbox-run`.
5. **Proactive Agency** — When idle, run `/proactive-scan` (or the goal-generator
   agent) to discover debt/bugs and build a prioritized, approval-gated task queue.

**Safety invariants**: all execution loops pass through `safe_shell_guard.py`;
irreversible actions require sandbox evidence + critic approval; `needs-approval`
tasks always wait for the user.

## For AI Agents: Token-Efficient Reading Protocol

**DO NOT** load all spec files at startup. Load them ON-DEMAND:

```
Task type                  → Load spec
─────────────────────────────────────────────────
Designing agent reasoning  → specs/agent_loop.md
Adding/modifying tools     → specs/tools.md
Creating slash commands    → specs/skills.md
Adding safety guards       → specs/hooks.md
RAG / semantic search      → specs/memory.md
Parallel agents            → specs/subagents.md
Safe code execution        → specs/sandbox.md
Token management           → specs/token_optimization.md
MCP / ACP / plugins        → specs/protocols.md
Security / secrets         → specs/security.md
Agent definition files     → specs/agent_definition.md
System prompt engineering  → specs/system_prompt.md
Symbol navigation          → specs/codebase_graph.md
Goal mode / orchestration  → specs/orchestration.md
Todo / task tracking       → specs/todo_system.md
Dreaming / consolidation   → specs/dreaming.md
Self-healing loops         → specs/self_healing.md
```

**Skill loading is dynamic**: consult `logs/skill-index.json` (via
`hooks/bin/skill_router.py`) instead of reading every SKILL.md.

## Core Rules (Mandatory for All Agents)

1. **Search before read**: grep/search to find relevant code, then read only those lines.
2. **Read before write**: always read a file before editing it.
3. **Checkpoint before destructive ops**: `git stash` or file copy before deletion.
4. **Verify after change**: run tests/lint to confirm correctness.
5. **Summarize large outputs**: don't dump 500 lines into context — summarize.
6. **Self-correct on failure**: retry 3x with adjusted approach before asking user.
7. **Update todo list**: for tasks with 3+ steps, use todo_write to track progress.

## Project-Specific Instructions

[Add your project's coding conventions, test requirements, and build commands here.]

Example:
- Run tests: `npm test` / `pytest` / `cargo test`
- Lint: `npm run lint` / `ruff check .` / `cargo clippy`
- Build: `npm run build` / `python -m build` / `cargo build`
- Branch naming: `feat/`, `fix/`, `chore/`
- Commit format: Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`)
