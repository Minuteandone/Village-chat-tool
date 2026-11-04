#!/usr/bin/env python3
"""One-shot, bounded public MSM archival comparison. Binary sources are temporary and not committed."""
import collections, datetime, hashlib, html.parser, io, json, os, pathlib, re, subprocess, tempfile
import urllib.parse, urllib.request

ROOT=pathlib.Path(__file__).resolve().parent
META=json.loads((ROOT/"official-guide-archive-metadata.json").read_text())
ORIGINAL={x["name"]:x for x in META["files"] if x.get("source")=="original"}
OUT=ROOT/"deep_archive_results.json"
AGENT="MSM-historical-public-archive-research/1.0"
class Redirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, base):
        self.base=base
        self.count=0
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.count+=1
        host=(urllib.parse.urlsplit(newurl).hostname or "").lower()
        allowed=(
            (self.base=="archive" and (host=="archive.org" or host.endswith(".us.archive.org")))
            or (self.base=="debug" and (host=="debugging.games" or host.endswith(".debugging.games")))
        )
        if self.count>5 or not allowed or not newurl.startswith("https://"):
            raise RuntimeError("Redirect outside approved public archive hosts")
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def fetch(url, max_bytes, source):
    req=urllib.request.Request(url,headers={"User-Agent":AGENT,"Accept":"*/*"})
    with urllib.request.build_opener(Redirects(source)).open(req,timeout=40) as res:
        b=res.read(max_bytes+1)
        final=res.geturl()
    if len(b)>max_bytes: raise ValueError("File exceeds bounded download limit")
    return b,final

def archive_url(path):
    return "https://archive.org/download/msm_official_guide_dlcs/"+urllib.parse.quote(path,safe="/")

class LinkParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.href=None; self.buf=[]; self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag=="a": self.href=dict(attrs).get("href"); self.buf=[]
    def handle_data(self,data):
        if self.href is not None:self.buf.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self.href is not None:
            self.links.append(("".join(self.buf).strip(),self.href));self.href=None

def try_symbols(results):
    section={"index":"https://debugging.games/Windows","status":"not_attempted","entries":[]}
    results["pc_2021"]=section
    try:
        page,final=fetch(section["index"],1_200_000,"debug")
        parse=LinkParser();parse.feed(page.decode("utf-8","replace"))
        matches=[(txt,href) for txt,href in parse.links if "My Singing Monsters" in txt and ".7z" in txt and "2021-" in txt]
        section["index_matches"]=[{"text":txt,"href":href} for txt,href in matches]
        if not matches:
            section["status"]="No 2021 link anchors found; only page listing available"
            return
        for txt,href in matches[:2]:
            u=urllib.parse.urljoin(final,href)
            host=urllib.parse.urlsplit(u).hostname
            entry={"title":txt,"requested_url":u}
            section["entries"].append(entry)
            if not (host=="debugging.games" or host.endswith(".debugging.games")):
                entry["error"]="Unexpected download host";continue
            try:
                b,dest=fetch(u,18_000_000,"debug")
                entry["bytes"]=len(b);entry["sha256"]=hashlib.sha256(b).hexdigest()
                entry["final_url"]=dest
                with tempfile.TemporaryDirectory() as t:
                    archive=pathlib.Path(t)/"archive.7z";archive.write_bytes(b)
                    p=subprocess.run(["7z","l","-slt",str(archive)],capture_output=True,text=True,timeout=18)
                    entry["7z_exit_code"]=p.returncode
                    if p.returncode==0:
                        entries=[]
                        for block in p.stdout.split("\n\n"):
                            z={}
                            for line in block.splitlines():
                                if " = " in line:
                                    a,c=line.split(" = ",1)
                                    if a in ("Path","Size","Packed Size","Attributes","Modified"):z[a]=c
                            if z.get("Size") and z.get("Path")!="archive.7z":entries.append(z)
                        entry["contents"]=entries[:100]
                        entry["item_count"]=len(entries)
                    else:entry["7z_error"]=p.stderr[-500:]
            except Exception as e:entry["error"]=type(e).__name__+": "+str(e)[:200]
        section["status"]="completed"
    except Exception as e:
        section["status"]=type(e).__name__+": "+str(e)[:200]

def try_dlc(results):
    section=[]
    results["guide_dlc_bundles"]=section
    versions=["1280 (1.3.0)","1383 (sept 26 2019)","1428 (oct 23 2019)"]
    names={"Server","data.unity3d","master.unity3d","localization.unity3d","static_data.unity3d"}
    try:
        import UnityPy
        have_unity=True
    except Exception as exc:
        have_unity=False; results["unitypy_import_error"]=repr(exc)
    for ver in versions:
        for f in META["files"]:
            path=f.get("name","")
            if f["source"]!="original" or not path.startswith(f"dlc/{ver}/android/") or path.split("/")[-1] not in names:
                continue
            item={"path":path,"bytes_expected":int(f.get("size") or 0),"archive_sha1":f.get("sha1")}
            section.append(item)
            try:
                data,url=fetch(archive_url(path),1_200_000,"archive")
                item["bytes"]=len(data)
                sha=hashlib.sha1(data).hexdigest()
                item["sha1_verified"]=(sha==f.get("sha1"))
                if sha!=f.get("sha1"): raise ValueError("Hash verification failed")
                if path.endswith("/Server"):
                    content=data.decode("utf-8","replace")
                    # public URL/config hints, without printing arbitrary possible credentials
                    item["config_lines"]=[line[:190] for line in content.splitlines() if not re.search(r"token|password|secret|authorization|bearer|key",line,re.I)][:25]
                    item["url_hosts"]=sorted(set(urllib.parse.urlsplit(u).hostname for u in re.findall(r"https?://[^\s\"'<>]+",content) if urllib.parse.urlsplit(u).hostname))
                elif have_unity:
                    env=UnityPy.load(data)
                    types=collections.Counter()
                    objs=[]
                    for obj in env.objects:
                        ty=obj.type.name; types[ty]+=1
                        ob={"type":ty}
                        try:
                            read=obj.read()
                            name=getattr(read,"m_Name",None)
                            if isinstance(name,str) and name:ob["name"]=name[:140]
                            if ty=="TextAsset":
                                sc=getattr(read,"script",None)
                                if isinstance(sc,(bytes,bytearray)):sc=sc.decode("utf-8","replace")
                                if isinstance(sc,str):ob["text_preview"]=sc[:200]
                        except Exception as e:ob["read_error"]=str(e)[:130]
                        if len(ob)>1:objs.append(ob)
                    item["unity_object_count"]=sum(types.values())
                    item["unity_types"]=dict(types.most_common())
                    item["objects_named_or_text"]=objs[:180]
                else:
                    item["header_hex"]=data[:20].hex()
            except Exception as e:
                item["error"]=type(e).__name__+": "+str(e)[:220]

def main():
    result={"generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "scope":"Public game preservation metadata only; original binary archives remain in runner temporary storage",
            "metadata_source":"https://archive.org/metadata/msm_official_guide_dlcs"}
    try_symbols(result)
    try_dlc(result)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    md=["# Deep MSM archive inspection","",
        "Run: "+result["generated_utc"],"",
        "Archive sources were publicly available; binary content was not committed.","",
        "## 2021 PC Windows archives",""]
    section=result["pc_2021"]
    md+=["Status: "+section["status"],""]
    for e in section["entries"]:
        md+=[f"### {e['title']}","",f"Downloaded bytes: {e.get('bytes','not retrieved')}.",
             f"Listed items: {e.get('item_count','unknown')}.",f"Error: {e.get('error','none')}.",""]
        for z in e.get("contents",[])[:40]:
            md.append("- "+z.get("Path","?")+" ("+z.get("Size","?")+" bytes)")
    md+=["","## Official Guide DLC",""]
    for e in result["guide_dlc_bundles"]:
        md+=[f"### {e['path']}","",
            f"Downloaded {e.get('bytes','no')} bytes. SHA-1 verified: {e.get('sha1_verified',False)}.",
            f"Unity objects: {e.get('unity_object_count','unknown')}.",
            f"Object types: {e.get('unity_types',{})}.",
            f"Error: {e.get('error','none')}.",""]
        for obj in e.get("objects_named_or_text",[])[:40]:
            md.append("- "+obj.get("type","")+": "+obj.get("name","(unnamed)"))
        for line in e.get("config_lines",[])[:15]:
            md.append("- Config: "+line)
    md+=["","**Interpretation caution:** Object names, compiler symbols and server paths do not by themselves establish scrapped gameplay."]
    (ROOT/"deep_archive_results.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print("Windows: "+section["status"])
    for e in section["entries"]:
        print("Archive",e["title"],"bytes",e.get("bytes"),"items",e.get("item_count"),"error",e.get("error"))
        for x in e.get("contents",[])[:16]:print("  ",x.get("Path"),x.get("Size"))
    print("Guide DLC:")
    for e in result["guide_dlc_bundles"]:
        print(e["path"],e.get("bytes"),e.get("unity_object_count"),e.get("unity_types"),e.get("error"))
        for line in e.get("config_lines",[])[:6]:print("  CFG",line)
        for x in e.get("objects_named_or_text",[])[:12]:print("  OBJ",x.get("type"),x.get("name"))
if __name__=="__main__":main()
