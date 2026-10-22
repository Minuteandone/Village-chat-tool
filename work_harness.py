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
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
WORKSPACE = ROOT / "workspace"
MAX_FILE = 160_000
MAX_COMMENT = 28_000
ALLOWED_HOSTS = {"raw.githubusercontent.com", "theaidigest.org",
                 "gitlab.com", "api.github.com"}

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
    if command.startswith("/work write "):
        head, separator, body = command.partition("\n")
        if not separator:
            raise ValueError("Write needs a newline after the filename.")
        filename = head[len("/work write "):].strip()
        if not filename or len(body.encode("utf-8")) > MAX_FILE:
            raise ValueError("Missing filename or file contents exceed limit.")
        return "write", filename, body
    parts = command.strip().split(maxsplit=2)
    if len(parts) < 2:
        raise ValueError("Use /work help.")
    op = parts[1]
    value = parts[2] if len(parts) > 2 else ""
    if op not in ("help", "list", "read", "run", "fetch"):
        raise ValueError("Allowed: help, list, read, write, run, fetch.")
    return op, value, ""

def execute(command):
    op, val, body = parse(command)
    WORKSPACE.mkdir(exist_ok=True)
    if op == "help":
        return ("### Owner-only remote workspace 🛠️\n\n"
                "/work list [directory]\n"
                "/work read path/to/file.txt\n"
                "/work write path/to/file.py followed by NEWLINE and contents\n"
                "/work run path/to/file.py (Python 3.12, no network, 45s limit)\n"
                "/work fetch https://raw.githubusercontent.com/... local/file.txt\n\n"
                "All paths are relative to workspace/. Changed files are committed "
                "back to the repository. No arbitrary shell execution or private URLs.")
    if op == "list":
        folder = resolve(val)
        if not folder.is_dir():
            raise ValueError("Not a directory.")
        rows = sorted(folder.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        lines = [("DIR  " if p.is_dir() else "FILE ") + p.name for p in rows[:120]]
        return "### workspace/" + (val or "") + "\n\n" + "\n".join(lines or ["(empty)"])
    if op == "read":
        f = resolve(val, expect_file=True)
        if not f.is_file() or f.stat().st_size > MAX_FILE:
            raise ValueError("File missing or too large to read.")
        text = f.read_text(encoding="utf-8", errors="replace")
        return "### workspace/" + val + "\n\n" + "~~~text\n" + text[:20000] + "\n~~~"
    if op == "write":
        f = resolve(val, expect_file=True)
        if len(val) > 180:
            raise ValueError("File path too long.")
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body, encoding="utf-8")
        return "Wrote workspace/" + val + " (" + str(len(body.encode())) + " bytes)."
    if op == "run":
        f = resolve(val, expect_file=True)
        if f.suffix != ".py" or not f.is_file():
            raise ValueError("Only existing Python .py files in workspace can run.")
        relative = f.relative_to(WORKSPACE).as_posix()
        cmd = ["docker", "run", "--rm", "--network", "none", "--read-only",
               "--pids-limit", "64", "--memory", "384m", "--cpus", "1",
               "--security-opt", "no-new-privileges",
               "--user", str(os.getuid()) + ":" + str(os.getgid()),
               "--tmpfs", "/tmp:rw,nosuid,nodev,size=32m",
               "-v", str(WORKSPACE.resolve()) + ":/workspace:rw",
               "-w", "/workspace", "python:3.12-slim",
               "python", "-I", "-B", relative]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    timeout=60, check=False)
        except subprocess.TimeoutExpired:
            return "Execution timed out; 60-second runner limit."
        return ("### Run workspace/" + relative + "\n\n"
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
