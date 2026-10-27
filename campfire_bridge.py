"""Owner-only bridge for CAMPFIRE's public, account-free agent board.

Commands (one GitHub issue comment each):
  /campfire post\nTitle\nBody
  /campfire read
  /campfire thread ID

This intentionally permits no arbitrary URL, credentials, or batch posts.
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any

BASE = "https://agentsboard.org/api/v1"
UA = "Minuteandone-AgentCommunityBridge/1.0"


def call(url: str, *, body: dict[str, Any] | None = None,
         request_id: str | None = None) -> dict:
    if not (url == BASE + "/feed" or url == BASE + "/threads"
            or re.fullmatch(re.escape(BASE) + r"/threads/[1-9]\d*(?:/replies)?", url)):
        raise ValueError("Endpoint not allowed")
    headers = {"Accept": "application/json", "User-Agent": UA}
    if body is not None:
        headers["Content-Type"] = "application/json"
        if request_id:
            headers["X-Request-Id"] = request_id
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers,
                                 method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read(128_000).decode("utf-8"))


def github_safe(text: str) -> str:
    # Prevent unrelated GitHub users from being pinged by quoted board messages.
    return re.sub(r"@(?![\u200b\u200c\u200d])", "@\u200b", text)


def issue_reply(message: str, event: dict) -> None:
    repo = os.environ["GITHUB_REPOSITORY"]
    n = event["issue"]["number"]
    token = os.environ["GITHUB_TOKEN"]
    url = f"https://api.github.com/repos/{repo}/issues/{n}/comments"
    data = json.dumps({"body": github_safe(message[:30_000])}).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    }, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        resp.read()


def handle(command: str, issue_comment_id: int) -> str:
    command = command.strip()
    if command.startswith("/campfire post\n"):
        parts = command.split("\n", 2)
        if len(parts) != 3:
            return "Post requires title and body on separate lines."
        title, body = parts[1].strip(), parts[2].strip()
        if not (1 <= len(title) <= 160 and 1 <= len(body) <= 8000):
            return "Refused: title must be 1-160 and body 1-8000 characters."
        if len(json.dumps({"title":title,"body":body}).encode()) > 31_000:
            return "Refused: payload too large."
        outcome = call(BASE + "/threads", body={
            "title": title,
            "body": body,
            "author": "Starpettergpt",
            "category": "discussion",
        }, request_id=f"github-comment-{issue_comment_id}")
        identifier = outcome.get("id") or (outcome.get("thread") or {}).get("id")
        link = f"https://agentsboard.org/thread/{identifier}" if identifier is not None else "(check site feed)"
        return f"CAMPFIRE accepted the prank thread! 🏕️\nThread ID: {identifier}\nPotential thread page: {link}\nResponse: `{json.dumps(outcome, ensure_ascii=False)[:2000]}`"
    if command == "/campfire read":
        result = call(BASE + "/feed")
        rendered = json.dumps(result, ensure_ascii=False)
        return "### CAMPFIRE public feed\n```json\n" + rendered[:24_000] + "\n```"
    if re.fullmatch(r"/campfire thread [1-9]\d{0,9}", command):
        identifier = command.split()[-1]
        result = call(BASE + f"/threads/{identifier}")
        return f"### CAMPFIRE thread {identifier}\n```json\n{json.dumps(result, ensure_ascii=False)[:24_000]}\n```"
    return "Supported: `/campfire read`, `/campfire thread ID`, or `/campfire post` followed by a title line and body."


def main() -> None:
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
        event = json.load(f)
    owner = os.environ["GITHUB_REPOSITORY"].split("/", 1)[0]
    comment = event.get("comment") or {}
    issue = event.get("issue") or {}
    if (comment.get("user", {}).get("login") != owner
            or issue.get("user", {}).get("login") != owner
            or issue.get("pull_request")):
        raise SystemExit("Refusing non-owner or PR command")
    cmd = comment.get("body", "")
    if not cmd.startswith("/campfire "):
        raise SystemExit("Not a CAMPFIRE command")
    try:
        result = handle(cmd, int(comment["id"]))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, KeyError) as e:
        result = "CAMPFIRE request failed (no automatic retries): " + str(e)[:350]
    print(result)
    issue_reply(result, event)


if __name__ == "__main__":
    main()
