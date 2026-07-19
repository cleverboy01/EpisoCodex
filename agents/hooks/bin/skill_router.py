#!/usr/bin/env python3
"""
Skill Router — dynamic skill retrieval (Phase 1: Semantic Routing)
Given a task description, ranks skills from agents/logs/skill-index.json and
returns ONLY the top-k relevant SKILL.md paths. Agents inject just those
instructions into context instead of loading every skill (context stays clean).

Usage:
    python agents/hooks/bin/skill_router.py "check a genetic variant" --top-k 3

Output (JSON):
    {"task": "...", "selected": [{"name": ..., "path": ..., "score": ...}]}
"""
import argparse
import json
import math
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
INDEX_FILE = os.path.join(ROOT, "agents", "logs", "skill-index.json")

STOPWORDS = {
    "a", "an", "the", "to", "of", "for", "and", "or", "in", "on", "with",
    "is", "are", "be", "this", "that", "it", "use", "when", "there", "my",
}


def tokenize(text: str) -> list:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS and len(t) > 1]


def load_index() -> dict:
    if not os.path.isfile(INDEX_FILE):
        # Build on demand if missing
        sys.path.insert(0, os.path.dirname(__file__))
        import skill_indexer  # noqa: local import by design
        return skill_indexer.build_index()
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def score_skill(task_tokens: set, skill: dict) -> float:
    """Bag-of-words overlap score, normalized by document length.
    Deliberately dependency-free; swap for embeddings (Vector DB) if available."""
    doc = " ".join([
        skill.get("name", ""),
        skill.get("description", ""),
        skill.get("when_to_use", ""),
        skill.get("short_description", ""),
    ])
    doc_tokens = tokenize(doc)
    if not doc_tokens:
        return 0.0
    overlap = sum(1 for t in doc_tokens if t in task_tokens)
    # Name matches are strong routing signals
    name_bonus = 2.0 * sum(1 for t in tokenize(skill.get("name", "")) if t in task_tokens)
    return (overlap + name_bonus) / math.sqrt(len(doc_tokens))


def route(task: str, top_k: int = 3, min_score: float = 0.05) -> dict:
    index = load_index()
    task_tokens = set(tokenize(task))
    ranked = []
    for skill in index.get("skills", []):
        if not skill.get("enabled", True):
            continue
        s = score_skill(task_tokens, skill)
        if s >= min_score:
            ranked.append({"name": skill["name"], "path": skill["path"], "score": round(s, 4)})
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return {"task": task, "selected": ranked[:top_k]}


def main():
    parser = argparse.ArgumentParser(description="Route a task to relevant skills")
    parser.add_argument("task", help="natural-language task description")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--min-score", type=float, default=0.05)
    args = parser.parse_args()
    print(json.dumps(route(args.task, args.top_k, args.min_score), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
