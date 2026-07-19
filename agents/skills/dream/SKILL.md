---
name: dream
description: Consolidate session logs into permanent memory — run the Dreaming background loop manually
when_to_use: Use when user wants to "consolidate memory", "update knowledge base", "summarize sessions", or when memory search is returning stale/missing results
short_description: Consolidate session memory
argument_hint: (optional) specific topic to focus consolidation on
allowed_tools: [read_file, write_file, list_dir, run_terminal_cmd]
user_invocable: true
disable_model_invocation: false
enabled: true
---

# Dream Skill

Manually triggers the Dreaming consolidation loop.
Reads recent session logs → merges into permanent MEMORY.md.

## When to Use
- After 5+ sessions working on the same project
- When memory search returns outdated information
- When you want to preserve key decisions before a major refactor
- When context window is getting large (consolidate before it compacts)

## Consolidation Protocol

### Step 1: Check session logs
```
list_dir("~/.grok/memory/{workspace_hash}/sessions/")
→ find all session files not yet consolidated
```

### Step 2: Read existing MEMORY.md (brief summary)
```
read_file("~/.grok/memory/{workspace_hash}/MEMORY.md")
→ understand current knowledge state
```

### Step 3: Read session logs (chronological, max 32K chars total)
Read each session file and extract:
- Decisions made
- Problems solved + solutions
- Architecture discoveries
- Conventions confirmed
- Dead ends (what didn't work)

### Step 4: Apply Dream System Prompt rules
```
MERGE related info into coherent ## sections
RESOLVE contradictions (keep newest truth)
CONVERT relative dates → absolute dates
DISCARD:
  - Greetings, meta-commentary
  - Tool output noise
  - Session metadata (message counts, timestamps)
  - 'Current state' / 'Next steps' sections
PRESERVE:
  - Decisions + rationale
  - Architecture choices
  - Problem/solution pairs
  - Performance/security discoveries
  - Coding conventions for this project
```

### Step 5: Write consolidated MEMORY.md
Format:
```markdown
# Project Memory — {project_name}
Last consolidated: {date}

## Architecture
[Key decisions about system structure]

## Conventions
[Coding patterns, naming, test requirements]

## Known Issues & Solutions
[Problem → root cause → solution pairs]

## Performance Notes
[What's fast, what's slow, why]

## Security Notes
[Auth patterns, secrets handling, access control]

## Dead Ends
[What was tried and didn't work — prevents repeating mistakes]
```

### Step 6: Report
```
Consolidated N session logs
Memory size: X KB → Y KB
Key topics preserved: [list]
Session files cleaned: N
```

## Token Budget
- Reading 5 session logs: ~1000 tokens
- Writing MEMORY.md: ~500 tokens
- **Total: ~1500 tokens for full consolidation** — pay once, save 10x future
