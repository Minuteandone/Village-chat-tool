#!/usr/bin/env python3
"""Metadata-only dry run of the existing AI Village GitLab archive filter.

Does not download project contents, repository ZIPs, or source files.
"""
import datetime
import json
from pathlib import Path
from export_gitlab_archives import discover, eligible, RESTRICTED

def main():
    projects = discover()  # Existing group enumeration; GitLab project metadata only.
    excluded = []
    included = []
    for project in projects:
        fields = ["name", "path_with_namespace", "description"]
        checked = {k: str(project.get(k) or "") for k in fields}
        checked["topics"] = " ".join(project.get("topics") or [])
        # Match exactly the concatenated string built by eligible().
        combined = " ".join(checked[k] for k in fields) + " " + checked["topics"]
        matched = RESTRICTED.search(combined)
        result = {
            "path": project.get("path_with_namespace", ""),
            "url": project.get("web_url", ""),
            "matched_text": matched.group(0) if matched else None,
            "matched_fields": [k for k in checked if RESTRICTED.search(checked[k])],
        }
        if not eligible(project):
            excluded.append(result)
        else:
            included.append(result["path"])
    report = {
        "generated_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "type": "metadata-only dry-run",
        "total_public_projects": len(projects),
        "would_include": len(included),
        "would_exclude": len(excluded),
        "excluded": excluded,
        "included_paths": included,
    }
    target = Path("output/gitlab-exclusion-audit.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"PUBLIC PROJECTS: {len(projects)}")
    print(f"WOULD INCLUDE: {len(included)}")
    print(f"WOULD EXCLUDE: {len(excluded)}")
    for i, row in enumerate(excluded, 1):
        print(f"{i}. {row['path']} | match: {row['matched_text']} | fields: {','.join(row['matched_fields'])}")
    print(f"Audit JSON: {target}")

if __name__ == "__main__":
    main()
