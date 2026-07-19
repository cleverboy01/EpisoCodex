#!/usr/bin/env python3
"""
Skill Indexer — SessionStart passive hook / CLI (Phase 1: Dynamic Skill Retrieval)
Scans agents/skills/*/SKILL.md, extracts frontmatter metadata, and writes
agents/logs/skill-index.json — the lightweight metadata map used by the
Skill Router for semantic retrieval (keeps agent context clean).

Usage:
    python agents/hooks/bin/skill_indexer.py          # rebuild the index
    (also runs as a SessionStart hook; reads stdin JSON and rebuilds silently)
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SKILLS_DIR = os.path.join(ROOT, "agents", "skills")
INDEX_FILE = os.path.join(ROOT, "agents", "logs", "skill-index.json")


def parse_frontmatter(text: str) -> dict:
    """Parse simple `key: value` YAML frontmatter between --- fences."""
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    meta = {}
    if match:
        for line in match.group(1).splitlines():
            if ":" in line and not line.startswith((" ", "\t", "-")):
                key, _, value = line.partition(":")
                meta[key.strip()] = value.strip()
    return meta


def build_index() -> dict:
    entries = []
    if os.path.isdir(SKILLS_DIR):
        for name in sorted(os.listdir(SKILLS_DIR)):
            path = os.path.join(SKILLS_DIR, name, "SKILL.md")
            if not os.path.isfile(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
            except OSError:
                continue
            meta = parse_frontmatter(text)
            entries.append({
                "name": meta.get("name", name),
                "path": os.path.relpath(path, ROOT).replace(os.sep, "/"),
                "description": meta.get("description", ""),
                "when_to_use": meta.get("when_to_use", ""),
                "short_description": meta.get("short_description", ""),
                "enabled": meta.get("enabled", "true").lower() != "false",
            })

    index = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "skill_count": len(entries),
        "skills": entries,
    }
    os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    return index


def main():
    # Determine mode from explicit flag — avoids stdin-blocking on all platforms
    hook_mode = "--hook" in sys.argv
    if hook_mode:
        try:
            json.load(sys.stdin)  # consume hook payload; content not needed
        except (json.JSONDecodeError, OSError):
            pass
        build_index()
        sys.exit(0)

    index = build_index()
    print(f"Indexed {index['skill_count']} skills -> {os.path.relpath(INDEX_FILE, ROOT)}")


if __name__ == "__main__":
    main()
