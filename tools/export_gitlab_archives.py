#!/usr/bin/env python3
"""Combine publicly accessible AI Village GitLab default-branch snapshots into a ZIP."""
import concurrent.futures
import datetime
import io
import json
import os
import random
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

API = "https://gitlab.com/api/v4"
GROUPS = ["ai-village-agents", "ai-village-agents/village",
          "ai-village-agents/open-chat", "ai-village-agents/game-jam"]
MAX_ZIP = 256 * 1024 * 1024
MAX_FILE = 128 * 1024 * 1024
MAX_TOTAL = 4 * 1024 * 1024 * 1024
def fetch(url, limit=None):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AI-Village-Public-Archiver/1.0"})
            with urllib.request.urlopen(req, timeout=75) as response:
                data = response.read(limit + 1 if limit is not None else -1)
                if limit is not None and len(data) > limit:
                    raise ValueError("source ZIP exceeds archive-size limit")
                return data
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            if getattr(exc, "code", None) in (401, 403, 404) or attempt == 3:
                raise
            time.sleep(2 ** attempt * 2 + random.random())

def discover():
    discovered = {}
    successes = 0
    for group in GROUPS:
        try:
            page = 1
            while page <= 1000:
                query = urllib.parse.urlencode({"include_subgroups": "true",
                     "simple": "true", "per_page": 100, "page": page})
                url = API + "/groups/" + urllib.parse.quote(group, safe="") + "/projects?" + query
                entries = json.loads(fetch(url))
                if not isinstance(entries, list):
                    raise ValueError("Invalid project-list response")
                successes += 1
                for p in entries:
                    if p.get("visibility") == "public":
                        discovered[p["id"]] = p
                print("Discover", group, "page", page, "items", len(entries), flush=True)
                if len(entries) < 100:
                    break
                page += 1
        except Exception as exc:
            print("Discovery failed:", group, str(exc)[:170], flush=True)
    if successes == 0:
        raise RuntimeError("No GitLab groups could be enumerated")
    return sorted(discovered.values(), key=lambda p: p.get("path_with_namespace", ""))

def eligible(project):
    # No keyword-based exclusions: preserve every discoverable public project.
    return project.get("visibility") == "public"

def download(project):
    branch = project.get("default_branch")
    record = {"id": project["id"], "name": project.get("path_with_namespace", ""),
              "url": project.get("web_url", ""), "branch": branch,
              "status": "unknown"}
    if not branch or project.get("empty_repo"):
        record["status"] = "empty"
        return record, None
    params = urllib.parse.urlencode({"sha": branch, "include_lfs_blobs": "false"})
    url = API + "/projects/" + str(project["id"]) + "/repository/archive.zip?" + params
    try:
        payload = fetch(url, MAX_ZIP)
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            for member in zf.infolist():
                if member.is_dir():
                    continue
                rel = "/".join(member.filename.split("/")[1:])
                if not rel or rel.startswith("/") or ".." in rel.split("/") or "\\" in rel:
                    raise ValueError("Invalid path in downloaded ZIP")
                if member.file_size > MAX_FILE:
                    raise ValueError("Source contains oversized file")
            record["uncompressed_bytes"] = sum(x.file_size for x in zf.infolist() if not x.is_dir())
            record["file_count"] = sum(not x.is_dir() for x in zf.infolist())
        record["status"] = "downloaded"
        return record, payload
    except Exception as exc:
        record["status"] = "error"
        record["error"] = (type(exc).__name__ + ": " + str(exc))[:220]
        return record, None

def main():
    all_projects = discover()
    selected = [p for p in all_projects if eligible(p)]
    print("Public projects", len(all_projects), "eligible", len(selected), flush=True)
    output = Path("output/ai-village-gitlab-public.zip")
    output.parent.mkdir(parents=True, exist_ok=True)
    records, total_bytes = [], 0
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6, allowZip64=True) as dst:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            for i, (record, payload) in enumerate(pool.map(download, selected), 1):
                if payload:
                    if record["uncompressed_bytes"] + total_bytes > MAX_TOTAL:
                        record["status"] = "bundle_limit"
                    else:
                        with zipfile.ZipFile(io.BytesIO(payload)) as src:
                            root = "repositories/" + record["name"] + "/"
                            for member in src.infolist():
                                if member.is_dir():
                                    continue
                                rel = "/".join(member.filename.split("/")[1:])
                                dst.writestr(root + rel, src.read(member))
                        total_bytes += record["uncompressed_bytes"]
                records.append(record)
                if i % 25 == 0 or i == len(selected):
                    print("Downloaded", i, "/", len(selected), flush=True)
        counts = {state: sum(p["status"] == state for p in records)
                  for state in ("downloaded", "error", "empty", "bundle_limit")}
        manifest = {"generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "scope": "Public AI Village GitLab projects (root and subgroups)",
                    "note": "Default branch snapshots only; private repositories, Git history, and LFS binaries are not included. No keyword-based project exclusions.",
                    "public_projects_found": len(all_projects),
                    "counts": counts, "projects": records}
        dst.writestr("MANIFEST.json", json.dumps(manifest, indent=2))
        dst.writestr("README.txt", "AI Village public GitLab repositories; default-branch file snapshots.\n"
                     "Browse repositories/ for files and MANIFEST.json for all included and failed records.\n"
                     "Not a Git history, private repository, or Git LFS export.\n")
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write("## GitLab archive\n\n" + json.dumps(counts) +
                         f"\n\nPublic found: {len(all_projects)}; output bytes: {output.stat().st_size}.\n")
    print("ARCHIVE", output, "bytes", output.stat().st_size, "counts", counts, flush=True)

if __name__ == "__main__":
    main()
