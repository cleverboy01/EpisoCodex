# Dreaming & Self-Improvement Loop Spec
# Source: xai-grok-memory/src/dream.rs, watcher.rs (xai-org/grok-build)

## What is Dreaming?
"Dreaming" is background knowledge consolidation — the agent reflects on recent
session logs and merges them into durable, structured memory during idle time.
This is the core AGI self-improvement mechanism in grok-build.

## Dream System Prompt (exact from source)
```
You are performing a dream — a reflective pass over memory files.
Synthesize recent session logs into durable, well-organized memories
so future sessions orient quickly.

1. MERGE related information into coherent topic summaries
2. RESOLVE contradictions — if a recent session disproves an older fact, keep only the current truth
3. CONVERT relative dates ("yesterday", "last week") to absolute dates
4. DISCARD ephemeral details:
   - Greetings, meta-commentary, tool output noise
   - Message counts and tool-usage statistics
   - 'Current state' and 'Next steps' sections
   - User preferences already in global memory
   - Session metadata (dates, message counts)
5. PRESERVE decisions, rationale, architecture, preferences, and problem/solution pairs

Respond with a single markdown document. Use ## headers to separate topics.
Each topic should be self-contained and useful to a future session that knows
nothing about the current conversation.

If the session logs contain nothing worth persisting, respond with NO_REPLY.
```

## Dream Gate System (when to fire)
Gates are checked cheapest first:
```
Gate 1: config.dream.enabled = true
Gate 2: hours since last consolidation >= min_hours (default: 24h)
Gate 3: session count since last consolidation >= min_sessions (default: 5)
```
If all gates pass → DreamGate::Open → dream fires.
Uses `.dream-lock` file to prevent concurrent dream runs.

## Dream Lifecycle
```
1. check_dream_gates()          → all pass → Open{sessions: [...]}
2. acquire lock (.dream-lock)   → prevents concurrent dreams
3. build_dream_user_message()   → concatenate session logs (max 32K chars)
4. call model (dream prompt)    → synthesize into MEMORY.md
5. process_dream_response()     → validate: must have ## headers, not NO_REPLY
6. write_long_term(MEMORY.md)   → overwrite workspace memory
7. clean_processed_sessions()   → delete session files (with 5-min recency guard)
8. release lock                 → record consolidation timestamp
```

## File Watcher Integration
The `MemoryFileWatcher` monitors `~/.grok/memory/` for `.md` changes:
- Lock-free design: `ArcSwap<HashSet<PathBuf>>` for dirty tracking
- Events: Create, Modify, Remove (non-`.md` files ignored)
- On dirty: trigger incremental re-index of changed files
- On delete: purge chunks from search index

## Dream Input Limits
- Max input: 32,000 chars (splits across sessions if exceeded)
- Max output: 16,000 chars (truncated if exceeded)
- Session files beyond cap: preserved for next dream pass

## Self-Improvement Pattern for IDE Agents
```
Session N ends:
    → write_session_log(discoveries, decisions, errors encountered)

Between sessions (N+5 or 24h later):
    → Dream fires
    → Reads session logs N through N+5
    → Merges into MEMORY.md:
        - "auth module uses JWT RS256 with 1h expiry"
        - "never use X library (causes memory leaks)"
        - "test command: pytest -x --timeout=30"
    → Deletes consumed session logs

Session N+6 starts:
    → memory_search("JWT") → instant answer from merged knowledge
    → No file reading needed → near-zero tokens
```

## What to Write to Session Logs
At session end, write a session log with:
```markdown
## Decisions
- [What was decided and why]

## Discoveries
- [What was learned about the codebase/domain]

## Problems Solved
- [Issue → root cause → solution]

## Conventions Confirmed
- [Coding patterns, naming, test requirements]

## Dead Ends
- [What didn't work and why — saves future sessions from repeating]
```

## Dreaming vs. Normal Memory Writes
| | Normal Write | Dream |
|--|--|--|
| Trigger | Immediately (model calls memory_write) | Background (time/session gate) |
| Input | Current conversation | Multiple past session logs |
| Output | Appended to MEMORY.md | Replaces MEMORY.md (merge) |
| Frequency | Every session | Every 5+ sessions / 24h+ |
| Purpose | Capture current fact | Consolidate + resolve contradictions |
