#!/usr/bin/env python3
"""Targeted recovery of AI Village GitLab archives without arbitrary file-size limits.

Reads the exact failures captured from the November 1, 2026 main export.
Archives 429 failures with respectful pacing, handles formerly oversized projects
individually, and audits 404 responses using project/branch metadata only.
It does NOT redownload the already-successful projects.
"""
import argparse
import collections
import datetime
import email.utils
import json
import random
import shutil
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

API = "https://gitlab.com/api/v4"
USER_AGENT = "AI-Village-Public-Archiver-Recovery/1.0"
TARGETS = Path(__file__).with_name("gitlab_recovery_targets.json")
ARCHIVE_GAP_SECONDS = 15.0
RETRIES = 10
_last_archive_start = 0.0


def retry_after_seconds(headers, attempt):
    value = headers.get("Retry-After", "")
    if value:
        try:
            return max(15.0, min(600.0, float(value) + 2.0))
        except ValueError:
            try:
                future = email.utils.parsedate_to_datetime(value)
                now = datetime.datetime.now(datetime.timezone.utc)
                return max(15.0, min(600.0, (future - now).total_seconds() + 2.0))
            except (ValueError, TypeError):
                pass
    return min(240.0, 20.0 * 2 ** min(attempt, 4)) + random.uniform(0, 3)


def gitlab_request(url, save_to=None, archive=False):
    """Return JSON bytes or stream a download to disk. Retry 429 and 5xx."""
    global _last_archive_start
    for attempt in range(RETRIES):
        if archive:
            delay = ARCHIVE_GAP_SECONDS - (time.monotonic() - _last_archive_start)
            if delay > 0:
                time.sleep(delay)
            _last_archive_start = time.monotonic()

        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"}, method="GET"
            )
            with urllib.request.urlopen(req, timeout=900) as response:
                if save_to is not None:
                    with open(save_to, "wb") as output:
                        shutil.copyfileobj(response, output, length=1024 * 1024)
                    return None
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == RETRIES - 1:
                raise
            delay = retry_after_seconds(exc.headers, attempt)
            print(f"  HTTP {exc.code}: retry {attempt+1}/{RETRIES-1} in {delay:.0f}s", flush=True)
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            if attempt == RETRIES - 1:
                raise
            delay = min(90, 5 * 2 ** attempt)
            print(f"  Network issue ({type(exc).__name__}): retry in {delay}s", flush=True)
            time.sleep(delay)


def gitlab_json(path, params=None):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return json.loads(gitlab_request(url))


def project_metadata(path):
    return gitlab_json("/projects/" + urllib.parse.quote(path, safe=""))


def checked_archive_member(member):
    if member.is_dir():
        return None
    pieces = member.filename.replace("\\", "/").split("/")
    # GitLab ZIPs have a generated top-level directory per project.
    relative = "/".join(pieces[1:])
    if (not relative or relative.startswith("/") or "\\" in member.filename
            or any(p in ("", ".", "..") for p in relative.split("/"))):
        raise ValueError("Unsafe path in GitLab archive: " + repr(member.filename))
    return relative


def metadata_404(path, record):
    """Check whether the previous 404 is likely an empty repository."""
    try:
        p = project_metadata(path)
        branch = p.get("default_branch")
        record["default_branch"] = branch
        record["empty_repo"] = p.get("empty_repo")
        if p.get("empty_repo") or not branch:
            record["status"] = "empty_or_uninitialized"
            return
        try:
            tree = gitlab_json(
                "/projects/" + str(p["id"]) + "/repository/tree",
                {"ref": branch, "per_page": 1},
            )
            record["branch_has_entries"] = bool(tree)
            record["status"] = "nonempty_archive_404" if tree else "branch_with_empty_tree"
        except urllib.error.HTTPError as exc:
            record["tree_lookup_http"] = exc.code
            if exc.code != 404:
                record["status"] = "branch_metadata_failed"
                record["detail"] = "HTTP " + str(exc.code)
                return
            # A tree 404 does not prove emptiness. List branches instead.
            try:
                branches = gitlab_json(
                    "/projects/" + str(p["id"]) + "/repository/branches",
                    {"per_page": 1},
                )
                if not isinstance(branches, list):
                    record["status"] = "invalid_branch_list_response"
                elif not branches:
                    record["status"] = "no_branches"
                else:
                    record["status"] = "branches_exist_but_tree_404"
                    record["sample_branch"] = branches[0].get("name")
            except urllib.error.HTTPError as branches_exc:
                record["status"] = "branch_list_unavailable"
                record["detail"] = "HTTP " + str(branches_exc.code)
    except urllib.error.HTTPError as exc:
        record["status"] = "project_metadata_failed"
        record["detail"] = "HTTP " + str(exc.code)
    except Exception as exc:
        record["status"] = "project_metadata_failed"
        record["detail"] = (type(exc).__name__ + ": " + str(exc))[:230]


def recover(path, record, destination):
    try:
        p = project_metadata(path)
        branch = p.get("default_branch")
        record["default_branch"] = branch
        if p.get("empty_repo") or not branch:
            record["status"] = "empty_or_uninitialized"
            return
        params = urllib.parse.urlencode({"sha": branch, "include_lfs_blobs": "false"})
        archive_url = API + "/projects/" + str(p["id"]) + "/repository/archive.zip?" + params
        print("Fetching:", path, flush=True)
        with tempfile.TemporaryDirectory() as tempdir:
            source = Path(tempdir) / "source.zip"
            # Stream to disk: no 512 MiB archive ceiling, no per-file limit.
            gitlab_request(archive_url, save_to=source, archive=True)
            record["source_zip_bytes"] = source.stat().st_size
            total = 0
            files = 0
            with zipfile.ZipFile(source, "r") as package:
                for member in package.infolist():
                    rel = checked_archive_member(member)
                    if rel is None:
                        continue
                    target_path = "repositories/" + path + "/" + rel
                    # Stream entry-by-entry; do not load large media files into RAM.
                    with package.open(member) as source_entry:
                        with destination.open(target_path, mode="w", force_zip64=True) as result_entry:
                            shutil.copyfileobj(source_entry, result_entry, length=1024 * 1024)
                    files += 1
                    total += member.file_size
            record.update(status="archived", files=files, uncompressed_bytes=total)
    except Exception as exc:
        record.update(status="download_failed",
                      error=(type(exc).__name__ + ": " + str(exc))[:250])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=("rate_limited_429", "source_zip_limit", "archive_404"), required=True)
    parser.add_argument("--path", help="Restrict to one recorded failure, e.g. an oversized project")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    manifest = json.loads(TARGETS.read_text(encoding="utf-8"))
    matching = [x for x in manifest["targets"] if x["reason"] == args.kind]
    if args.path:
        matching = [x for x in matching if x["path"] == args.path]
        if len(matching) != 1:
            parser.error("--path must match exactly one previously omitted project")

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    records = []
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=1, allowZip64=True) as destination:
        for i, item in enumerate(matching, 1):
            record = {"path": item["path"], "previous_error": item["reason"]}
            if args.kind == "archive_404":
                metadata_404(item["path"], record)
            else:
                recover(item["path"], record, destination)
            records.append(record)
            print(f"{i}/{len(matching)} {record['path']} => {record['status']}", record.get("error", ""), flush=True)
        counts = dict(collections.Counter(record["status"] for record in records))
        report = {
            "source_run": manifest["source_workflow_run"],
            "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "note": "Supplementary snapshots, not commit history; no artificial archive/file byte cap. 404 projects inspected via metadata only.",
            "counts": counts, "results": records
        }
        destination.writestr("MANIFEST.json", json.dumps(report, indent=2))
    print("RECOVERY RESULT", output, output.stat().st_size, "bytes; counts:", counts, flush=True)
    if (summary := __import__("os").environ.get("GITHUB_STEP_SUMMARY")):
        with open(summary, "a", encoding="utf-8") as file:
            file.write(f"## GitLab recovery: {args.kind}\n\n" +
                       f"{len(matching)} targets; statuses: {json.dumps(counts)}\n\n")

if __name__ == "__main__":
    main()
