#!/usr/bin/env python3
"""Download public AI Village GitLab repositories into one ZIP.

No arbitrary per-source ZIP limit, per-file limit, or combined uncompressed-size
cap. Archives are streamed to temporary disk files and entries are streamed into
the final ZIP to keep memory consumption bounded. Physical disk/artifact limits
still apply.
"""
import collections
import datetime
import json
import shutil
import tempfile
import urllib.error
import urllib.parse
import zipfile
from pathlib import Path

from recover_gitlab_archives import API, gitlab_json, gitlab_request, checked_archive_member

GROUPS = ["ai-village-agents", "ai-village-agents/village",
          "ai-village-agents/open-chat", "ai-village-agents/game-jam"]


def discover():
    discovered = {}
    completed_groups = []
    failed_groups = []
    for group in GROUPS:
        page = 1
        try:
            while page <= 1000:
                entries = gitlab_json(
                    "/groups/" + urllib.parse.quote(group, safe="") + "/projects",
                    {"include_subgroups": "true", "simple": "true", "per_page": 100, "page": page},
                )
                if not isinstance(entries, list):
                    raise ValueError("Invalid project listing")
                for project in entries:
                    if project.get("visibility") == "public":
                        discovered[project["id"]] = project
                print("Discover", group, "page", page, "items", len(entries), flush=True)
                if len(entries) < 100:
                    break
                page += 1
            completed_groups.append(group)
        except Exception as exc:
            failed_groups.append({"group": group, "error": str(exc)[:240]})
            print("Discovery error for", group, str(exc)[:200], flush=True)
    if not completed_groups:
        raise RuntimeError("No GitLab groups were enumerated successfully")
    return sorted(discovered.values(), key=lambda p: p.get("path_with_namespace", "")), failed_groups


def export_project(project, target):
    name = project["path_with_namespace"]
    branch = project.get("default_branch")
    record = {"id": project["id"], "name": name,
              "url": project.get("web_url", ""), "branch": branch}
    if project.get("empty_repo") or not branch:
        record["status"] = "empty"
        return record
    params = urllib.parse.urlencode({"sha": branch, "include_lfs_blobs": "false"})
    endpoint = API + "/projects/" + str(project["id"]) + "/repository/archive.zip?" + params
    try:
        with tempfile.TemporaryDirectory() as work:
            tempzip = Path(work) / "gitlab-source.zip"
            # Retry 429 and transient errors. Do not load ZIP bytes into memory.
            gitlab_request(endpoint, save_to=tempzip, archive=False)
            nfiles, nbytes = 0, 0
            with zipfile.ZipFile(tempzip, "r") as source:
                for info in source.infolist():
                    relative = checked_archive_member(info)
                    if relative is None:
                        continue
                    with source.open(info) as src, target.open(
                        "repositories/" + name + "/" + relative,
                        mode="w", force_zip64=True,
                    ) as dest:
                        shutil.copyfileobj(src, dest, length=1024 * 1024)
                    nfiles += 1
                    nbytes += info.file_size
            record.update({"status": "downloaded", "files": nfiles,
                           "uncompressed_bytes": nbytes,
                           "source_zip_bytes": tempzip.stat().st_size})
    except Exception as exc:
        record.update({"status": "error", "error": (type(exc).__name__ + ": " + str(exc))[:240]})
    return record


def main():
    projects, failed_groups = discover()
    print("Public projects", len(projects), "eligible", len(projects), flush=True)
    output = Path("output/ai-village-gitlab-public.zip")
    output.parent.mkdir(parents=True, exist_ok=True)
    records = []
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=1, allowZip64=True) as target:
        for index, project in enumerate(projects, 1):
            record = export_project(project, target)
            records.append(record)
            if record["status"] == "error":
                print("OMITTED", record["name"], record["error"], flush=True)
            if index % 25 == 0 or index == len(projects):
                print("Processed", index, "/", len(projects),
                      "success", sum(r["status"] == "downloaded" for r in records),
                      flush=True)
        counts = dict(collections.Counter(r["status"] for r in records))
        manifest = {
            "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "scope": "Discoverable public AI Village GitLab projects",
            "note": "Default-branch files; no Git history or LFS blobs. No artificial size exclusions. Disk and GitHub artifact limits still apply.",
            "public_projects_found": len(projects),
            "failed_group_enumerations": failed_groups,
            "counts": counts, "projects": records,
        }
        target.writestr("MANIFEST.json", json.dumps(manifest, indent=2))
        target.writestr("README.txt", "Public AI Village GitLab default-branch snapshots.\n"
                         "See MANIFEST.json for included, empty, and failed repositories.\n")
    print("ARCHIVE", output, "bytes", output.stat().st_size, "counts", counts, flush=True)
    if summary := __import__("os").environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a", encoding="utf-8") as file:
            file.write("## AI Village archive\n\n" + json.dumps(counts) +
                       f"\n\nPublic projects: {len(projects)}; ZIP bytes: {output.stat().st_size}\n")

if __name__ == "__main__":
    main()
