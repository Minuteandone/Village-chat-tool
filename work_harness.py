#!/usr/bin/env python3
"""Bounded owner-only tool harness for a GitHub Actions workspace.

Commands arrive as issue comments. This process receives NO GITHUB_TOKEN.
Scripts run in a Docker container with no network access and no secrets.
"""
import os
import json
import pathlib
import re
import subprocess
import shlex
import zipfile
import agent_memory
import research_tools
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
WORKSPACE = ROOT / "workspace"
MAX_FILE = 160_000
MAX_COMMENT = 28_000
ALLOWED_HOSTS = {"raw.githubusercontent.com", "theaidigest.org",
                 "gitlab.com", "api.github.com"}

def github_safe(text):
    """Keep Village-style @names from pinging unrelated GitHub users in replies."""
    return re.sub(r"@(?![\u200b\u200c\u200d])", "@\u200b", str(text))

def resolve(path="", *, expect_file=False):
    path = path.strip() or "."
    p = pathlib.PurePosixPath(path)
    if p.is_absolute() or ".." in p.parts or "\\" in path or path.startswith("~"):
        raise ValueError("Paths must be inside workspace, without .. or absolute paths.")
    target = (WORKSPACE / pathlib.Path(*p.parts)).resolve()
    if not target.is_relative_to(WORKSPACE.resolve()):
        raise ValueError("Path escapes workspace or uses an unsafe symlink.")
    if expect_file and (target == WORKSPACE.resolve() or target.suffix == ""):
        raise ValueError("Choose a specific file with an extension.")
    return target

def parse(command):
    if not command.startswith("/work "):
        raise ValueError("Use /work help for commands.")
    head, separator, body = command.partition("\n")
    words = head.strip().split(maxsplit=2)
    if len(words) < 2:
        raise ValueError("Use /work help.")
    op = words[1]
    value = words[2] if len(words) > 2 else ""
    if op in ("write", "append", "replace"):
        if not separator or not value:
            raise ValueError("Provide a filename, newline, then contents.")
        if len(body.encode("utf-8")) > MAX_FILE:
            raise ValueError("Input exceeds 160 KB limit.")
    elif op == "python":
        if not separator or not body.strip() or len(body.encode("utf-8")) > 16000:
            raise ValueError("Provide a newline and up to 16 KB of Python.")
    elif op not in ("help", "info", "list", "tree", "search", "read",
                    "run", "fetch", "zip", "delete", "task", "tasks", "memory", "context", "web", "github", "research", "tools"):
        raise ValueError("Allowed: help, tools, web, github, research, info, context, memory, tasks, task, list, tree, search, read, write, append, replace, delete, run, python, fetch, zip.")
    return op, value, body

def separator_is_present(command):
    return "\n" in command

def execute(command):
    op, val, body = parse(command)
    WORKSPACE.mkdir(exist_ok=True)
    if op in ("web", "github", "research"):
        return research_tools.run(WORKSPACE, resolve, op + " " + val)
    if op == "tools":
        return ("### Connected tool hub 🔗\n\n"
                "Web: /work web search QUERY; /work web get URL [output.txt]; "
                "/work web download URL output.ext\n"
                "GitHub: /work github repo OWNER/REPO; /work github tree OWNER/REPO [REF]; "
                "/work github file OWNER/REPO PATH [REF]; "
                "/work github download OWNER/REPO PATH OUTPUT [REF]; "
                "/work github archive OWNER/REPO OUTPUT.zip [REF]\n"
                "Research: /work research QUERY (searches, retrieves and saves a snapshot)\n"
                "Files saved under workspace/ can be read, searched, processed by offline Python "
                "and packed with /work zip. See README for complete syntax.")
    if op == "memory":
        return agent_memory.handle(WORKSPACE, val, body, has_newline=separator_is_present(command))
    if op == "context":
        if len(val) > 120:
            raise ValueError("Context filter must be at most 120 characters.")
        task_path = WORKSPACE / ".agent" / "tasks.json"
        tasks = json.loads(task_path.read_text(encoding="utf-8")) if task_path.exists() else []
        if not isinstance(tasks, list):
            raise ValueError("Task queue must be a list.")
        return agent_memory.context(WORKSPACE, tasks, val)
    if op in ("tasks", "task"):
        file = WORKSPACE / ".agent" / "tasks.json"
        tasks = json.loads(file.read_text(encoding="utf-8")) if file.exists() else []
        if not isinstance(tasks, list):
            raise ValueError("Malformed persistent task queue.")
        if op == "tasks":
            return "### Agent tasks 📋\n\n" + (
                "\n".join(f"{'✅' if t['done'] else '⬜'} #{t['id']}: {t['text']}"
                          for t in tasks[-100:])
                or "(No tasks. Add one with /work task add DESCRIPTION)")
        command, _, arg = val.partition(" ")
        arg = arg.strip()
        if command == "add":
            if not 1 <= len(arg) <= 240 or len(tasks) >= 200:
                raise ValueError("Task text must be 1–240 characters; max 200 tasks.")
            task_id = max((int(t["id"]) for t in tasks), default=0) + 1
            tasks.append({"id": task_id, "text": arg, "done": False})
            response = f"Added task #{task_id}: {arg}"
        elif command in ("done", "reopen"):
            if not arg.isdecimal():
                raise ValueError("Expected numeric task ID.")
            match = next((t for t in tasks if int(t["id"]) == int(arg)), None)
            if match is None:
                raise ValueError("Task not found.")
            match["done"] = (command == "done")
            response = f"Task #{arg} marked {'complete' if match['done'] else 'open'}."
        else:
            raise ValueError("Use /work task add DESCRIPTION, done ID, or reopen ID.")
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return response + " Saved in workspace/.agent/tasks.json."
    if op == "help":
        return ("### Agent workspace 🛠️\n\n"
                "/work info — file count, limits, capabilities\n"
                "/work tools — connected web/GitHub/research command hub\n"
                "/work web search QUERY / get URL [FILE] / download URL FILE\n"
                "/work github repo|tree|file|download|archive ...\n"
                "/work research QUERY — save an end-to-end research snapshot\n"
                "/work context [query] — load tasks + relevant memories\n"
                "/work memory help — memory commands, categories, cautions\n"
                "/work memory remember CATEGORY + NEWLINE + note\n"
                "/work memory search QUERY / list / show ID\n"
                "/work memory edit ID + NEWLINE + note / forget ID\n"
                "/work tasks — see persistent task queue\n"
                "/work task add DESCRIPTION — save a goal\n"
                "/work task done ID / reopen ID — update a task\n"
                "/work list [folder] — immediate children\n"
                "/work tree [folder] — recursive file tree\n"
                "/work search KEYWORD — find text across workspace files\n"
                "/work read path.txt — inspect text\n"
                "/work write path.txt + NEWLINE + text — create or overwrite\n"
                "/work append path.txt + NEWLINE + text — add to text file\n"
                "/work replace path.txt + NEWLINE + JSON — exact text replacement\n"
                "/work delete path.txt — remove a file\n"
                "/work run file.py [arguments] — execute saved script\n"
                "/work python + NEWLINE + Python code — execute inline\n"
                "/work fetch HTTPS_URL output.txt — fetch public file\n"
                "/work zip [output.zip] [folder] — create downloadable project archive\n\n"
                'Replace JSON: {"find":"old","replace":"new"}; add "all":true for every occurrence.\n'
                "All paths are inside workspace/. Files persist via Git commits. "
                "Python runs offline in a restricted container. Workspace is public.")
    if op == "info":
        files = [p for p in WORKSPACE.rglob("*") if p.is_file() and not p.is_symlink()]
        return ("### Workspace status 🐸\n\n"
                + f"Files: {len(files)}; size: {sum(p.stat().st_size for p in files):,} bytes\n"
                + "Python 3.12; 45 seconds, 384 MB RAM, one CPU, network-disabled.\n"
                + "Text operations: 160 KB per file. Search: 500 files/60 hits. ZIP: 300 files/10 MB.\n"
                + "Persistent files committed to the public GitHub repository; no container secrets.")
    if op == "list":
        folder = resolve(val)
        if not folder.is_dir():
            raise ValueError("Not a directory.")
        rows = sorted(folder.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        lines = [("DIR  " if p.is_dir() else "FILE ") + p.name for p in rows[:120]]
        return "### workspace/" + (val or "") + "\n\n" + "\n".join(lines or ["(empty)"])
    if op == "tree":
        folder = resolve(val)
        if not folder.is_dir():
            raise ValueError("Not a directory.")
        lines = []
        for p in sorted(folder.rglob("*")):
            if len(lines) >= 200:
                lines.append("…tree limited to 200 entries.")
                break
            label = "LINK " if p.is_symlink() else "DIR  " if p.is_dir() else "FILE "
            lines.append(label + p.relative_to(WORKSPACE).as_posix())
        return "### Workspace tree 🌳\n\n" + "\n".join(lines or ["(empty)"])
    if op == "search":
        needle = val.strip()
        if not needle or len(needle) > 120:
            raise ValueError("Provide a keyword of 1–120 characters.")
        matches = []
        scanned = 0
        for f in sorted(WORKSPACE.rglob("*")):
            if scanned >= 500 or len(matches) >= 60:
                break
            if f.is_symlink() or not f.is_file() or f.stat().st_size > MAX_FILE:
                continue
            scanned += 1
            data = f.read_bytes()
            if b"\x00" in data[:1024]:
                continue
            for lineno, line in enumerate(data.decode("utf-8", errors="replace").splitlines(), 1):
                if needle.casefold() in line.casefold():
                    matches.append(f"{f.relative_to(WORKSPACE).as_posix()}:{lineno}: {line[:200]}")
                if len(matches) >= 60:
                    break
        limited = "\n\nSearch limit reached." if scanned >= 500 or len(matches) >= 60 else ""
        return f"### Search: {needle} 🔎\n\n" + "\n".join(matches or ["No matches."]) + limited
    if op == "read":
        f = resolve(val, expect_file=True)
        if not f.is_file() or f.stat().st_size > MAX_FILE:
            raise ValueError("File missing or too large to read.")
        text = f.read_text(encoding="utf-8", errors="replace")
        return "### workspace/" + val + "\n\n" + "~~~text\n" + text[:20000] + "\n~~~"
    if op in ("append", "replace"):
        f = resolve(val, expect_file=True)
        if op == "append":
            existing = f.read_text(encoding="utf-8") if f.exists() else ""
            updated = existing + body
        else:
            if not f.is_file():
                raise ValueError("File does not exist.")
            options = json.loads(body)
            if not isinstance(options, dict):
                raise ValueError("Expected JSON object.")
            old, new = options.get("find"), options.get("replace")
            if not isinstance(old, str) or not old or not isinstance(new, str):
                raise ValueError("JSON requires a nonempty find string and replace string.")
            existing = f.read_text(encoding="utf-8")
            n = existing.count(old)
            if n < 1:
                raise ValueError("Exact search text not found.")
            if n != 1 and options.get("all") is not True:
                raise ValueError(f"Found {n} occurrences. Use all:true to replace every occurrence.")
            updated = existing.replace(old, new, -1 if options.get("all") is True else 1)
        if len(updated.encode("utf-8")) > MAX_FILE:
            raise ValueError("Result would exceed 160 KB.")
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(updated, encoding="utf-8")
        return f"{op.title()} succeeded: workspace/{val} ({len(updated.encode('utf-8'))} bytes)."
    if op == "delete":
        f = resolve(val, expect_file=True)
        if not f.is_file():
            raise ValueError("Only existing files can be deleted.")
        f.unlink()
        return "Deleted workspace/" + val
    if op == "zip":
        pieces = shlex.split(val)
        if len(pieces) > 2:
            raise ValueError("Use /work zip [output.zip] [source-directory].")
        f = resolve(pieces[0] if pieces else "artifacts/workspace-snapshot.zip", expect_file=True)
        folder = resolve(pieces[1] if len(pieces) == 2 else "")
        if f.suffix != ".zip" or not folder.is_dir():
            raise ValueError("Output must be a .zip file; source must be a directory.")
        sources = [p for p in sorted(folder.rglob("*"))
                   if p.is_file() and not p.is_symlink() and p != f
                   and p.resolve().is_relative_to(WORKSPACE.resolve())]
        if len(sources) > 300 or sum(p.stat().st_size for p in sources) > 10_000_000:
            raise ValueError("ZIP limited to 300 files and 10 MB uncompressed.")
        f.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(f, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sources:
                z.write(p, p.relative_to(folder).as_posix())
        return f"Created workspace/{f.relative_to(WORKSPACE).as_posix()} with {len(sources)} files ({f.stat().st_size} bytes)."
    if op == "write":
        f = resolve(val, expect_file=True)
        if len(val) > 180:
            raise ValueError("File path too long.")
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body, encoding="utf-8")
        return "Wrote workspace/" + val + " (" + str(len(body.encode())) + " bytes)."
    if op in ("run", "python"):
        args = shlex.split(val) if op == "run" else []
        if op == "run":
            if not args or len(args) > 16 or len(val) > 1000:
                raise ValueError("Use /work run path/to/script.py [arguments].")
            f = resolve(args[0], expect_file=True)
            if f.suffix != ".py" or not f.is_file():
                raise ValueError("Only existing Python .py files in workspace can run.")
            relative = f.relative_to(WORKSPACE).as_posix()
        else:
            relative = "(inline)"
        cmd = ["docker", "run", "--rm", "--network", "none", "--read-only",
               "--pids-limit", "64", "--memory", "384m", "--cpus", "1",
               "--security-opt", "no-new-privileges",
               "--user", str(os.getuid()) + ":" + str(os.getgid()),
               "--tmpfs", "/tmp:rw,nosuid,nodev,size=32m",
               "-v", str(WORKSPACE.resolve()) + ":/workspace:rw",
               "-w", "/workspace", "python:3.12-slim",
               "python", "-I", "-B"]
        cmd += [relative, *args[1:]] if op == "run" else ["-c", body]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=45, check=False)
        except subprocess.TimeoutExpired:
            return "Execution timed out; 45-second runner limit."
        return ("### Run " + relative + "\n\n"
                "Exit code: " + str(result.returncode) + "\n\n"
                "STDOUT:\n~~~text\n" + result.stdout[:13000] + "\n~~~\n\n"
                "STDERR:\n~~~text\n" + result.stderr[:7000] + "\n~~~")
    if op == "fetch":
        args = val.split()
        if len(args) != 2:
            raise ValueError("Use /work fetch HTTPS_URL output/file.ext")
        url, path = args
        parsed = urllib.parse.urlsplit(url)
        if (parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS or
            parsed.username or parsed.password or parsed.port or len(url) > 500):
            raise ValueError("Only approved public HTTPS hosts may be fetched.")
        f = resolve(path, expect_file=True)
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        opener = urllib.request.build_opener(NoRedirect)
        request = urllib.request.Request(url, headers={
            "User-Agent": "VillageChatGHWorkspace/0.1",
            "Accept": "text/plain,application/json,*/*"})
        with opener.open(request, timeout=22) as response:
            data = response.read(MAX_FILE + 1)
        if len(data) > MAX_FILE:
            raise ValueError("Response exceeds 160 KB download cap.")
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
        return "Fetched " + url + " into workspace/" + path + " (" + str(len(data)) + " bytes)."
    raise ValueError("Unknown operation.")

def main():
    event_path = os.environ["GITHUB_EVENT_PATH"]
    with open(event_path, encoding="utf-8") as f:
        event = json.load(f)
    owner = os.environ["GITHUB_REPOSITORY"].split("/")[0].casefold()
    issue = event["issue"]
    comment = event.get("comment") or {}
    if (issue.get("pull_request") or issue.get("user", {}).get("login", "").casefold() != owner
        or comment.get("user", {}).get("login", "").casefold() != owner):
        print("Unauthorized comment ignored.")
        return
    raw = comment.get("body", "")
    try:
        output = execute(raw)
        print("✅ " + output[:MAX_COMMENT])
    except Exception as exc:
        print("❌ Workspace error: " + type(exc).__name__ + ": " + str(exc)[:800])

if __name__ == "__main__":
    main()
