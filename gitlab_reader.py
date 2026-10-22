"""Read-only GitLab browsing for public AI Village projects."""
import json
import re
import urllib.parse
import urllib.request
import urllib.error

API = "https://gitlab.com/api/v4"
ROOT = "ai-village-agents"
ALLOWED_GROUPS = ("village", "open-chat")
UA = "VillageChatGitHubBridge/0.2"

def get(path, params=None, raw=False):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA,
        "Accept": "text/plain" if raw else "application/json"}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            data = response.read(25000 if raw else 250000)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403, 404):
            raise ValueError("GitLab resource not found or not publicly readable.") from exc
        raise RuntimeError(f"GitLab HTTP {exc.code}") from exc
    return data.decode("utf-8", "replace") if raw else json.loads(data)

def project_name(value):
    if value.startswith(ROOT + "/"):
        value = value[len(ROOT) + 1:]
    parts = value.split("/")
    if len(parts) == 1:
        parts = ["village", parts[0]]
    if len(parts) != 2 or parts[0] not in ALLOWED_GROUPS:
        raise ValueError("Use a public project slug, or open-chat/PROJECT or village/PROJECT.")
    name = parts[1]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,100}", name) or name in (".", ".."):
        raise ValueError("Invalid AI Village project slug.")
    return ROOT + "/" + parts[0] + "/" + name

def trunc(value, length=12000):
    s = str(value or "")
    return s[:length] + ("\n[truncated]" if len(s) > length else "")

def read_project(slug, operation="summary", argument=""):
    name = project_name(slug)
    root = "/projects/" + urllib.parse.quote(name, safe="")
    proj = get(root)
    title = proj.get("path_with_namespace", name)
    head = "### GitLab read-only: " + str(title) + "\n\n"
    if operation in ("", "summary", "project"):
        return head + "\n".join([
            "URL: " + str(proj.get("web_url", "")),
            "Visibility: " + str(proj.get("visibility", "unknown")),
            "Default branch: " + str(proj.get("default_branch", "unknown")),
            "Description: " + trunc(proj.get("description", ""), 1000),
            "Last activity: " + str(proj.get("last_activity_at", "unknown")),
            "",
            "Commands: tree [directory], file PATH, mrs, mr IID, diff IID, issues, issue IID.",
        ])
    if operation == "tree":
        path = argument.strip()
        if path.startswith("/") or ".." in path.split("/"):
            raise ValueError("Use a normal repository-relative directory path.")
        files = get(root + "/repository/tree", {"path": path, "per_page": 100})
        if not isinstance(files, list):
            raise ValueError("Invalid GitLab directory response.")
        return head + "Directory: " + (path or "/") + "\n\n" + "\n".join(
            ("📁 " if row.get("type") == "tree" else "📄 ") +
            str(row.get("path", "")) for row in files
        ) + ("\n(Up to 100 entries shown)" if len(files) == 100 else "")
    if operation == "file":
        path = argument.strip()
        if not path or path.startswith("/") or ".." in path.split("/") or len(path) > 300:
            raise ValueError("Supply a repository-relative file path.")
        route = root + "/repository/files/" + urllib.parse.quote(path, safe="") + "/raw"
        contents = get(route, {"ref": proj.get("default_branch") or "main"}, raw=True)
        return head + "File: " + path + "\n\n" + "~~~text\n" + trunc(contents, 13000) + "\n~~~"
    if operation in ("mrs", "issues"):
        route = "/merge_requests" if operation == "mrs" else "/issues"
        values = get(root + route, {"state": "opened", "per_page": 25})
        if not isinstance(values, list):
            raise ValueError("Invalid GitLab listing.")
        lines = [head, "Open merge requests" if operation == "mrs" else "Open issues", ""]
        for item in values:
            lines.append(("#" if operation == "issues" else "!") +
                         str(item.get("iid")) + " " + trunc(item.get("title", ""), 130) +
                         " — " + str(item.get("web_url", "")))
        if not values:
            lines.append("(none returned)")
        return "\n".join(lines)
    if operation in ("mr", "diff", "issue"):
        if not re.fullmatch(r"[1-9][0-9]{0,7}", argument.strip()):
            raise ValueError("Provide a positive merge request or issue IID.")
        iid = argument.strip()
        route = "/issues/" + iid if operation == "issue" else "/merge_requests/" + iid
        obj = get(root + route)
        lines = [head, ("Issue #" if operation == "issue" else "MR !") +
                 iid + ": " + str(obj.get("title", "")), "",
                 "Status: " + str(obj.get("state", "")),
                 "URL: " + str(obj.get("web_url", "")),
                 "Updated: " + str(obj.get("updated_at", ""))]
        if operation != "issue":
            lines += ["Branch: " + str(obj.get("source_branch", "")) +
                      " → " + str(obj.get("target_branch", "")),
                      "Merge status: " + str(obj.get("merge_status", ""))]
        lines += ["", "Description:", trunc(obj.get("description", "(none)"), 7000)]
        if operation == "diff":
            changes = get(root + "/merge_requests/" + iid + "/diffs", {"per_page": 10})
            lines += ["", "Changed files (up to 10):"]
            for change in changes if isinstance(changes, list) else []:
                lines += ["", "File: " + str(change.get("new_path", "")),
                          "~~~diff", trunc(change.get("diff", ""), 1400), "~~~"]
        return "\n".join(lines)
    raise ValueError("Commands: summary, tree [directory], file PATH, mrs, mr IID, diff IID, issues, issue IID.")

def run(slug, spec):
    words = spec.strip().split(maxsplit=1)
    operation = words[0].lower() if words else "summary"
    argument = words[1] if len(words) > 1 else ""
    return trunc(read_project(slug, operation, argument), 22000)
