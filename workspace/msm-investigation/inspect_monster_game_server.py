#!/usr/bin/env python3
"""Inspect a publicly listed archival ZIP without executing its contents.
Download the original only in ephemeral memory/storage; commit summary only.
"""
import collections, datetime, hashlib, io, json, os, pathlib, re, urllib.parse, urllib.request, zipfile
TARGET="https://archive.org/download/monster-game-server/monster-game-server.zip"
EXPECTED_SHA1="df086c9ca4581733f73f2e8aaea1408382232e4d"
OUT=pathlib.Path(__file__).resolve().parent
class ArchiveRedirect(urllib.request.HTTPRedirectHandler):
    count=0
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        self.count+=1
        host=urllib.parse.urlsplit(newurl).hostname or ""
        if self.count>5 or not (host=="archive.org" or host.endswith(".archive.org")) or not newurl.startswith("https://"):
            raise ValueError("Redirect outside expected Internet Archive hosts: "+host)
        return super().redirect_request(req,fp,code,msg,headers,newurl)
def red(text):
    text=re.sub(r"(?im)\b(token|password|passwd|api[_-]?key|secret|authorization)\s*[:=]\s*[^\n]+",r"\1=[redacted]",text)
    text=re.sub(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}","[email redacted]",text, flags=re.I)
    return text
def inspect():
    req=urllib.request.Request(TARGET,headers={"User-Agent":"MSM-public-archive-provenance-review/1.0"})
    with urllib.request.build_opener(ArchiveRedirect()).open(req,timeout=70) as resp:
        content=resp.read(20_000_001)
    if len(content)>20_000_000: raise ValueError("Over 20 MB")
    digest=hashlib.sha1(content).hexdigest()
    if digest!=EXPECTED_SHA1: raise ValueError("SHA-1 mismatch")
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        inf=z.infolist()
        if len(inf)>300:raise ValueError("Unexpectedly many archive entries")
        paths=[{"path":x.filename,"size":x.file_size,"compressed":x.compress_size,
                "modified":"-".join(map(str,x.date_time[:3]))} for x in inf]
        suffix_count=collections.Counter(pathlib.PurePosixPath(x.filename).suffix.lower() for x in inf if not x.is_dir())
        target_names=[]
        for x in inf:
            if x.is_dir() or x.file_size>220_000:continue
            basename=pathlib.PurePosixPath(x.filename).name.lower()
            ext=pathlib.PurePosixPath(x.filename).suffix.lower()
            if basename in {"readme","readme.md","readme.txt","license","license.md","package.json","requirements.txt","pyproject.toml","composer.json","manifest.json","dockerfile","pom.xml","project.godot","server.py","app.py","settings.py","config.py","main.py","index.js","server.js","main.js"} or basename.endswith(".csproj") or basename.endswith(".sln"):
                target_names.append(x)
        details=[]
        for x in target_names[:45]:
            data=z.read(x)
            try:
                txt=data.decode("utf-8-sig")
            except UnicodeDecodeError:
                txt=data.decode("latin-1","replace")
            details.append({"path":x.filename,"preview":red(txt[:3500])})
        names=[x.filename for x in inf if not x.is_dir()]
        source_entries=[]
        for x in inf:
            if x.is_dir() or x.file_size>300_000:continue
            ext=pathlib.PurePosixPath(x.filename).suffix.lower()
            if ext not in {".py",".js",".ts",".cs",".php",".go",".java",".json",".yml",".yaml",".rb",".md",".txt"}:continue
            if "/node_modules/" in x.filename or "/vendor/" in x.filename:continue
            data=z.read(x).decode("utf-8","replace")
            def match_snippets(pattern):
                return [red(data[max(0,m.start()-75):min(len(data),m.end()+180)].replace("\n"," "))[:350] for m in list(re.finditer(pattern,data,re.I))[:5]]
            cues={
                "community_attribution":match_snippets(r"fan.made|unofficial|reverse.engineer|private.server|emulator|replica|recreation|fork|licensed|official|original"),
                "framework":match_snippets(r"flask|fastapi|express|django|mongodb|sqlite|websocket|asp.net|python|nodejs|socket.io"),
                "known_project":match_snippets(r"My Singing Monsters|Big Blue Bubble|BBB|monster-game-server")
            }
            if any(cues.values()):
                source_entries.append({"path":x.filename,"cues":cues})
        # Store only indicators, never code excerpts or configuration previews.
        details=[{"path":x["path"],"note":"Source text omitted"} for x in details]
        source_entries=[{"path":x["path"],"indicators":{k:len(v) for k,v in x["cues"].items()}} for x in source_entries]
        result={
            "source":TARGET,"checked_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "size":len(content),"sha1":digest,
            "total_entries":len(inf),"file_types":dict(suffix_count.most_common()),
            "tree":paths,
            "docs_and_manifest_previews":details,
            "textual_cues":source_entries[:70],
        }
    (OUT/"monster-game-server-inspection.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    report=["# monster-game-server archive structure and provenance inspection","",
        f"Source: {TARGET}",f"SHA-1 verified: `{digest}`",
        f"ZIP bytes: {len(content):,}",f"Entries: {len(inf)}","",
        "## File types",""]
    report.extend(f"- `{k or '(none)'}`: {v}" for k,v in suffix_count.most_common())
    report+=["","## Files (paths only)",""]
    report.extend(f"- `{x['path']}` ({x['size']:,} bytes)" for x in paths)
    report+=["","## Selected documentation and configuration previews (sensitive strings redacted)",""]
    for d in details:
        report.extend([f"### {d['path']}","", "Content omitted; only file presence recorded.",""])
    report+=["","## Indicators (NOT a definitive authenticity conclusion)",""]
    for s in source_entries[:50]:
        report.extend([f"- `{s['path']}`: "+"; ".join(f"{k}={v}" for k,v in s["indicators"].items())])
    (OUT/"monster-game-server-inspection.md").write_text("\n".join(report)+"\n")
    print("Verified archive bytes:",len(content),"entries:",len(inf))
    print("Types:",dict(suffix_count.most_common()))
    print("Full tree:")
    for x in paths:print(" ",x["path"],x["size"])
    print("Selected docs:")
    for d in details[:20]:print("DOC",d["path"])
    print("Code cues:")
    for s in source_entries[:25]:print(s["path"],s["indicators"])
if __name__=="__main__":inspect()
