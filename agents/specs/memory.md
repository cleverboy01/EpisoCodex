# Memory & RAG Spec
# Source: xai-grok-memory/src/ (xai-org/grok-build)

## Architecture
Cross-session knowledge persistence via markdown + sqlite-vec (vector DB).
Enabled via `--experimental-memory` or `GROK_MEMORY=1`.

## Data Layout on Disk
```
~/.grok/memory/
  ├── MEMORY.md                              # Global curated knowledge
  └── {workspace_hash}/                      # Per-workspace (blake3(cwd)[..16])
      ├── MEMORY.md                          # Project-level curated knowledge
      └── sessions/
          └── YYYY-MM-DD-{slug}-{sid8}.md   # Session logs
```

## Pipeline: Text → Searchable Memory
```
1. Chunker       → split markdown/code into logical segments
2. Embedding     → convert chunks to float vectors (batch size: 32)
3. Index (SQLite-vec) → store vectors + metadata
4. Watcher       → file system monitor, triggers re-index on change
5. Dream         → background consolidation during idle time
6. Search        → ANN (approximate nearest neighbor) lookup
7. MMR           → diversify results (Maximal Marginal Relevance)
8. Query Expand  → expand short queries before search
```

## Chunker Strategy
- Split on markdown headings (`#`, `##`, `###`)
- Respect code block boundaries (never split mid-block)
- Target chunk size: fits in one embedding call
- Overlap: small overlap between adjacent chunks for context continuity

## Embedding
- Provider: xAI embedding API (same credentials as main model)
- Batch size: 32 chunks per API call
- Output: float vector stored in sqlite-vec
- Missing embeddings embedded on: reindex / flush / session-end

## Dreaming (Background Consolidation)
Runs during agent idle time (between user turns):
- Scans for unembedded chunks → batch embed them
- Merges redundant memory entries
- Rebuilds degraded indexes
- Optimizes vector storage
- No user-visible activity; transparent performance improvement

## MMR (Maximal Marginal Relevance) Algorithm
Prevents returning redundant results:
```
selected = []
candidates = initial_ann_results(query, top_k=50)

while len(selected) < desired_k:
    best = argmax over candidates:
        λ * similarity(candidate, query)
        - (1-λ) * max(similarity(candidate, s) for s in selected)
    selected.append(best)
    candidates.remove(best)
```
Default λ: 0.5 (balance relevance vs diversity)

## Query Expansion
Before ANN search, expand short user queries:
- Add synonyms and related terms
- Expand acronyms
- Add context from recent conversation
- Goal: improve recall for short/ambiguous queries

## Search API Pattern
```
query: str
    → query_expansion(query) → expanded_query
    → embed(expanded_query) → query_vector
    → ann_search(query_vector, top_k=50) → candidates
    → mmr(candidates, query_vector, k=10) → diverse_results
    → format_results() → context for model
```

## Memory Scope
- `MemoryScope::Global` → `~/.grok/memory/MEMORY.md`
- `MemoryScope::Workspace` → `~/.grok/memory/{hash}/MEMORY.md`
- `MemoryScope::Session` → `~/.grok/memory/{hash}/sessions/{slug}.md`

## Best Practices for IDE
1. Write important decisions/discoveries to workspace MEMORY.md at session end.
2. Search memory BEFORE reading large files — answer may already be cached.
3. Keep memory entries short and factual (saves embedding cost).
4. Use session logs for ephemeral context, MEMORY.md for permanent knowledge.
