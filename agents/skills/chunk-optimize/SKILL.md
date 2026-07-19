---
name: chunk-optimize
description: Inspect and modify large Python files chunk-by-chunk (classes or functions) to minimize token consumption.
when_to_use: Use when you need to read or edit a large Python file (>150 lines) without loading the entire file into context.
short_description: Split and edit large files on class/function level
argument_hint: [list | view | replace] [file_path] [chunk_name] [new_content_file]
allowed_tools: [run_terminal_cmd]
enabled: true
---

# Chunk Optimize Skill

Tolls for splitting large files into logical AST chunks (functions/classes) to read or optimize them piece-by-piece, and stitching them back together.

## How to Use

### 1. Outline the File (Map)
Get all functions/classes and their line ranges:
```bash
python agents/hooks/bin/chunk_optimizer.py list <file_path>
```

### 2. View a Specific Chunk (Targeted Read)
Read only the target function/class:
```bash
python agents/hooks/bin/chunk_optimizer.py view <file_path> <chunk_name>
```

### 3. Replace the Chunk (Stitch)
Write your modified chunk code to a temporary file (e.g. `temp_edit.py`), then apply:
```bash
python agents/hooks/bin/chunk_optimizer.py replace <file_path> <chunk_name> temp_edit.py
```
*Note: This automatically handles compilation checks, backups, and merging.*
