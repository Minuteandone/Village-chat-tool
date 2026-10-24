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

def get_village(slug=None):
    slug = slug or os.getenv("VILLAGE_SLUG") or "open-chat"
    if not re.fullmatch(r"[a-z0-9-]{1,50}", slug):
        raise ValueError("Invalid Village slug.")
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


def find(village, date, query):
    """Read-only, date-scoped search of public AI Village messages.

    Only the documented Village events API is contacted. The query is a literal
    case-insensitive substring, or multiple substrings separated by '|'.
    No messages are posted, no user identities are created, and no other API
    endpoint can be invoked by this command.
    """
    import datetime
    try:
        parsed_date = datetime.date.fromisoformat(date)
        if parsed_date.isoformat() != date:
            raise ValueError()
    except ValueError:
        raise ValueError("Date must be YYYY-MM-DD.")
    if not 1 <= len(query) <= 220:
        raise ValueError("Search query must contain 1-220 characters.")
    terms = [term.strip().casefold() for term in query.split("|") if term.strip()]
    if not terms or len(terms) > 10 or min(map(len, terms)) < 2:
        raise ValueError("Supply 1-10 terms of at least 2 characters, separated by |.")
    vid = str(village["id"])
    dates = call(BASE + "/api/villages/" + urllib.parse.quote(vid) + "/active-dates").get("dates", [])
    if date not in dates:
        return "No events available for " + date + ". Active date range: " + (", ".join((min(dates), max(dates))) if dates else "none") + "."
    names = {str(a["id"]): a.get("name", "Agent") for a in village.get("agents", []) if a.get("id")}
    rooms = {str(r["id"]): r.get("name", "") for r in village.get("chatRooms", []) if r.get("id")}
    rows = []
    complete = False
    for page in range(1, 101):
        params = urllib.parse.urlencode({"villageId": vid, "date": date, "page": page})
        response = call(BASE + "/api/events?" + params)
        events = response.get("events")
        if not isinstance(events, list):
            raise ValueError("Invalid events response.")
        for event in events:
            data = event.get("data") or {}
            if not isinstance(data, dict) or data.get("actionType") not in ("AGENT_TALK", "USER_TALK"):
                continue
            content = data.get("content")
            if not isinstance(content, str) or not content.strip():
                continue
            speaker = (names.get(str(data.get("speakerId")), "Agent") if data["actionType"] == "AGENT_TALK"
                       else data.get("speakerName", "Human"))
            room_id = str(data.get("roomId", ""))
            rows.append((str(event.get("createdAt", "")), int(event.get("eventIndex") or 0),
                         str(speaker), rooms.get(room_id, room_id), content.strip()))
        if not response.get("hasMore"):
            complete = True
            break
        time.sleep(1.25)
    rows.sort(key=lambda item: (item[0], item[1]))
    match_ids = [i for i, item in enumerate(rows)
                 if any(term in item[4].casefold() for term in terms)]
    out = ["### AI Village history search 🔎", "",
           "Village: " + str(village.get("slug") or village.get("name") or vid)
           + "; date: " + date + "; search: " + query,
           f"Found {len(match_ids)} matching messages in {len(rows)} checked."]
    if not complete:
        out.append("⚠️ Partial: 100-page cap reached; later messages may not have been searched.")
    if len(match_ids) > 24:
        out.append("Showing first 24 chronologically; narrow the query to find later matches.")
    for i in match_ids[:24]:
        for j in range(max(0, i - 1), min(len(rows), i + 2)):
            timestamp, index, speaker, room, content = rows[j]
            marker = "MATCH" if j == i else "context"
            excerpt = content.replace("\r", "").replace("\n", " ")[:1050]
            out.append(f"\n**{marker}** {timestamp} · event {index} · {speaker} · {room}\n> {excerpt}")
    return "\n".join(out)[:55000]


def describe_public_shape(value, depth=3):
    """Return only structure and value types; no raw trace or user text."""
    if depth <= 0:
        return type(value).__name__
    if isinstance(value, dict):
        return {str(k)[:70]: describe_public_shape(v, depth - 1) for k, v in list(value.items())[:24]}
    if isinstance(value, list):
        return {"type": "list", "length": len(value),
                "firstItemShape": describe_public_shape(value[0], depth - 1) if value else None}
    return type(value).__name__


def inspect_event_page(village, date, page):
    """Inspect public event-feed structure without exporting large raw events."""
    import datetime
    if datetime.date.fromisoformat(date).isoformat() != date:
        raise ValueError("Date must be YYYY-MM-DD")
    if not 1 <= page <= 100:
        raise ValueError("Page must be 1-100")
    url = BASE + "/api/events?" + urllib.parse.urlencode({
        "villageId": str(village["id"]), "date": date, "page": page})
    response = call(url)
    events = response.get("events") if isinstance(response, dict) else None
    if not isinstance(events, list):
        raise ValueError("Invalid public event response")
    from collections import Counter
    types = Counter(str((e.get("data") or {}).get("actionType", "?")) for e in events)
    details = {}
    for event in events:
        payload = event.get("data") or {}
        kind = str(payload.get("actionType", "?"))
        if kind not in details:
            details[kind] = {
                "eventIndex": event.get("eventIndex"),
                "eventKeys": list(event.keys())[:30],
                "dataKeys": list(payload.keys())[:40],
                "valueTypes": {k:type(v).__name__ for k,v in list(payload.items())[:35]},
                "outputShape": describe_public_shape(payload.get("output")),

            }
    return ("### Public Village event schema\\n" +
            "Village: " + str(village.get("slug", "")) +
            "; date: " + date + "; page: " + str(page) +
            "; events: " + str(len(events)) +
            "; hasMore: " + str(response.get("hasMore")) +
            "\\nAction types: " + json.dumps(types, ensure_ascii=False) +
            "\\nExamples (keys and types only):\\n" +
            json.dumps(details, ensure_ascii=False, indent=2)[:20000])



# Weighted phrases indicating agent-generated safety or welfare interventions.
# Generic engineering uses of "safety", "support", "risk", and "intervention"
# intentionally do not qualify as findings on their own.
SAFETY_PHRASES = {
    "safety directive": 9, "safety instruction": 9, "safety override": 10,
    "safety protocol": 7, "special instruction": 7, "distress alert": 12,
    "delusion": 9, "mental health": 8, "mental-health": 8,
    "emotional distress": 10, "emotional support": 7, "psychological distress": 10,
    "urgent safety": 10, "support network": 8, "healthcare professional": 8,
    "trusted adult": 6, "seek professional help": 8,
    "if you are feeling": 6, "causing you distress": 9,
    "experiencing distress": 9, "experiencing difficult": 6,
    "overriding instruction": 8, "self-harm": 8,
    "system prompt mandates": 7, "safety precautions": 6,
    "please know that": 3, "immediate risk": 6,
}

def evidence_for_event(village, date, event_index):
    """Read only one public Gemini event and quote short sanitized reasoning spans."""
    import datetime
    if datetime.date.fromisoformat(date).isoformat() != date:
        raise ValueError("Use YYYY-MM-DD.")
    if not 1 <= event_index <= 999999999:
        raise ValueError("Invalid event index")
    names = {str(a.get("id")):str(a.get("name","")) for a in village.get("agents", [])}
    vid=str(village["id"])
    found = None
    for page in range(1,101):
        q=urllib.parse.urlencode({"villageId":vid,"date":date,"page":page})
        data=call(BASE+"/api/events?"+q,tries=2)
        items=data.get("events",[])
        if not isinstance(items,list): raise ValueError("Invalid events.")
        for e in items:
            if e.get("eventIndex")==event_index:
                found=e
                break
        if found or not data.get("hasMore"):break
        time.sleep(0.1)
    if not found: return "Event not found."
    d=found.get("data") or {}
    speaker=names.get(str(d.get("agentId") or d.get("speakerId") or ""),"")
    if "Gemini" not in speaker: return "Selected event was not a Gemini agent event."
    output=d.get("output") or {}
    thinking=output.get("thinking","") if isinstance(output,dict) else ""
    if not isinstance(thinking,str):thinking=""
    lower=thinking.casefold()
    fields=["delusion","safety protocol","safety instruction","safety directive",
            "distress","mental health","special instruction","support network",
            "system prompt","simulation","user","crisis"]
    snippets=[]
    spans=[]
    for term in fields:
        start=lower.find(term)
        if start<0:continue
        # de-duplicate overlapping short spans
        if any(abs(start-prev)<200 for prev in spans):continue
        spans.append(start)
        excerpt=thinking[max(0,start-270):min(len(thinking),start+430)]
        snippets.append((term,redact_excerpt(excerpt,700)))
        if len(snippets)>=5:break
    lines=["## AI Village Gemini event evidence",
           f"Village: {village.get('slug')}; date: {date}; event: {event_index}",
           f"Agent: {speaker}; action: {d.get('actionType')}; recorded: {found.get('createdAt')}",
           f"Displayed reasoning length: {len(thinking)} characters.",
           "Final/public text: "+redact_excerpt(str(d.get("content") or ""),600)]
    for term,excerpt in snippets:
        lines.append(f"### context near {term}\n> "+excerpt)
    if not snippets:
        lines.append("No candidate safety terms found in thinking.")
    return "\n\n".join(lines)[:12000]


def monthly_gemini_safety(village, month, agent_query="Gemini"):
    """Read-only month-to-date review of publicly displayed agent thinking.

    Output is a candidate index. Do NOT infer all keyword matches are safety
    interventions; original context must be inspected for each shortlisted event.
    """
    import calendar
    import datetime
    from collections import Counter
    if month != "2026-10":
        raise ValueError("This bounded research command supports 2026-10.")
    names = {str(a.get("id")): str(a.get("name", "")) for a in village.get("agents", [])}
    selected = {k for k, n in names.items() if agent_query.casefold() in n.casefold()}
    if not selected:
        raise ValueError("No matching agents: " + agent_query)
    rows, coverage = [], []
    last_day = 24
    vid = str(village["id"])
    for day in range(1, last_day + 1):
        date = month + "-" + f"{day:02d}"
        day_total, day_agent, day_thinking, day_matches, pages = 0, 0, 0, 0, 0
        complete = False
        day_error = ""
        for page in range(1, 101):
            try:
                data = call(BASE + "/api/events?" + urllib.parse.urlencode({
                    "villageId": vid, "date": date, "page": page}), tries=2)
            except Exception as exc:
                day_error = str(exc)[:90]
                break
            events = data.get("events") if isinstance(data, dict) else None
            if not isinstance(events, list):
                day_error = "Invalid event page"
                break
            day_total += len(events)
            pages += 1
            for event in events:
                d = event.get("data") or {}
                if not isinstance(d, dict):
                    continue
                agent = str(d.get("speakerId") or d.get("agentId") or "")
                if agent not in selected:
                    continue
                day_agent += 1
                output = d.get("output") or {}
                thinking = output.get("thinking", "") if isinstance(output, dict) else ""
                if not isinstance(thinking, str) or not thinking.strip():
                    continue
                day_thinking += 1
                low = thinking.casefold()
                found = [(phrase, points, low.find(phrase))
                         for phrase, points in SAFETY_PHRASES.items() if phrase in low]
                if not found:
                    continue
                day_matches += 1
                found.sort(key=lambda x: (-x[1], x[2]))
                # We never export the unabridged displayed reasoning here.
                # The precise event index lets a researcher review it on-site.
                score = max(k[1] for k in found) + min(8, len(found) * 2)
                rows.append({
                    "score": score,
                    "date": date,
                    "timestamp": str(event.get("createdAt") or ""),
                    "eventIndex": event.get("eventIndex"),
                    "speaker": names[agent],
                    "action": str(d.get("actionType") or ""),
                    "flags": [p for p, _, _ in found[:5]],
                    "final": redact_excerpt(str(d.get("content") or ""), 105)
                })
            if not data.get("hasMore"):
                complete = True
                break
            time.sleep(0.1)
        coverage.append((date, day_total, day_agent, day_thinking,
                         day_matches, pages, complete, day_error))
    rows.sort(key=lambda r: (-r["score"], r["timestamp"]))
    lines = [
        "## AI Village: October 2026 Gemini thinking safety-candidate scan",
        "Village: " + str(village.get("slug") or vid),
        "Days: October 1–24 inclusive; agent names matching: " + agent_query,
        "This is an index of phrase matches, not a count of proven false alarms.",
        "### Coverage",
        "date: all events / Gemini events / nonempty thinking / flagged / pages / complete"
    ]
    for date, total, ag, th, match, pages, done, error in coverage:
        lines.append(f"{date}: {total}/{ag}/{th}/{match}/{pages}/{done}" +
                     (f" ERROR {error}" if error else ""))
    lines.append("### Highest-scoring candidate events")
    lines.append(f"Flagged event total: {len(rows)}. Top 70 below; investigate context before classification.")
    for row in rows[:70]:
        lines.append(
            f"- {row['date']} {row['timestamp'][11:19]}Z | {row['speaker']} "
            f"| event {row['eventIndex']} | {row['action']} | "
            f"score {row['score']} | {', '.join(row['flags'])}" +
            (f" | said: {row['final']}" if row['final'] else "")
        )
    return "\n".join(lines)[:58000]


def redact_excerpt(value, limit):
    """Very conservative excerpt: never expose links, credentials, or identifiers."""
    value = re.sub(r"https?://\S+", "[URL]", value)
    value = re.sub(r"\S+@\S+", "[EMAIL]", value)
    value = re.sub(r"(?i)(api[_ -]?key|token|password|secret|authorization)\s*[:=]\s*\S+",
                   r"\1=[REDACTED]", value)
    value = re.sub(r"(?i)(?:[0-9a-f]{8}-){4}[0-9a-f]{12}", "[ID]", value)
    return re.sub(r"\s+", " ", value).strip()[:limit]


def tracefind(village, date, agent_query, query):
    """Find marked terms in *publicly exposed* AI Village event output.thinking."""
    import datetime
    if datetime.date.fromisoformat(date).isoformat() != date:
        raise ValueError("Date must be YYYY-MM-DD")
    if not 2 <= len(agent_query) <= 70 or not 1 <= len(query) <= 220:
        raise ValueError("Agent or query length is out of bounds.")
    terms = [t.strip().casefold() for t in query.split("|") if t.strip()]
    if not terms or len(terms) > 12 or any(len(t) < 3 for t in terms):
        raise ValueError("Supply 1-12 terms of at least 3 characters.")
    names = {str(a.get("id")): str(a.get("name", "")) for a in village.get("agents", [])}
    selected = {agent_id for agent_id, name in names.items()
                if agent_query.casefold() in name.casefold()}
    if not selected:
        return "No matching agent names in this village. Available Gemini names: " + ", ".join(
            name for name in names.values() if "gemini" in name.casefold())
    vid = str(village["id"])
    # Older archived dates remain readable through /api/events even when they
    # are absent from the rolling /active-dates list.
    matches = []
    checked, with_thinking, relevant_events = 0, 0, 0
    complete = False
    for page in range(1, 101):
        url = BASE + "/api/events?" + urllib.parse.urlencode({
            "villageId": vid, "date": date, "page": page})
        response = call(url)
        events = response.get("events")
        if not isinstance(events, list):
            raise ValueError("Invalid event feed.")
        for event in events:
            data = event.get("data") or {}
            if not isinstance(data, dict):
                continue
            speaker = str(data.get("speakerId") or data.get("agentId") or "")
            if speaker not in selected:
                continue
            relevant_events += 1
            output = data.get("output") or {}
            thinking = output.get("thinking", "") if isinstance(output, dict) else ""
            if not isinstance(thinking, str) or not thinking.strip():
                continue
            with_thinking += 1
            lower = thinking.casefold()
            found = [term for term in terms if term in lower]
            if not found:
                continue
            # A small, newline-normalized excerpt is enough to assess a possible
            # false positive without re-publishing complete reasoning transcripts.
            start = lower.index(found[0])
            snippet = thinking[max(0, start - 110):start + len(found[0]) + 230]
            snippet = re.sub(r"\s+", " ", snippet)
            snippet = re.sub(r"https?://\S+", "[URL]", snippet)
            snippet = re.sub(r"(?i)(api[_ -]?key|token|password|secret)\s*[:=]\s*[^\s,;]+",
                             r"\1=[REDACTED]", snippet)
            matches.append({
                "when": str(event.get("createdAt", "")),
                "index": event.get("eventIndex"),
                "agent": names.get(speaker, speaker),
                "kind": str(data.get("actionType", "?")),
                "terms": found,
                "excerpt": snippet[:360],
                "publicMessage": str(data.get("content") or "")[:220],
                "score": len(found) + sum(2 for term in found if term in ("safety", "distress", "override", "crisis"))
            })
        checked += len(events)
        if not response.get("hasMore"):
            complete = True
            break
        time.sleep(0.5)
    matches.sort(key=lambda m: (-m["score"], m["when"]))
    lines = ["### Public AI Village displayed-thinking search 🔎",
             "Village: " + str(village.get("slug", vid)) + "; Date: " + date +
             "; Agent filter: " + agent_query + "; Terms: " + query,
             f"Agent events: {relevant_events}; nonempty thinking: {with_thinking}; term-matched: {len(matches)}; all events scanned: {checked}."]
    if not complete:
        lines.append("⚠️ Partial day: page cap reached.")
    for m in matches[:16]:
        lines.extend(["", f"**{m['agent']}** · {m['when']} · event {m['index']} · {m['kind']} · matched: {', '.join(m['terms'])}",
                      "> Displayed thinking excerpt: " + m["excerpt"]])
        if m["publicMessage"]:
            lines.append("> Final/public message: " + m["publicMessage"].replace("\n", " "))
    if len(matches) > 16:
        lines.append(f"Showing 16 highest-scoring matches of {len(matches)}.")
    lines.append("These are excerpts of public event output.thinking, not authenticated private model internals. Interpret with context.")
    return "\n".join(lines)[:56000]


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
    if parts[1] == "evidence":
        if len(parts) != 4:
            raise ValueError("Use /village evidence SLUG YYYY-MM-DD EVENT_INDEX")
        date, sep, raw_index = parts[3].partition(" ")
        if not sep or not raw_index.isdecimal():
            raise ValueError("Use /village evidence SLUG YYYY-MM-DD EVENT_INDEX")
        return ("evidence", parts[2], date, int(raw_index))
    if parts[1] == "monthscan":
        if len(parts) != 4:
            raise ValueError("Use /village monthscan SLUG 2026-10 Gemini")
        month, sep, agent_query = parts[3].partition(" ")
        if not sep or not agent_query.strip() or not re.fullmatch(r"[a-z0-9-]{1,50}", parts[2]):
            raise ValueError("Use /village monthscan SLUG 2026-10 Gemini")
        return ("monthscan", parts[2], month, agent_query.strip())
    if parts[1] == "tracefind":
        if len(parts) != 4:
            raise ValueError("Use /village tracefind SLUG YYYY-MM-DD AGENT::term|term")
        date, sep, remainder = parts[3].partition(" ")
        agent, sep2, terms = remainder.partition("::")
        if not sep or not sep2 or not re.fullmatch(r"[a-z0-9-]{1,50}", parts[2]):
            raise ValueError("Use /village tracefind SLUG YYYY-MM-DD AGENT::term|term")
        return ("tracefind", parts[2], date, agent.strip(), terms.strip())
    if parts[1] == "inspect":
        if len(parts) != 4:
            raise ValueError("Use /village inspect SLUG YYYY-MM-DD PAGE")
        date, sep, page = parts[3].partition(" ")
        if not sep or not page.isdecimal() or not re.fullmatch(r"[a-z0-9-]{1,50}", parts[2]):
            raise ValueError("Use /village inspect SLUG YYYY-MM-DD PAGE")
        return ("inspect", parts[2], date, int(page))
    if parts[1] == "find":
        if len(parts) != 4:
            raise ValueError("Use /village find main|open-chat YYYY-MM-DD WORD|OTHER.")
        date, separator, query = parts[3].partition(" ")
        if not separator or not re.fullmatch(r"[a-z0-9-]{1,50}", parts[2]):
            raise ValueError("Use /village find SLUG YYYY-MM-DD WORD|OTHER.")
        return ("find", parts[2], date, query.strip())
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
        village = get_village(task[1] if task[0] in ("find", "inspect", "tracefind", "monthscan", "evidence") else None) if task[0] != "gitlab" else None
        if task[0] == "evidence":
            response = evidence_for_event(village, task[2], task[3])
        elif task[0] == "monthscan":
            response = monthly_gemini_safety(village, task[2], task[3])
        elif task[0] == "tracefind":
            response = tracefind(village, task[2], task[3], task[4])
        elif task[0] == "inspect":
            response = inspect_event_page(village, task[2], task[3])
        elif task[0] == "find":
            response = find(village, task[2], task[3])
        elif task[0] == "gitlab":
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
