"""Inspect public browser code for the documented UI submission flow; never POST."""
import re
import urllib.parse
import urllib.request

SITE="https://theaidigest.org/village"

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; VillageReadOnlyInspector/1.0)"})
    with urllib.request.urlopen(req,timeout=15) as r:
        return r.read(10_000_000).decode("utf-8","replace")

def diagnose():
    html=get(SITE)
    scripts=re.findall(r'<script[^>]+src=["\x27]([^"\x27]+)["\x27]',html,re.I)
    scripts+=re.findall(r'["\x27]([^"\x27]+\.js(?:\?[^"\x27]*)?)["\x27]',html,re.I)
    urls=[]
    for src in scripts:
        url=urllib.parse.urljoin(SITE,src)
        if urllib.parse.urlsplit(url).hostname=="theaidigest.org" and url not in urls:
            urls.append(url)
    needles=[
        "47926:(e,t,n)=>",
        'fetch("/village/api/users"',
        "'/village/api/users'",
        '"/village/api/users"',
        'fetch("/village/api/chat/messages"',
        'fetch("/village/api/users/display-name"',
        "userSpeakerId:",
        "useUser",
        "createUser"
    ]
    results={name:[] for name in needles}
    failures=0
    for url in urls[:65]:
        try:
            js=get(url)
        except Exception:
            failures+=1
            continue
        for name in needles:
            if len(results[name])>=2:
                continue
            pos=js.find(name)
            if pos>=0:
                snippet=js[max(0,pos-300):pos+2300]
                results[name].append(re.sub(r'\s+',' ',snippet)[:2600])
    lines=["### Open Chat client request inspection (read-only)","",
           f"Scripts considered: {min(65,len(urls))}. Failed loads: {failures}.",""]
    for name in needles:
        lines.append(f"#### {name}")
        if not results[name]:
            lines.append("Not found in inspected assets.")
        for s in results[name]:
            lines.extend(["",s,""])
    return "\n".join(lines)[:54000]
