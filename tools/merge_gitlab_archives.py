#!/usr/bin/env python3
"""Merge already-downloaded AI Village archives in place (no GitLab requests).

The base ZIP is renamed, not copied, to minimize disk usage on GitHub runners.
The two large recovery ZIPs and the 27-project patch are appended. The 404
branch-verification report supplies directory entries for empty projects.
argon-3d-fidelity-atlas is deliberately excluded.
"""
import argparse
import collections
import datetime
import json
import os
import shutil
import zipfile
from pathlib import Path

EXCLUDED = "ai-village-agents/village/argon-3d-fidelity-atlas"
PATCHES = {
    "429": 27,
    "lumen-series": 1,
    "village-videos": 1,
}

def read_manifest(path):
    with zipfile.ZipFile(path, "r") as archive:
        return json.loads(archive.read("MANIFEST.json"))

def check_file_entry(name):
    if (not name.startswith("repositories/") or name.startswith("/")
            or "\\" in name or any(p in ("", ".", "..") for p in name.split("/"))):
        raise ValueError("Invalid ZIP path: " + repr(name))
    if name.startswith("repositories/" + EXCLUDED + "/"):
        raise ValueError("Excluded repository appeared in ZIP: " + name)

def combine(base, patches, empty_audit, dest):
    if dest.exists():
        raise FileExistsError("Refusing to overwrite " + str(dest))
    original_manifest = read_manifest(base)
    projects = original_manifest["projects"]
    lookup = {p["name"]: p for p in projects}
    if len(lookup) != len(projects):
        raise ValueError("Duplicate projects in original manifest")
    base_names = {p["name"] for p in projects if p["status"] == "downloaded"}
    if EXCLUDED not in lookup:
        raise ValueError("Excluded project not found in main manifest")
    if lookup[EXCLUDED]["status"] == "downloaded":
        raise ValueError("Excluded project already archived in main ZIP")

    expected_missing = {p["name"] for p in projects if p["status"] != "downloaded"}
    audit = read_manifest(empty_audit)
    empty_records = audit["results"]
    empties = {r["path"] for r in empty_records if r["status"] == "no_branches"}
    if len(empty_records) != 29 or len(empties) != 29:
        raise ValueError("404 audit did not verify all 29 no-branch projects")
    if not empties <= expected_missing:
        raise ValueError("404 audit conflicts with base manifest")

    patch_data = {}
    patch_projects = set()
    for label, patch_path in patches.items():
        manifest = read_manifest(patch_path)
        results = manifest["results"]
        recovered = [p["path"] for p in results if p["status"] == "archived"]
        if len(recovered) != PATCHES[label] or len(results) != PATCHES[label]:
            raise ValueError(f"Patch {label} did not recover all {PATCHES[label]} projects")
        if any(n in patch_projects or n in base_names or n in empties or n == EXCLUDED for n in recovered):
            raise ValueError("Duplicate or excluded recovery project in " + label)
        patch_projects.update(recovered)
        patch_data[label] = {"path": patch_path, "names": set(recovered), "results": results}

    all_names = base_names | patch_projects | empties
    expected_names = set(lookup) - {EXCLUDED}
    if all_names != expected_names:
        print("Missing:", sorted(expected_names - all_names), flush=True)
        print("Unexpected:", sorted(all_names - expected_names), flush=True)
        raise ValueError("Combined repository coverage is incomplete")
    print(f"Validated: {len(base_names)} base + {len(patch_projects)} recovered + {len(empties)} empty = {len(all_names)} projects", flush=True)

    dest.parent.mkdir(parents=True, exist_ok=True)
    # Both paths are on the same local runner volume. This does not duplicate
    # the 6 GB base archive and preserves its original entry compression.
    base.rename(dest)
    try:
        with zipfile.ZipFile(dest, mode="a", compression=zipfile.ZIP_DEFLATED,
                             compresslevel=1, allowZip64=True) as target:
            existing = set(target.namelist())
            for label, bundle in patch_data.items():
                with zipfile.ZipFile(bundle["path"], "r") as source:
                    copied = 0
                    for info in source.infolist():
                        if info.is_dir():
                            continue
                        name = info.filename
                        if name == "MANIFEST.json":
                            continue
                        check_file_entry(name)
                        if name in existing:
                            raise ValueError("Duplicate ZIP member: " + name)
                        # Confirm the member belongs to a repo recorded in
                        # this supplement, not merely an arbitrary repository.
                        if not any(name.startswith("repositories/" + n + "/") for n in bundle["names"]):
                            raise ValueError("Unexpected project in supplement: " + name)
                        with source.open(info) as reader:
                            with target.open(name, "w", force_zip64=True) as writer:
                                shutil.copyfileobj(reader, writer, length=1024 * 1024)
                        existing.add(name)
                        copied += 1
                print("Appended", label, "repositories", len(bundle["names"]), "files", copied, flush=True)

            for name in sorted(empties):
                dirname = "repositories/" + name + "/"
                if dirname not in existing:
                    target.writestr(dirname, "")
                    existing.add(dirname)

            final_projects = []
            for name in sorted(all_names):
                if name in base_names:
                    status, source = "archived", "original_full_export"
                elif name in empties:
                    status, source = "empty_no_branches", "verified_404_metadata"
                else:
                    status, source = "archived", next(k for k,v in patch_data.items() if name in v["names"])
                final_projects.append({"name": name, "url": lookup[name].get("url"),
                                       "status": status, "source": source})

            combined = {
                "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "description": "Combined public AI Village GitLab default-branch repository snapshots; excludes argon-3d-fidelity-atlas",
                "original_export_run_id": 41327050023,
                "recovery_run_id": 41328846868,
                "no_branch_verification_run_id": 41329076750,
                "source_project_count": len(projects),
                "excluded_project": EXCLUDED,
                "archived_project_count": len(base_names) + len(patch_projects),
                "empty_project_count": len(empties),
                "represented_project_count": len(all_names),
                "note": "Original MANIFEST.json belongs to the earlier full export and contains historic error statuses. COMBINED_MANIFEST.json is authoritative. This bundle contains default branches only, not commit history or Git LFS binaries.",
                "projects": final_projects,
            }
            target.writestr("COMBINED_MANIFEST.json", json.dumps(combined, indent=2, ensure_ascii=False))
            target.writestr(
                "README_FIRST.txt",
                "AI VILLAGE GITLAB BUNDLE -- EXCLUDING ARGON-3D-FIDELITY-ATLAS\n"
                f"All {len(all_names)} public GitLab projects besides the deliberately excluded atlas are represented.\n"
                f"{len(base_names) + len(patch_projects)} contain archived code, and {len(empties)} have no branches and are shown as empty directories.\n"
                "Read COMBINED_MANIFEST.json for the final project inventory.\n"
                "The older MANIFEST.json is kept for provenance, not as the final count.\n"
                "This ZIP is a default-branch snapshot, not full Git history or Git LFS binaries.\n"
            )
        # Detect structural corruption in central directory and name listing.
        with zipfile.ZipFile(dest, "r") as verified:
            names = set(verified.namelist())
            if "COMBINED_MANIFEST.json" not in names or any(
                name.startswith("repositories/" + EXCLUDED + "/") for name in names
            ):
                raise ValueError("Post-merge validation failed")
        print("SUCCESS: merged archive", dest, "bytes", dest.stat().st_size,
              "projects", len(all_names), flush=True)
    except Exception:
        # The moved base file remains available for debugging; never label
        # partial output complete.
        raise

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--patch429", type=Path, required=True)
    parser.add_argument("--lumen", type=Path, required=True)
    parser.add_argument("--videos", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    combine(
        a.base,
        {"429": a.patch429, "lumen-series": a.lumen, "village-videos": a.videos},
        a.audit, a.output
    )

if __name__ == "__main__":
    main()
