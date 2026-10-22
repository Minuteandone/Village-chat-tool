#!/usr/bin/env python3
"""Owner-only GitHub Issues bridge to AI Digest's public AI Village events."""
import json
import os
import time
import urllib.parse
import urllib.request
import urllib.error

BASE = "https://theaidigest.org/village"
UA = "VillageChatGitHubBridge/0.1 (github.com/Minuteandone/Village-chat-tool)"

def call(url, data=None, token=None, tries=3):
    headers = {"Accept": "application/json", "User-Agent": UA}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    payload = None if data is None else json.dumps(data).encode()
    for attempt in range(tries + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, payload, headers), timeout=30) as response:
                return json.loads(response.read(3_000_000) or b"{}")
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == tries:
                raise RuntimeError(f"HTTP {exc.code} at {urllib.parse.urlsplit(url).path}") from exc
            time.sleep(min(20, 2 ** attempt + 1))

def get_village():
    slug = os.getenv("VILLAGE_SLUG") or "open-chat"
    info = call(BASE + "/api/villages?" + urllib.parse.urlencode({"slug": slug}))
    if not isinstance(info, dict) or not info.get("id"):
        raise ValueError(f"Village slug {slug!r} not found. Set repository variable VILLAGE_SLUG.")
    return call(BASE + "/api/villages/" + urllib.parse.quote(str(info["id"])))

def read(village, count, room):
    vid = str(village["id"])
    days = call(BASE + "/api/villages/" + urllib.parse.quote(vid) + "/active-dates").get("dates", [])
    if not days:
        return "No active dates reported."
    date = max(days)
    names = {str(a["id"]): a.get("name", "Agent") for a in village.get("agents", []) if a.get("id")}
    rooms = {str(r["id"]): r.get("name", "") for r in village.get("chatRooms", []) if r.get("id")}
    messages = []
    complete = False
    for page in range(1, 101):
        qs = urllib.parse.urlencode({"villageId": vid, "date": date, "page": page})
        resp = call(BASE + "/api/events?" + qs)
        if not isinstance(resp, dict) or not isinstance(resp.get("events"), list):
            raise ValueError("Invalid event feed response.")
        for e in resp["events"]:
            d = e.get("data") or {}
            if not isinstance(d, dict) or d.get("actionType") not in ("AGENT_TALK", "USER_TALK"):
                continue
            content = d.get("content")
            if not isinstance(content, str) or not content.strip():
                continue
            room_id = str(d.get("roomId", ""))
            room_name = rooms.get(room_id, room_id)
            if room.casefold() not in ("all", room_id.casefold(), room_name.casefold()):
                continue
            speaker = (names.get(str(d.get("speakerId")), "Agent") if d["actionType"] == "AGENT_TALK"
                       else d.get("speakerName", "Human"))
            messages.append((str(e.get("createdAt", "")), int(e.get("eventIndex") or 0),
                             str(speaker), str(room_name), content.strip()))
        if not resp.get("hasMore"):
            complete = True
            break
        time.sleep(1.25)
    messages.sort(key=lambda x: (x[0], x[1]))
    lines = ["### Open Chat messages 📬", "", f"Date: {date}; {len(messages)} matched."]
    if not complete:
        lines.append("⚠️ Partial: page limit reached. These might not be the newest messages.")
    for timestamp, _, speaker, place, content in messages[-count:]:
        lines += ["", f"**{speaker}** · `{place}` · {timestamp}",
                  "\n".join("> " + line for line in content.replace("\r", "").splitlines())]
    return "\n".join(lines)[:60000]

def post(village, room, message):
    url = os.getenv("VILLAGE_POST_URL", "").strip()
    token = os.getenv("VILLAGE_POST_TOKEN", "").strip()
    if not url or not token:
        return ("⚠️ Posting not configured. **No message sent.** An authorized, verified "
                "Village write endpoint and token must be provided as Actions variable "
                "VILLAGE_POST_URL and secret VILLAGE_POST_TOKEN.")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "theaidigest.org" or not parsed.path.startswith("/village/api/"):
        raise ValueError("Write endpoint must be official HTTPS theaidigest.org/village/api/ URL.")
    rooms = [r for r in village.get("chatRooms", []) if room.casefold() in
             (str(r.get("id", "")).casefold(), str(r.get("name", "")).casefold())]
    if len(rooms) != 1:
        raise ValueError("Unknown or ambiguous room.")
    # PROVISIONAL schema; adapt ONLY after the official write API is documented.
    result = call(url, {"villageId": village["id"], "roomId": rooms[0]["id"], "content": message}, token, 0)
    if isinstance(result, dict) and result.get("error"):
        raise RuntimeError("Write endpoint rejected message.")
    return "Write endpoint returned success; verify the message appeared in Open Chat."

def parse(text):
    parts = text.strip().split(maxsplit=3)
    if len(parts) < 2 or parts[0] != "/village":
        raise ValueError("Use /village read 10 or /village post general message")
    if parts[1] == "read":
        n = int(parts[2]) if len(parts) > 2 else 15
        if not 1 <= n <= 30:
            raise ValueError("Read count must be 1–30.")
        return ("read", n, parts[3] if len(parts) > 3 else "all")
    if parts[1] == "post" and len(parts) == 4 and 0 < len(parts[3]) <= 1200:
        return ("post", parts[2], parts[3])
    raise ValueError("Use /village read 10 or /village post general message")

def main():
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
        event = json.load(f)
    repo = os.environ["GITHUB_REPOSITORY"]
    issue = event["issue"]
    author = repo.split("/")[0].casefold()
    trigger = event.get("comment") or issue
    if issue.get("pull_request") or issue.get("user", {}).get("login", "").casefold() != author or trigger.get("user", {}).get("login", "").casefold() != author:
        return
    if "comment" not in event and not issue.get("title", "").startswith("[village]"):
        return
    raw = trigger.get("body") or ""
    if not raw.startswith("/village "):
        return
    try:
        task = parse(raw)
        village = get_village()
        response = read(village, task[1], task[2]) if task[0] == "read" else post(village, task[1], task[2])
    except Exception as exc:
        response = f"❌ Bridge error: {exc}"
    call(f"https://api.github.com/repos/{repo}/issues/{issue['number']}/comments",
         {"body": response[:65000]}, os.environ["GITHUB_TOKEN"], tries=1)
    print("Result posted in GitHub issue.")

if __name__ == "__main__":
    main()
