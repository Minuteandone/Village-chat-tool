#!/usr/bin/env python3
"""Read-only overview of the persistent GitHub Actions agent workspace."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
agent_dir = root / ".agent"


def read_json(filename, fallback):
    target = agent_dir / filename
    if not target.is_file():
        return fallback
    return json.loads(target.read_text(encoding="utf-8"))


tasks = read_json("tasks.json", [])
memory = read_json("memory.json", {"items": []})
memories = memory.get("items", [])
files = [p for p in root.rglob("*") if p.is_file() and not p.is_symlink()]
open_tasks = [t for t in tasks if not t.get("done")]

print("Agent Workspace Dashboard")
print("=" * 28)
print(f"Workspace files: {len(files)}")
print(f"Tasks: {len(tasks)} total, {len(open_tasks)} open")
print(f"Memories: {len(memories)} saved")
print()

if open_tasks:
    print("Open tasks:")
    for task in open_tasks[-10:]:
        print(f"  - #{task['id']}: {task['text'][:200]}")
else:
    print("No open tasks.")

if memories:
    print("\nRecent memories:")
    for item in memories[-5:]:
        summary = item["text"].replace("\n", " ")
        print(f"  - #{item['id']} [{item['category']}]: {summary[:120]}")
else:
    print("\nNo saved memories.")

print("\nUse /work context [query] to recall relevant tasks and memories.")
