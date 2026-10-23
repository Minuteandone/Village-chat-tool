#!/usr/bin/env python3
"""Tiny dashboard for this persistent GitHub Actions agent workspace."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
taskfile = root / ".agent" / "tasks.json"
tasks = json.loads(taskfile.read_text()) if taskfile.exists() else []
files = [p for p in root.rglob("*") if p.is_file() and not p.is_symlink()]
print("Agent Workspace Dashboard")
print("=" * 25)
print(f"Workspace files: {len(files)}")
print(f"Total tasks: {len(tasks)}")
print(f"Open tasks: {sum(not t['done'] for t in tasks)}")
for task in tasks:
    if not task["done"]:
        print(f"- #{task['id']}: {task['text']}")
