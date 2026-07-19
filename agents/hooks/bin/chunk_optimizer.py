#!/usr/bin/env python3
"""
Chunk Optimizer — AST-based File Splitter & Stitcher
====================================================
Phase: Advanced Token Optimization (AGI Cognitive Layer)

This tool allows the agent to inspect and modify large Python files on a
chunk-by-chunk basis (functions and classes) instead of loading the entire file.
It parses the file's AST, extracts ranges, and updates specific nodes
while preserving the rest of the file structure.

Usage:
    # List all functions/classes and their line ranges:
    python agents/hooks/bin/chunk_optimizer.py list path/to/file.py

    # View a single function/class content:
    python agents/hooks/bin/chunk_optimizer.py view path/to/file.py function_or_class_name

    # Replace a single function/class in-place:
    python agents/hooks/bin/chunk_optimizer.py replace path/to/file.py function_or_class_name new_content.py
"""
import sys
import os
import ast
import json
import argparse
from pathlib import Path

def get_utf8_terminal():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

class ChunkVisitor(ast.NodeVisitor):
    def __init__(self, source_lines):
        self.source_lines = source_lines
        self.chunks = []

    def visit_FunctionDef(self, node):
        self._add_node(node, "function")
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._add_node(node, "async_function")
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self._add_node(node, "class")
        self.generic_visit(node)

    def _add_node(self, node, node_type):
        # Determine end line
        end_line = getattr(node, "end_lineno", node.lineno)
        # Find docstring
        docstring = ast.get_docstring(node)
        summary = docstring.split("\n")[0] if docstring else ""

        self.chunks.append({
            "name": node.name,
            "type": node_type,
            "start_line": node.lineno,
            "end_line": end_line,
            "summary": summary
        })

def parse_chunks(file_path: Path) -> tuple[list[dict], list[str]]:
    source = file_path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)
    tree = ast.parse(source)
    visitor = ChunkVisitor(lines)
    visitor.visit(tree)
    # Sort chunks by starting line
    visitor.chunks.sort(key=lambda x: x["start_line"])
    return visitor.chunks, lines

def list_chunks(file_path: Path) -> None:
    try:
        chunks, lines = parse_chunks(file_path)
    except Exception as e:
        print(json.dumps({"error": f"Failed to parse file: {str(e)}"}))
        sys.exit(1)

    output = []
    for c in chunks:
        # Calculate approximate token size (roughly characters / 4)
        chunk_lines = lines[c["start_line"]-1 : c["end_line"]]
        char_count = sum(len(l) for l in chunk_lines)
        approx_tokens = int(char_count / 4)

        output.append({
            "name": c["name"],
            "type": c["type"],
            "range": f"L{c['start_line']}-L{c['end_line']}",
            "tokens": approx_tokens,
            "summary": c["summary"]
        })
    print(json.dumps({"file": str(file_path.name), "chunks": output}, indent=2, ensure_ascii=False))

def view_chunk(file_path: Path, target_name: str) -> None:
    try:
        chunks, lines = parse_chunks(file_path)
    except Exception as e:
        print(f"Error: Failed to parse file: {e}", file=sys.stderr)
        sys.exit(1)

    for c in chunks:
        if c["name"] == target_name:
            chunk_content = "".join(lines[c["start_line"]-1 : c["end_line"]])
            print(chunk_content, end="")
            return

    print(f"Error: Chunk '{target_name}' not found in {file_path.name}", file=sys.stderr)
    sys.exit(1)

def replace_chunk(file_path: Path, target_name: str, new_content_file: Path) -> None:
    if not new_content_file.exists():
        print(f"Error: New content file '{new_content_file}' not found", file=sys.stderr)
        sys.exit(1)

    try:
        chunks, lines = parse_chunks(file_path)
    except Exception as e:
        print(f"Error: Failed to parse target file: {e}", file=sys.stderr)
        sys.exit(1)

    target_chunk = None
    for c in chunks:
        if c["name"] == target_name:
            target_chunk = c
            break

    if not target_chunk:
        print(f"Error: Chunk '{target_name}' not found in {file_path.name}", file=sys.stderr)
        sys.exit(1)

    new_content = new_content_file.read_text(encoding="utf-8")
    
    # Verify the new content compiles (syntax gate)
    try:
        ast.parse(new_content)
    except SyntaxError as e:
        print(f"Error: New content has syntax error: {e}", file=sys.stderr)
        sys.exit(1)

    # Stitch the file back together
    # lines indices are 0-based; start_line and end_line are 1-based
    before = lines[:target_chunk["start_line"]-1]
    after = lines[target_chunk["end_line"]:]
    
    # Ensure new content ends with a newline if it doesn't
    if not new_content.endswith("\n"):
        new_content += "\n"

    # Backup the original file
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    file_path.write_text("".join(lines), encoding="utf-8") # Backup state
    
    # Write the stitched file
    file_path.write_text("".join(before) + new_content + "".join(after), encoding="utf-8")
    print(json.dumps({
        "status": "success",
        "file": file_path.name,
        "updated_chunk": target_name,
        "lines_before": len(before),
        "lines_after": len(after)
    }))

def main():
    get_utf8_terminal()
    parser = argparse.ArgumentParser(description="AST-based Chunk Optimizer for large files")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ── list ──
    p_lst = sub.add_parser("list", help="list logical chunks in a file")
    p_lst.add_argument("file", help="path to Python script")

    # ── view ──
    p_vw = sub.add_parser("view", help="view single chunk code")
    p_vw.add_argument("file", help="path to Python script")
    p_vw.add_argument("name", help="name of the class or function")

    # ── replace ──
    p_rep = sub.add_parser("replace", help="replace single chunk in-place")
    p_rep.add_argument("file", help="path to Python script")
    p_rep.add_argument("name", help="name of the class or function")
    p_rep.add_argument("new_content_file", help="file containing the new code block")

    args = parser.parse_args()
    file_path = Path(args.file).resolve()

    if not file_path.exists():
        print(f"Error: File '{file_path}' not found", file=sys.stderr)
        sys.exit(1)

    if args.cmd == "list":
        list_chunks(file_path)
    elif args.cmd == "view":
        view_chunk(file_path, args.name)
    elif args.cmd == "replace":
        replace_chunk(file_path, args.name, Path(args.new_content_file).resolve())

if __name__ == "__main__":
    main()
