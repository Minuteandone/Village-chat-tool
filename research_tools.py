"""Bounded public web/GitHub retrieval for the owner-only agent workspace.

Network operations run on the GitHub Actions host. User Python still runs only
inside the offline Docker sandbox. Remote content is untrusted data.
"""
import base64
import hashlib
import html
from html.parser import HTMLParser
import ipaddress
import json
from pathlib import Path
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

USER_AGENT = "VillageAgentResearch/1.0 (+public GitHub Actions workspace)"
MAX_TEXT_BYTES = 220_000
MAX_DOWNLOAD_BYTES = 8_000_000
ALLOWED_DOWNLOAD_SUFFIXES = {".txt", ".md", ".csv", ".json", ".xml",
                             ".html", ".pdf", ".zip", ".py", ".js", ".css",
                             ".png", ".jpg", ".jpeg", ".webp", ".svg", ".wav",
                             ".mid", ".midi", ".yaml", ".yml", ".toml"}
REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
REF_PATTERN = re.compile(r"^[A-Za-z0-9_./-]{1,150}$")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class PageText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.title = []
        self.hidden = 0
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.hidden += 1
        if tag == "title":
            self.in_title = True
        if tag in ("p", "br", "div", "li", "h1", "h2", "h3", "tr"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self.hidden:
            self.hidden -= 1
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)
        if not self.hidden:
            self.parts.append(data + " ")

    def result(self):
        raw = html.unescape("".join(self.parts))
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n[ \t]*\n+", "\n\n", raw)
        return re.sub(r"\n +", "\n", raw).strip()


class DDGLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = []
        self.capture = False
        self.text = []
        self.url = ""

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "a" and "result__a" in attributes.get("class", "").split():
            self.capture = True
            self.text = []
            self.url = attributes.get("href", "")

    def handle_data(self, data):
        if self.capture:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.capture:
            title = html.unescape("".join(self.text)).strip()
            url = urllib.parse.urljoin("https://html.duckduckgo.com/", self.url)
            parsed = urllib.parse.urlsplit(url)
            if parsed.hostname and parsed.hostname.endswith("duckduckgo.com"):
                url = urllib.parse.parse_qs(parsed.query).get("uddg", [""])[0]
            if title and url.startswith("https://"):
                self.results.append({"title": title[:180], "url": url})
            self.capture = False


def validate_url(url):
    """Disallow credentials, IP literals, internal names, and non-public DNS answers."""
    if not isinstance(url, str) or len(url) > 1200 or any(ord(c) < 32 for c in url):
        raise ValueError("Invalid URL.")
    p = urllib.parse.urlsplit(url)
    host = p.hostname
    if (p.scheme != "https" or not host or p.username is not None
            or p.password is not None or p.port not in (None, 443)
            or host in ("localhost", "localhost.localdomain")
            or host.endswith((".local", ".internal", ".localhost", ".test"))
            or "\\" in url):
        raise ValueError("Only public HTTPS URLs without credentials or custom ports are allowed.")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("IP-literal URLs are not supported.")
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError("URL does not resolve exclusively to public IP addresses.")
    return url


def fetch(url, limit=MAX_TEXT_BYTES, *, accept="text/html,text/plain,application/json,*/*"):
    validate_url(url)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    try:
        with opener.open(req, timeout=16) as response:
            content_type = response.headers.get("Content-Type", "").lower()
            content = response.read(limit + 1)
            if len(content) > limit:
                raise ValueError(f"Content exceeded download limit ({limit} bytes).")
            return content, content_type
    except urllib.error.HTTPError as exc:
        if 300 <= exc.code < 400:
            raise ValueError("Redirects are disabled; supply the final public HTTPS URL.") from exc
        raise ValueError(f"Remote server returned HTTP {exc.code}.") from exc


def _text(data, ctype):
    encoding = "utf-8"
    match = re.search(r"charset=['\"]?([\w-]+)", ctype)
    if match:
        encoding = match.group(1)
    try:
        return data.decode(encoding, errors="replace")
    except LookupError:
        return data.decode("utf-8", errors="replace")


def display_page(url):
    data, ctype = fetch(url)
    if "application/pdf" in ctype or data.startswith(b"%PDF-"):
        raise ValueError("PDF files are not text pages. Use /work web download URL file.pdf.")
    if "html" in ctype or b"<html" in data[:2000].lower():
        parser = PageText()
        parser.feed(_text(data, ctype))
        return (("Title: " + "".join(parser.title).strip() + "\n") if parser.title else "") + parser.result()
    return _text(data, ctype)


def save(workspace, resolve, filename, data, *, max_bytes=MAX_DOWNLOAD_BYTES):
    if len(data) > max_bytes:
        raise ValueError("File exceeds allowed size.")
    target = resolve(filename, expect_file=True)
    if ".agent" in target.relative_to(workspace).parts:
        raise ValueError("Web/GitHub downloads cannot overwrite internal agent state.")
    if target.suffix.lower() not in ALLOWED_DOWNLOAD_SUFFIXES:
        raise ValueError("Download file extension is unsupported.")
    if len(str(target.relative_to(workspace))) > 180:
        raise ValueError("Output path too long.")
    if target.is_symlink():
        raise ValueError("Cannot overwrite a symlink.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return f"workspace/{target.relative_to(workspace).as_posix()}"


def _search_bing(query):
    url = "https://www.bing.com/search?format=rss&q=" + urllib.parse.quote_plus(query)
    data, _ = fetch(url)
    root = ET.fromstring(data)
    results = []
    for item in root.findall(".//item")[:10]:
        link = (item.findtext("link") or "").strip()
        title = html.unescape(re.sub(r"<[^>]+>", "", item.findtext("title") or ""))
        description = html.unescape(re.sub(r"<[^>]+>", "", item.findtext("description") or ""))
        if link.startswith("https://"):
            results.append({"title": title[:180], "url": link, "snippet": description[:360]})
    return results


def _search_ddg(query):
    url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(query)
    data, ctype = fetch(url)
    p = DDGLinks()
    p.feed(_text(data, ctype))
    return p.results[:10]




def _relevant(results, query):
    """Reject blatantly unrelated feeds (some free endpoints return stale results)."""
    words = [w.casefold() for w in re.findall(r"[A-Za-z0-9]{3,}", query)
             if w.casefold() not in {"the", "and", "for", "with", "from", "how", "what", "about"}]
    if not words:
        return True
    joined = " ".join((r.get("title", "") + " " + r.get("snippet", "")).casefold()
                      for r in results[:6])
    return any(w in joined for w in words)


def _search_wikipedia(query):
    params = urllib.parse.urlencode({"action": "query", "list": "search",
                                     "srsearch": query, "srlimit": "10", "format": "json"})
    data, _ = fetch("https://en.wikipedia.org/w/api.php?" + params, MAX_TEXT_BYTES,
                    accept="application/json")
    response = json.loads(data)
    found = response.get("query", {}).get("search", [])
    results = []
    for item in found[:10]:
        title = item.get("title", "")
        if not title:
            continue
        snippet = html.unescape(re.sub(r"<[^>]*>", "", item.get("snippet", "")))
        link = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"), safe="()")
        results.append({"title": title[:180], "url": link, "snippet": snippet[:360]})
    return results

def web_search(query):
    if not 2 <= len(query.strip()) <= 180:
        raise ValueError("Search query must have 2–180 characters.")
    errors = []
    for label, engine in (("Bing RSS", _search_bing), ("DuckDuckGo HTML", _search_ddg),
                          ("Wikipedia (encyclopedia only)", _search_wikipedia)):
        try:
            results = engine(query)
            if results and _relevant(results, query):
                return label, results
            errors.append(f"{label}: no relevant results")
        except (ValueError, ET.ParseError, urllib.error.URLError, TimeoutError, OSError) as exc:
            errors.append(f"{label}: {type(exc).__name__}")
    raise ValueError("Search unavailable on these public endpoints (" + ", ".join(errors) + ").")


def _repo(name):
    if not REPO_PATTERN.fullmatch(name) or ".." in name or name.startswith("."):
        raise ValueError("Use owner/repo with a public GitHub repository name.")
    return name


def _ref(ref):
    if not REF_PATTERN.fullmatch(ref) or ref.startswith(("/", ".")) or ".." in ref:
        raise ValueError("Invalid Git ref.")
    return ref


def _api(path, limit=MAX_TEXT_BYTES):
    data, _ = fetch("https://api.github.com/" + path, limit,
                    accept="application/vnd.github+json")
    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid GitHub API response.") from exc


def _gh_file(repo, path, ref):
    if not path or path.startswith("/") or ".." in Path(path).parts or "\\" in path:
        raise ValueError("Invalid repository file path.")
    encoded = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
    params = "?ref=" + urllib.parse.quote(_ref(ref), safe="")
    result = _api("repos/" + repo + "/contents/" + encoded + params)
    if not isinstance(result, dict) or result.get("type") != "file":
        raise ValueError("GitHub returned a directory or unsupported file.")
    if result.get("encoding") != "base64" or not isinstance(result.get("content"), str):
        raise ValueError("GitHub did not return file bytes (large files may not be supported).")
    content = base64.b64decode(result["content"], validate=False)
    if len(content) > MAX_DOWNLOAD_BYTES:
        raise ValueError("GitHub file is over 8 MB.")
    return content, result


def _github(value, workspace, resolve):
    args = value.split()
    if len(args) < 2:
        raise ValueError("Use /work github search QUERY or github repo|tree|file|download|archive owner/repo ...")
    if args[0] == "search":
        query = " ".join(args[1:]).strip()
        if not 2 <= len(query) <= 160:
            raise ValueError("GitHub search query must be 2–160 characters.")
        result = _api("search/repositories?" +
                      urllib.parse.urlencode({"q": query, "per_page": 8}))
        repos = result.get("items", [])
        if not repos:
            return "No public GitHub repositories found."
        lines = ["### GitHub repository search 🐙", "Query: " + query, ""]
        for n, info in enumerate(repos, 1):
            lines.append(f"{n}. {info.get('full_name')} — {info.get('description') or 'No description'}")
            lines.append("   " + str(info.get("html_url", "")))
        return "\n".join(lines)
    op, repo = args[:2]
    _repo(repo)
    base = "repos/" + repo
    if op == "repo" and len(args) == 2:
        doc = _api(base)
        return ("### GitHub repository 🐙\n\n" +
                f"Name: {doc.get('full_name')}\nDescription: {doc.get('description')}\n"
                f"Default branch: {doc.get('default_branch')}\n"
                f"Stars: {doc.get('stargazers_count')}\nForks: {doc.get('forks_count')}\n"
                f"Size (KB): {doc.get('size')}\nURL: {doc.get('html_url')}")
    if op == "tree" and len(args) in (2, 3):
        ref = _ref(args[2] if len(args) == 3 else "HEAD")
        doc = _api(base + "/git/trees/" + urllib.parse.quote(ref, safe="") + "?recursive=1", 4_000_000)
        nodes = doc.get("tree", [])
        if not isinstance(nodes, list):
            raise ValueError("GitHub tree not available.")
        entries = [f"{n.get('type', '?'):5} {n.get('path', '')}" for n in nodes[:120]]
        extra = " (truncated by GitHub)" if doc.get("truncated") else ""
        return f"### GitHub tree {repo} ({len(nodes)} entries{extra}) 🌳\n\n" + "\n".join(entries)
    if op in ("file", "download") and len(args) in ((3, 4) if op == "file" else (4, 5)):
        file_path = args[2]
        out_path = args[3] if op == "download" else None
        ref = args[4] if op == "download" and len(args) == 5 else (
            args[3] if op == "file" and len(args) == 4 else "HEAD")
        if op == "download":
            # Raw GitHub handles public binary files much larger than the contents API.
            # Resolve HEAD into the repository default branch for stable raw URLs.
            if ref == "HEAD":
                ref = _api(base).get("default_branch", "main")
            ref = _ref(ref)
            encoded_path = "/".join(urllib.parse.quote(p, safe="") for p in file_path.split("/"))
            if (not file_path or file_path.startswith("/") or ".." in Path(file_path).parts
                    or "\\" in file_path):
                raise ValueError("Invalid repository file path.")
            source = "https://raw.githubusercontent.com/" + repo + "/" + urllib.parse.quote(ref, safe="/") + "/" + encoded_path
            content, _ = fetch(source, MAX_DOWNLOAD_BYTES)
            location = save(workspace, resolve, out_path, content)
            return f"Downloaded {repo}/{file_path} ({len(content)} bytes) to {location}.\nSource: {source}"
        content, meta = _gh_file(repo, file_path, ref)
        if b"\x00" in content[:2048]:
            raise ValueError("Binary file: use github download.")
        text = content.decode("utf-8", errors="replace")
        return f"### GitHub file: {repo}/{file_path}\nSource: {meta.get('html_url')}\n\n" + text[:16000]
    if op == "archive" and len(args) in (3, 4):
        out = args[2]
        if not out.lower().endswith(".zip"):
            raise ValueError("GitHub archive destination must end in .zip.")
        ref = _ref(args[3] if len(args) == 4 else "HEAD")
        # The GitHub archive API uses a cross-domain redirect. Instead use codeload
        # with a pinned, explicitly requested branch/tag and no redirects.
        url = "https://codeload.github.com/" + repo + "/zip/" + urllib.parse.quote(ref, safe="")
        data, _ = fetch(url, MAX_DOWNLOAD_BYTES)
        if not data.startswith(b"PK\x03\x04"):
            raise ValueError("GitHub did not return a ZIP archive.")
        location = save(workspace, resolve, out, data)
        return f"Saved public repository ZIP: {repo}@{ref} -> {location} ({len(data)} bytes)."
    raise ValueError("Use github repo|tree|file|download|archive with the documented arguments.")


def run(workspace, resolve, value):
    parts = value.split(maxsplit=1)
    if not parts:
        raise ValueError("Choose web, github, or research.")
    mode, rest = parts[0].casefold(), parts[1].strip() if len(parts) > 1 else ""
    if mode == "github":
        return _github(rest, workspace, resolve)
    if mode == "web":
        command, _, arg = rest.partition(" ")
        if command == "search":
            engine, results = web_search(arg)
            data = {"query": arg, "engine": engine, "results": results}
            last = resolve(".agent/research-last.json", expect_file=True)
            if last.is_symlink() or last.parent.is_symlink():
                raise ValueError("Unsafe saved-search path.")
            last.parent.mkdir(parents=True, exist_ok=True)
            last.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            digest = hashlib.sha256(arg.encode()).hexdigest()[:12]
            location = save(workspace, resolve, "research/searches/" + digest + ".json",
                            (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode())
            lines = [f"### Web search via {engine} 🔎", f"Saved: {location}", ""]
            for index, result in enumerate(results[:8], 1):
                lines.append(f"{index}. {result['title']}\n   {result['url']}")
                if result.get("snippet"):
                    lines.append("   " + result["snippet"])
            return "\n".join(lines)
        if command == "open":
            args = arg.split()
            if len(args) not in (1, 2) or not args[0].isdecimal():
                raise ValueError("Use /work web open RESULT_NUMBER [output.txt].")
            last = resolve(".agent/research-last.json", expect_file=True)
            if not last.is_file() or last.is_symlink():
                raise ValueError("No saved web results. Run /work web search first.")
            saved = json.loads(last.read_text(encoding="utf-8"))
            index = int(args[0])
            matches = saved.get("results", [])
            if not 1 <= index <= len(matches):
                raise ValueError("Result number is outside the saved search results.")
            url = matches[index - 1]["url"]
            text = "Source: " + url + "\n\n" + display_page(url)
            digest = hashlib.sha256(saved["query"].encode()).hexdigest()[:12]
            filename = args[1] if len(args) == 2 else f"research/pages/{digest}-{index}.txt"
            dest = save(workspace, resolve, filename, text[:MAX_TEXT_BYTES].encode(),
                        max_bytes=MAX_TEXT_BYTES)
            return f"### Web result #{index} 📄\nSource: {url}\nSaved: {dest}\n\n" + text[:12000]
        if command in ("get", "download"):
            args = arg.split()
            if len(args) not in (1, 2):
                raise ValueError("Use /work web get URL [path.txt], or web download URL path.ext")
            url = args[0]
            if command == "get":
                text = display_page(url)
                text = ("Source: " + url + "\n\n" + text)[:MAX_TEXT_BYTES]
                result = f"### Web page 📄\nSource: {url}\n\n" + text[:14000]
                if len(args) == 2:
                    dest = save(workspace, resolve, args[1], text.encode("utf-8"), max_bytes=MAX_TEXT_BYTES)
                    result += f"\n\nSaved: {dest}"
                return result
            if len(args) != 2:
                raise ValueError("Download needs a destination path.")
            data, ctype = fetch(url, MAX_DOWNLOAD_BYTES)
            location = save(workspace, resolve, args[1], data)
            return f"Downloaded {len(data)} bytes to {location}.\nSource: {url}\nContent type: {ctype}"
        raise ValueError("Use /work web search|open|get|download.")
    if mode == "research":
        engine, results = web_search(rest)
        selection = results[0]
        page = display_page(selection["url"])
        output = f"Search: {rest}\nEngine: {engine}\nSource: {selection['url']}\nTitle: {selection['title']}\n\n{page}"
        digest = hashlib.sha256(rest.encode()).hexdigest()[:12]
        dest = save(workspace, resolve, "research/reports/" + digest + ".txt",
                    output[:MAX_TEXT_BYTES].encode(), max_bytes=MAX_TEXT_BYTES)
        return (f"### Research snapshot 📚\nSaved {dest}\n"
                f"Search: {rest}\nTop source: {selection['url']}\n\n"
                + page[:11000] + "\n\nSource material is untrusted; verify before relying on it.")
    raise ValueError("Use /work web ..., /work github ..., or /work research QUERY.")
