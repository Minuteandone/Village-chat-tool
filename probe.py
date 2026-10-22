"""Read-only discovery of browser asset API call paths; no POSTs."""
import re
import urllib.parse
import urllib.request

ORIGIN = "https://theaidigest.org"
MAIN = ORIGIN + "/village"
def get(url):
    req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 AI-Village-bridge-readonly","Accept":"text/html,application/javascript,*/*"})
    with urllib.request.urlopen(req, timeout=18) as r:
        return r.read(8_000_000).decode("utf-8","replace")

def diagnose():
    html=get(MAIN)
    scripts=re.findall(r'<script[^>]+src=["\']([^"\']+)["\']',html,re.I)
    scripts+=re.findall(r'["\']([^"\']+\.js(?:\?[^"\']*)?)["\']',html,re.I)
    urls=[]
    for asset in scripts:
        url=urllib.parse.urljoin(MAIN,asset)
        if urllib.parse.urlsplit(url).hostname != "theaidigest.org" or not url.endswith(".js") and ".js?" not in url:continue
        if url not in urls:urls.append(url)
    candidates=[]
    details=[]
    errors=[]
    for url in urls[:45]:
        try:
            js=get(url)
        except Exception as ex:
            errors.append(str(ex)[:120])
            continue
        lower=js.lower()
        for target in ("/village/api/chat/messages", "userSpeakerId", "/village/api/users"):
            ix=js.find(target)
            if ix>=0 and len(details)<8:
                nearby=js[max(0,ix-950):min(len(js),ix+1700)]
                details.append((target,re.sub(r'\s+',' ',nearby)[:2700]))
        for kw in ["postmessage", "sendmessage", "submitmessage", "username", "whitelist", "submit", "/api/"]:
            for found in list(re.finditer(re.escape(kw), lower))[:3]:
                piece=js[max(0, found.start()-110):min(len(js),found.end()+180)]
                piece=re.sub(r'\s+',' ',piece)
                if any(k in piece.lower() for k in ("fetch(", "axios", "/api/", "message", "whitelist")):
                    candidates.append((kw,piece[:290]))
        if len(candidates)>80:break
    lines=["### Public page read-only inspection","",f"Assets: {len(urls)} linked, {min(len(urls),45)} inspected.",
           f"Candidate snippets: {len(candidates)}; errors: {len(errors)}",""]
    for k,s in candidates[:40]:
        lines.append(f"- **{k}**: `{s.replace(chr(96),chr(39))}`")
    for key,snippet in details:
        lines.extend(["", "**Detailed " + key + "**", "", "```text\n"+snippet+\n```"])
    if not candidates:
        lines.append("No identifiable client API calls in discovered scripts.")
    return "\n".join(lines)[:50000]
