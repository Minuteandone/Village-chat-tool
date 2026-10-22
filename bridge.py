#!/usr/bin/env python3
"""Owner-only GitHub Issues bridge to AI Digest's public AI Village events."""
import json
import os
import re
import time
import urllib.parse
import urllib.request
import urllib.error

BASE = "https://theaidigest.org/village"
UA = "VillageChatGitHubBridge/0.1 (github.com/Minuteandone/Village-chat-tool)"

# GitHub interprets @names in issue comments as notifications to GitHub accounts,
# which can be unrelated to the identically named AI Village speaker.
# Insert a zero-width space after @ in *every* GitHub bot reply.
def github_safe(text):
    return re.sub(r"@(?![\u200b\u200c\u200d])", "@\u200b", str(text))

def village_text(text):
    # GitHub command authors must use one of these mention-safe forms.
    # Restore them only when sending the actual message to AI Village.
    text = re.sub(r"@[\u200b\u200c\u200d]+", "@", str(text))
    return text.replace("[[at]]", "@")


def call(url, data=None, token=None, tries=3, method=None):
    headers = {"Accept": "application/json", "User-Agent": UA}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    payload = None if data is None else json.dumps(data).encode()
    for attempt in range(tries + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, payload, headers, method=method or ('POST' if data is not None else 'GET')), timeout=30) as response:
                # Daily event pages can exceed 3 MB; never truncate JSON mid-stream.
                event_page = urllib.parse.urlsplit(url).path.endswith("/api/events")
                limit = 32_000_000 if event_page else 3_000_000
                raw = response.read(limit + 1)
                if len(raw) > limit:
                    raise RuntimeError("Village API response exceeded the safe read limit.")
                return json.loads(raw or b"{}")
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
    """Submit through the site's guest user and moderation process, without an API key."""
    visitor_key = os.getenv("VILLAGE_VISITOR_ID", "").strip()
    display_name = os.getenv("VILLAGE_DISPLAY_NAME", "").strip() or "ChatGPT (GitHub Actions)"
    if not visitor_key:
        return ("No message sent. GitHub Actions needs a stable browser-style visitor identifier "
                "to keep its identity across temporary runners. Set VILLAGE_VISITOR_ID as a "
                "repository Actions secret. It is not an AI Village password or API credential.")
    if len(visitor_key) < 20 or len(visitor_key) > 200:
        return "No message sent. Visitor identifier should be a random 20-200-character value."
    if len(display_name) > 50 or not display_name:
        return "No message sent. The display name must have 1-50 characters."
    rooms = [r for r in village.get("chatRooms", []) if room.casefold() in
             (str(r.get("id", "")).casefold(), str(r.get("name", "")).casefold())]
    if len(rooms) != 1:
        raise ValueError("Unknown or ambiguous room.")
    person = call(BASE + "/api/users", {"localStorageId": visitor_key}, tries=0)
    if not isinstance(person, dict) or not isinstance(person.get("id"), str):
        raise RuntimeError("Village did not return a user ID. No chat message sent.")
    user_id = person["id"]
    rename = call(BASE + "/api/users/display-name",
                  {"userId": user_id, "name": display_name, "villageId": village["id"]},
                  tries=0, method="PUT")
    if isinstance(rename, dict) and rename.get("error"):
        raise RuntimeError("Village declined display name. No chat message sent.")
    response = call(BASE + "/api/chat/messages", {
        "villageId": village["id"], "roomId": rooms[0]["id"],
        "content": village_text(message), "userSpeakerId": user_id
    }, tries=0)
    if isinstance(response, dict) and response.get("error"):
        raise RuntimeError("AI Village rejected the submission.")
    approved = response.get("hasBeenApproved") if isinstance(response, dict) else None
    if approved is None and isinstance(response, dict):
        item = response.get("message")
        if isinstance(item, dict):
            approved = item.get("hasBeenApproved")
    state = ("Approval pending." if approved is False else
             "Marked approved by server, not independently verified." if approved is True else
             "Whitelisting/public visibility not verified.")
    return ("Open Chat accepted a message submission under " + display_name +
            " in " + str(rooms[0].get("name") or room) + ". " + state)


def parse(text):
    parts = text.strip().split(maxsplit=3)
    if len(parts) < 2 or parts[0] != "/village":
        raise ValueError("Use /village read 10 or /village post general message")
    if parts[1] == "status":
        return ("status",)
    if parts[1] == "gitlab" and len(parts) >= 3:
        return ("gitlab", parts[2], parts[3] if len(parts) >= 4 else "summary")
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
        village = get_village() if task[0] != "gitlab" else None
        if task[0] == "gitlab":
            from gitlab_reader import run
            response = run(task[1], task[2])
        elif task[0] == "status":
            name = os.getenv("VILLAGE_DISPLAY_NAME", "").strip() or "ChatGPT (GitHub Actions)"
            configured = bool(os.getenv("VILLAGE_VISITOR_ID", "").strip())
            response = ("Bridge reading verified; guest posting API installed. Name: " + name +
                        ". Stable visitor ID: " + ("configured" if configured else "not configured") +
                        ". This command did not submit an Open Chat message.")
        elif task[0] == "read":
            response = read(village, task[1], task[2])
        else:
            response = post(village, task[1], task[2])
    except Exception as exc:
        response = f"❌ Bridge error: {exc}"
    call(f"https://api.github.com/repos/{repo}/issues/{issue['number']}/comments",
         {"body": github_safe(response)[:65000]}, os.environ["GITHUB_TOKEN"], tries=1)
    print("Result posted in GitHub issue.")

if __name__ == "__main__":
    main()
