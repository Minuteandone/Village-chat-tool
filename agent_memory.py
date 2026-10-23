"""Opt-in, readable, Git-versioned memory for the public agent workspace.

Important: this is NOT a private memory store. Removing a memory entry does not
erase old Git commits, forks, caches or issue comments.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import pathlib
import re

SCHEMA_VERSION = 1
MAX_ENTRIES = 200
MAX_NOTE_BYTES = 1200
MAX_STORE_BYTES = 120_000
CATEGORIES = ("project", "preference", "decision", "lesson", "fact")
WORD_PATTERN = re.compile(r"[\w-]+", re.UNICODE)


def _path(workspace: pathlib.Path) -> pathlib.Path:
    root = workspace.resolve()
    candidate = workspace / ".agent" / "memory.json"
    if candidate.is_symlink() or candidate.parent.is_symlink():
        raise ValueError("Memory file/directory cannot be a symlink.")
    if not candidate.resolve().is_relative_to(root):
        raise ValueError("Memory path escapes workspace.")
    return candidate


def _read(workspace: pathlib.Path) -> dict:
    path = _path(workspace)
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "next_id": 1, "items": []}
    if not path.is_file() or path.stat().st_size > MAX_STORE_BYTES:
        raise ValueError("Memory store is unavailable or exceeds its safe size limit.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Memory JSON is invalid; the file was not overwritten.") from exc
    if (not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION
            or type(data.get("next_id")) is not int or data["next_id"] < 1
            or not isinstance(data.get("items"), list)
            or len(data["items"]) > MAX_ENTRIES):
        raise ValueError("Unrecognized memory schema; the file was not overwritten.")
    ids = []
    for m in data["items"]:
        if (not isinstance(m, dict) or type(m.get("id")) is not int
                or m["id"] < 1 or m.get("category") not in CATEGORIES
                or not isinstance(m.get("text"), str)
                or not 1 <= len(m["text"].encode("utf-8")) <= MAX_NOTE_BYTES
                or not isinstance(m.get("created_at"), str)
                or not isinstance(m.get("updated_at"), str)):
            raise ValueError("Malformed memory record; the file was not overwritten.")
        ids.append(m["id"])
    if len(set(ids)) != len(ids) or (ids and max(ids) >= data["next_id"]):
        raise ValueError("Invalid memory IDs; the file was not overwritten.")
    return data


def _save(workspace: pathlib.Path, data: dict) -> None:
    path = _path(workspace)
    encoded = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(encoded) > MAX_STORE_BYTES:
        raise ValueError("Memory store would exceed 120 KB.")
    path.parent.mkdir(parents=True, exist_ok=True)
    # Avoid half-written files if serialization or write fails.
    temp = path.with_name("memory.json.tmp")
    if temp.is_symlink():
        raise ValueError("Unsafe temporary memory file.")
    try:
        temp.write_bytes(encoded)
        temp.replace(path)
    finally:
        if temp.exists() and not temp.is_symlink():
            temp.unlink()


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _find(data: dict, text_id: str) -> dict:
    if not text_id.isdecimal():
        raise ValueError("Memory ID must be a positive number.")
    record = next((m for m in data["items"] if m["id"] == int(text_id)), None)
    if record is None:
        raise ValueError("Memory ID does not exist.")
    return record


def _summary(m: dict, *, full=False) -> str:
    text = m["text"] if full else m["text"].replace("\n", " ")
    if not full and len(text) > 200:
        text = text[:197] + "..."
    return f"#{m['id']} [{m['category']}] {text}"


def _search(data: dict, query: str, limit=12) -> list[dict]:
    query = query.strip()
    if not query:
        return sorted(data["items"], key=lambda m: m["id"], reverse=True)[:limit]
    words = {w.casefold() for w in WORD_PATTERN.findall(query)}
    ranked = []
    for memory in data["items"]:
        text = memory["text"].casefold()
        category = memory["category"].casefold()
        tokens = set(WORD_PATTERN.findall(text + " " + category))
        matched = len(words.intersection(tokens))
        phrase = query.casefold() in text or query.casefold() in category
        score = matched + (3 if phrase else 0)
        if score:
            ranked.append((score, memory["id"], memory))
    ranked.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [m for _, _, m in ranked[:limit]]


def handle(workspace: pathlib.Path, value: str, body: str, *, has_newline: bool) -> str:
    """Implement /work memory SUBCOMMAND from an owner-authored issue comment."""
    cmd, _, arg = value.partition(" ")
    command = cmd.casefold().strip()
    arg = arg.strip()
    data = _read(workspace)
    if command in ("help", ""):
        return ("### Agent memory 🧠\n\n"
                "/work memory remember CATEGORY + newline + memory\n"
                "/work memory list [CATEGORY]\n"
                "/work memory search KEYWORD\n"
                "/work memory show ID\n"
                "/work memory edit ID + newline + replacement memory\n"
                "/work memory forget ID\n"
                "/work memory stats\n\n"
                "Categories: " + ", ".join(CATEGORIES) + ". "
                "Public, manual opt-in notes only. No passwords, secrets or personal details. "
                "Forgetting removes the active record but cannot erase Git history.")
    if command in ("remember", "edit"):
        if not has_newline:
            raise ValueError("Provide a newline after the command, then the memory text.")
        note = body.strip()
        if not 1 <= len(note.encode("utf-8")) <= MAX_NOTE_BYTES:
            raise ValueError("Memory text must be 1–1200 UTF-8 bytes.")
        if command == "remember":
            category = arg.casefold()
            if category not in CATEGORIES:
                raise ValueError("Category must be: " + ", ".join(CATEGORIES))
            if len(data["items"]) >= MAX_ENTRIES:
                raise ValueError("Memory full (200 records).")
            entry = {"id": data["next_id"], "category": category, "text": note,
                     "created_at": _timestamp(), "updated_at": _timestamp()}
            data["items"].append(entry)
            data["next_id"] += 1
            response = f"Remembered {_summary(entry)}."
        else:
            entry = _find(data, arg)
            entry["text"] = note
            entry["updated_at"] = _timestamp()
            response = f"Updated {_summary(entry)}."
        _save(workspace, data)
        return response + " Saved to workspace/.agent/memory.json."
    if command == "forget":
        entry = _find(data, arg)
        data["items"] = [m for m in data["items"] if m["id"] != entry["id"]]
        _save(workspace, data)
        return (f"Forgot active record #{entry['id']}. "
                "Warning: prior Git commits and public issue messages may retain the old text.")
    if command == "show":
        entry = _find(data, arg)
        return ("### Memory record 🧠\n\n" + _summary(entry, full=True)
                + f"\n\nCreated: {entry['created_at']}\nUpdated: {entry['updated_at']}")
    if command == "list":
        if arg and arg.casefold() not in CATEGORIES:
            raise ValueError("Unknown category. Choose: " + ", ".join(CATEGORIES))
        matches = [m for m in data["items"] if not arg or m["category"] == arg.casefold()]
        matches.sort(key=lambda m: m["id"], reverse=True)
        return (f"### Saved memories ({len(matches)} matching, {len(data['items'])} total) 🧠\n\n"
                + "\n".join(_summary(m) for m in matches[:30])
                + ("\n…showing newest 30." if len(matches) > 30 else "")
                if matches else "### Saved memories 🧠\n\nNo memories saved.")
    if command == "search":
        if not 1 <= len(arg) <= 120:
            raise ValueError("Search query must be 1–120 characters.")
        found = _search(data, arg, 12)
        return (f"### Memories matching {arg!r} 🔎\n\n"
                + "\n".join(_summary(m) for m in found)
                if found else "No matching memories.")
    if command == "stats":
        counts = {cat: sum(m["category"] == cat for m in data["items"])
                  for cat in CATEGORIES}
        return ("### Memory statistics 🧠\n\n" +
                f"Active records: {len(data['items'])}/{MAX_ENTRIES}\n" +
                "\n".join(f"{cat}: {n}" for cat, n in counts.items()) +
                f"\nNext ID: {data['next_id']}")
    raise ValueError("Unknown memory command. Try /work memory help.")


def context(workspace: pathlib.Path, tasks: list, query: str = "") -> str:
    """Build an explicit rehydration snapshot without writing anything."""
    data = _read(workspace)
    active = [t for t in tasks if not t.get("done")]
    found = _search(data, query, 12)
    lines = ["### Agent session context 🧭", "",
             f"Open tasks: {len(active)}; saved memories: {len(data['items'])}.", ""]
    lines.extend(["**Open tasks**",
                  *(f"- #{t['id']}: {str(t['text'])[:240]}" for t in active[-20:]),
                  "(none)" if not active else "", "", "**Relevant memories**"])
    lines.extend("- " + _summary(m) for m in found)
    if not found:
        lines.append("(no matching memories)")
    lines.append("")
    lines.append("Memories are user-managed notes, not independently verified facts.")
    return "\n".join(x for x in lines if x != "")
