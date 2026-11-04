#!/usr/bin/env python3
"""Offline audit of a public MSM resource Git tree. No network or authentication."""
import collections
import datetime
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
src = ROOT / "resources-tree.json"
out_json = ROOT / "asset-audit.json"
out_md = ROOT / "asset-audit.md"
data = json.loads(src.read_text(encoding="utf-8"))
entries = [n for n in data.get("tree", []) if n.get("type") == "blob" and isinstance(n.get("path"), str)]
paths = [n["path"] for n in entries]
kinds = {
    "explicit_test": r"(^|[/_.-])test([/_.-]|$)",
    "explicit_placeholder": r"(^|[/_.-])placeholder([/_.-]|$)",
    "developer_admin": r"(^|[/_.-])admin([/_.-]|$)",
    "explicit_unused_or_beta": r"(^|[/_.-])(unused|beta|prototype|deprecated|scrapped)([/_.-]|$)",
    "dish_harmonizer_related": r"dish_harmonizer",
    "monster_audio": r"^split_asset_pack/audio/music/.*\.(ogg|mid)$",
    "music_world_midi": r"^split_asset_pack/audio/music/world[0-9]+\.mid$",
}
flagged = {}
for category, pattern in kinds.items():
    regex = re.compile(pattern, re.I)
    flagged[category] = [p for p in paths if regex.search(p)]
suffixes = collections.Counter(Path(p).suffix.lower() or "(no extension)" for p in paths)
result = {
    "source": "https://github.com/Next-Private-Server/Resources",
    "source_git_tree": "https://api.github.com/repos/Next-Private-Server/Resources/git/trees/main?recursive=1",
    "inspected_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "tree_sha": data.get("sha"),
    "tree_truncated": data.get("truncated"),
    "file_count": len(entries),
    "extension_counts": dict(suffixes.most_common()),
    "flagged_files": flagged,
    "note": "Filename candidates only. Presence does not establish unused gameplay or scrapped development. Confirm via historical versions or code references.",
}
out_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
lines = ["# My Singing Monsters public asset filename audit", "",
         f"Source: {result['source']}", f"Tree SHA: {result['tree_sha']}",
         f"Entries: {len(entries):,}; truncated: {data.get('truncated')}", "",
         "This is an asset filename survey, **not** proof of cancelled gameplay.", "",
         "## Category matches"]
for category, matches in flagged.items():
    lines += [f"### {category} — {len(matches)} matches", ""]
    lines += [f"- `{p}`" for p in matches[:35]]
    if len(matches)>35: lines += [f"- …and {len(matches)-35} more in asset-audit.json"]
    lines += [""]
out_md.write_text("\n".join(lines)+"\n", encoding="utf-8")
print(f"Scanned {len(entries):,} public asset files; wrote {out_json.name}, {out_md.name}.")
for cat, v in flagged.items():
    print(f"{cat}: {len(v)}")
    for path in v[:8]: print("  "+path)
