# Token Optimization Spec
# Source: xai-token-estimation/, xai-grok-memory/, xai-grok-workspace/ (xai-org/grok-build)

## Core Principle
Every token costs money and latency. Optimize relentlessly.

## Context Window Budget
```
Total window: model-dependent (e.g. 128K, 200K tokens)
Allocation:
  System prompt:       ~5-10%   (skills, rules, agent definition)
  Conversation history: ~40-60%  (turns, tool results)
  Working context:     ~20-30%  (current files, search results)
  Reserve for output:  ~10-20%  (model response)

Danger zone: > auto_compact_threshold_percent (default ~85%)
  → triggers context compaction automatically
```

## Token Estimation
The `xai-token-estimation` crate provides fast local token counting:
- No API call needed — uses local tokenizer
- Used to pre-check if content fits before sending
- Used for compaction threshold decisions

## File Reading Strategy (Minimize Tokens)
```
# Priority order — use the FIRST that gives enough context:
1. Memory search → cheapest (vectors already indexed)
2. Symbol lookup via LSP → exact, no full-file read
3. grep/search → find relevant section, read only that
4. Read specific line range → don't read entire file
5. Read full file → last resort, only for small files

# Never:
- Read a file you've already read in this session (use cached version)
- Read a whole directory tree upfront
- Include build artifacts, node_modules, .git in any search
```

## Chunking for Large Files
When a file is too large to fit in context:
```
1. Identify relevant sections via search/LSP
2. Extract only relevant chunks (functions, classes, sections)
3. Summarize non-relevant parts: "// [rest of file: 200 lines, handles auth]"
4. Include full content only for the target section
```

## Tool Result Compression
Before returning large tool results to the model:
- Truncate file listings to most relevant entries
- Summarize command output: first 50 lines + last 20 lines if > 200 lines
- For test output: show ONLY failures, skip passing tests
- For build output: show ONLY errors and warnings, skip successful steps

## Context Compaction
When context reaches threshold:
```
PreCompact hook fires
    → optional: inject summary via hook script
Model summarizes history:
    → keeps: key decisions, current task state, important facts
    → drops: verbose tool outputs, superseded file versions
PostCompact hook fires
    → new history = summary + recent turns only
```

## Hunk Tracking (Efficient Change Awareness)
The `xai-hunk-tracker` tracks file changes line-by-line:
- Agent does NOT re-read unchanged files
- Only changed hunks are re-processed
- Saves tokens on large codebase edits

## System Prompt Optimization
- Skills: only include body of enabled, matching skills
- Rules: keep rules concise (each rule < 2 sentences)
- Agent definition: reference, don't inline large docs
- Disable unused skills via `enabled: false`

## Codebase Graph (Avoid Full Tree Reads)
The `xai-codebase-graph` indexes the entire repo structure:
- Query: "where is the auth logic?" → returns: `src/auth/mod.rs`, `src/middleware/auth.rs`
- No need to `ls -R` or read every file
- Saves 90%+ of tokens on "find where X is" tasks

## Practical Rules
1. Search before reading — use grep/ripgrep to locate relevant code
2. Summarize before including — compress tool outputs
3. Cache aggressively — don't re-read files already in context
4. Chunk large inputs — never send a 2000-line file as one tool result
5. Use memory — persist discoveries to avoid re-discovering each session
6. Batch tool calls — do multiple reads in parallel when possible
