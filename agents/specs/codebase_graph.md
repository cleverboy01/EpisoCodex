# Codebase Graph Spec
# Source: xai-codebase-graph/src/ (xai-org/grok-build)

## What is the Codebase Graph?
A fast, in-memory symbol index of the entire repository.
Built using tree-sitter for language-aware parsing.
Enables go-to-definition and go-to-references without reading full files.

## Core Capabilities
- **Go-to-definition**: Find where a symbol is defined
- **Go-to-references**: Find all usages of a symbol
- **Initial indexing**: Build full index from scratch (parallel, rayon)
- **Incremental reindex**: Update on file system events (no full rebuild)
- **Memory-mapped I/O**: Zero-copy file reading, fast index caching
- **Cache persistence**: Save/load index as binary (`.grok-index.bin`)

## Architecture
```
FileSystem Events (FSNotify)
        │
        ▼
IndexManager (actor, background)
        │
        ├─► Parser (tree-sitter, per language)
        │       └─► ScopeGraph (symbol definitions + references)
        │
        ├─► StringInterner (memory-efficient symbol storage)
        │
        ├─► IndexManagerHandle (query channel)
        │       ├─► goto_definition(file, row, col)
        │       ├─► goto_references(file, row, col)
        │       ├─► has_definition(symbol_name)
        │       └─► get_file_count()
        │
        └─► Cache (binary serialized, mmap on load)
```

## Supported Languages
Identified by file extension via `LanguageRegistry`:
- Rust, Python, JavaScript, TypeScript, Go, Java, C/C++, Ruby, etc.
- Files above `MAX_INDEXABLE_FILE_SIZE` are skipped
- Binary files are automatically detected and skipped

## Query API (IDE Usage Pattern)
```python
# Instead of: read_file("src/main.rs") → parse manually → find definition
# Use: goto_definition(file, line, col) → instant answer

# Go to definition:
result = handle.goto_definition_blocking("src/main.rs", row=10, col=15)
for loc in result.locations:
    print(f"{loc.path}:{loc.line}")

# Has definition:
exists = handle.has_definition_blocking("MyStruct")

# File stats:
count = handle.get_file_count()
```

## Token Savings
```
Traditional approach:
  read_file(src/auth/mod.rs)          → 500 tokens
  read_file(src/auth/handler.rs)      → 800 tokens
  grep("authenticate", recursive)     → 200 tokens
  Total: ~1500 tokens to find one function

With codebase graph:
  goto_definition("authenticate", file, line, col) → 50 tokens
  read_file(result.path, lines=[result.line-5:result.line+20]) → 150 tokens
  Total: ~200 tokens = 87% reduction
```

## ScopeGraph Nodes
```
Symbol     → a named definition (function, class, variable)
Reference  → a usage of a symbol
LocalDef   → definition within a scope
LocalImport → import/use statement
LocalScope → a nested scope (function body, block, etc.)
```

## Cache Strategy
```
~/.grok/codebase-index/{workspace_hash}/
  └── .grok-index.bin    # mmap'd binary cache

Loading: try cache first → if stale or missing → rebuild
Invalidation: any file event triggers incremental update
Lock: WorkspaceLockGuard prevents concurrent rebuilds
```

## IDE Integration Pattern
Use codebase graph for:
1. Finding where a function/class/variable is defined → zero file reads needed
2. Finding all callers of a function before refactoring
3. Checking if a symbol exists before writing code that uses it
4. Understanding import graph without reading node_modules
