---
name: create-skill
description: Synthesize a brand-new skill (tool + SKILL.md + tests) when no existing skill matches the task, then install and index it
when_to_use: Use when the skill-router finds no matching skill, or the user asks to add a new capability to the agent system
short_description: Self-evolve - write a new skill
argument_hint: description of the missing capability
allowed_tools: [read_file, grep, list_dir, search_replace, write_file, run_terminal_cmd]
user_invocable: true
disable_model_invocation: false
enabled: true
---

# Create-Skill (Tool Synthesis)

Grows the skill library autonomously — the core self-evolution loop.

## Protocol
1. **Gap check**: `python agents/hooks/bin/skill_router.py "<capability>"` — abort if an adequate skill already exists (upgrade it instead).
2. **Recall**: `python agents/hooks/bin/episodic_memory.py query "<capability>"` for prior lessons.
3. **Scaffold**: create `agents/skills/<kebab-name>/` containing:
   - helper script(s) — Python, stdlib-first, no destructive shell access
   - `SKILL.md` with standard frontmatter (name, description, when_to_use, short_description, argument_hint, allowed_tools, user_invocable, enabled)
4. **Verify in sandbox**: `python agents/hooks/bin/sandbox_runner.py --cmd "<test command>"` — must return verdict `ok` before install.
5. **Critic review**: submit the plan + diff to the critic agent; only proceed on APPROVE.
6. **Index**: `python agents/hooks/bin/skill_indexer.py` to register the new skill.
7. **Reflect**: `python agents/hooks/bin/episodic_memory.py store --task "create-skill <name>" --outcome success --lessons "<what worked>" --tags skill-synthesis`

## Output
```
Skill: <name> at agents/skills/<name>/
Verification: <sandbox command + verdict>
Indexed: yes (skill-index.json rebuilt)
```
