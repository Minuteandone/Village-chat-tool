#!/usr/bin/env python3
"""Full static inventory of historical MSM archive; excludes wordsFile.txt."""
import collections, datetime, hashlib, io, json, pathlib, re, urllib.parse, urllib.request, zipfile, csv, xml.etree.ElementTree as ET
BASE=pathlib.Path(__file__).resolve().parent
URL="https://archive.org/download/monster-game-server/monster-game-server.zip"
DIGEST="df086c9ca4581733f73f2e8aaea1408382232e4d"
class Redirect(urllib.request.HTTPRedirectHandler):
    def __init__(self):self.count=0
    def redirect_request(self,req,fp,code,msg,hdrs,u):
        self.count+=1
        h=urllib.parse.urlsplit(u).hostname or ""
        if self.count>5 or not u.startswith("https://") or not (h=="archive.org" or h.endswith(".archive.org")):
            raise ValueError("Unexpected redirect")
        return super().redirect_request(req,fp,code,msg,hdrs,u)
req=urllib.request.Request(URL,headers={"User-Agent":"Public-MSM-Source-Static-Review/1.0"})
with urllib.request.build_opener(Redirect()).open(req,timeout=80) as resp:raw=resp.read(20000001)
if len(raw)>20000000 or hashlib.sha1(raw).hexdigest()!=DIGEST:raise ValueError("Archive is too large or changed")
z=zipfile.ZipFile(io.BytesIO(raw))
if len(z.infolist())>350:raise ValueError("Archive has unexpected contents")
m_re=re.compile(r"\b(public|private|protected)\s+(?:(?:static|final|synchronized|abstract|native)\s+)*(?:[\w\[\]<>,.?]+\s+)+([A-Za-z_]\w*)\s*\(",re.M)
class_re=re.compile(r"\b(class|interface|enum)\s+([A-Za-z_]\w*)")
mark_re=re.compile(r"\b(TODO|FIXME|HACK|XXX|UNUSED|DISABLED|UNRELEASED|TEMPORARY|DEPRECATED|TESTING)\b",re.I)
sensitive=re.compile(r"password|credential|secret|token|access.?key|auth|account|email|session|private",re.I)
TOPICS={
 "Monster and breeding":r"monster|breed|egg|nurs|gene|hatch|rare|box|fuz",
 "Island and structures":r"island|structure|deco|hotel|storage|torch|tribal",
 "Currencies, rewards, store":r"currency|diamond|coin|store|reward|purchase|scratch|advert|sale",
 "Quests and timed events":r"quest|event|achiev|promo|time|goal",
 "Music and minigames":r"music|composer|track|minigame|memory|instrument",
 "Administration and tests":r"admin|test|debug|qa|unreleased",
 "Networking and services":r"server|http|cloud|auth|session|metric|encryp|sns|sqs"
}
def rel(n):return "/".join(n.split("/")[1:])
def category(path):
    if path.startswith("external/src/org/json/"):return "Third-party JSON source"
    if path.startswith("external/src/com/bigbluebubble/"):return "Shared BBB infrastructure"
    if path.startswith("src/com/bigbluebubble/mysingingmonsters/"):
        tail=path.split("/")[4:-1]
        return "MSM game code: "+("/".join(tail) if tail else "core")
    if path.startswith("external/lib/"):return "Libraries and library configuration"
    if path.startswith("external/"):return "Shared code or configuration"
    return "Root project and database"
def xml_info(data,path):
    try:
        root=ET.fromstring(data)
        tags=collections.Counter(x.tag.split("}")[-1] for x in root.iter())
        result={"root_tag":root.tag.split("}")[-1],"tag_counts":dict(tags)}
        if path=="build.xml":
            result["ant_targets"]=[x.attrib["name"] for x in root.iter() if x.tag.endswith("target") and "name" in x.attrib][:100]
        return result
    except Exception as e:return {"parse_error":type(e).__name__}
def jar_info(data):
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as f:
            ns=f.namelist()
            classes=[x for x in ns if x.endswith(".class")]
            top=collections.Counter("/".join(x.split("/")[:3]) for x in classes)
            vers=collections.Counter()
            for n in classes[:120]:
                h=f.read(n)[:8]
                if len(h)==8 and h[:4]==bytes.fromhex("cafebabe"):
                    vers[int.from_bytes(h[6:8],"big")]+=1
            return {"class_count":len(classes),"entry_count":len(ns),
                    "class_package_groups":dict(top.most_common(18)),
                    "class_file_major_versions_sample":dict(vers)}
    except Exception as e:return {"error":type(e).__name__}
inventory=[];classes=[];jars=[];misc=[];comments=[];skipped=[]
for x in z.infolist():
    if x.is_dir():continue
    p=rel(x.filename)
    if pathlib.PurePosixPath(p).name=="wordsFile.txt":
        skipped.append(p);continue
    suf=pathlib.PurePosixPath(p).suffix.lower()
    inventory.append({"path":p,"kind":suf,"group":category(p),"bytes":x.file_size,
                      "date":str(x.date_time[0])+"-"+str(x.date_time[1]).zfill(2)+"-"+str(x.date_time[2]).zfill(2)})
    data=z.read(x)
    if suf==".java":
        s=data.decode("utf-8","replace")
        methods=list(dict.fromkeys(x.group(2) for x in m_re.finditer(s)))
        cls=class_re.findall(s)
        imports=re.findall(r"(?m)^\s*import\s+([\w.]+)\s*;",s)
        tags=[k for k,pat in TOPICS.items() if re.search(pat,p+" "+" ".join(methods),re.I)]
        found={}
        for term in ["BATTLE","DARE","ABCDE","UNRELEASED","FIXME","TODO","HACK","UNDERLING"]:
            n=len(re.findall(r"\b"+term+r"\b",s,re.I))
            if n:found[term]=n
        c={"path":p,"group":category(p),"lines":len(s.splitlines()),"class_names":[b for a,b in cls][:25],
           "method_count":len(methods),"methods":methods[:280],"imports_count":len(imports),
           "dependency_roots":sorted(set(".".join(q.split(".")[:2]) for q in imports if not q.startswith(("java.","javax."))))[:35],
           "topics":tags,"keyword_counts":found}
        classes.append(c)
        for n,line in enumerate(s.splitlines(),1):
            if len(line)>500 or sensitive.search(line) or not mark_re.search(line):continue
            if line.lstrip().startswith(("//","/*","*")) or "TODO" in line or "FIXME" in line:
                comments.append({"file":p,"line":n,"tags":sorted(set(k.upper() for k in mark_re.findall(line)))})
    elif suf==".jar":
        jars.append({"path":p,"bytes":x.file_size,**jar_info(data)})
    elif suf in (".xml",".jardesc"):
        misc.append({"path":p,"kind":"XML",**xml_info(data,p)})
    elif suf==".properties":
        lines=data.decode("utf-8","replace").splitlines()
        keys=[line.split("=",1)[0].split(":",1)[0].strip()
              for line in lines if line.strip() and not line.lstrip().startswith(("#","!")) and ("=" in line or ":" in line)]
        misc.append({"path":p,"kind":"Properties","key_count":len(keys),
                     "non_sensitive_key_names":[k for k in keys if not sensitive.search(k)][:160]})
    elif suf==".sql":
        text=data.decode("utf-8","replace")
        names=re.findall(r"(?im)\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?\x60?([a-z_][\w]*)\x60?",text)
        safe=[n for n in names if not n.startswith("user_") and n!="users"]
        refs=collections.Counter(re.findall(r"(?im)\b(?:FROM|UPDATE|INTO|JOIN)\s+\x60?([a-z_]\w*)",text))
        misc.append({"path":p,"kind":"SQL","table_count":len(names),
                     "nonpersonal_table_names":safe,
                     "nonpersonal_sql_references":{k:v for k,v in refs.items() if k in safe}})
    else:
        misc.append({"path":p,"kind":"Other"})
result={"original_url":URL,"sha1":DIGEST,"zip_size":len(raw),"total_items_reviewed":len(inventory),
        "excluded":skipped,"inventory":inventory,"java":classes,"jars":jars,"misc":misc,
        "dev_markers":comments,"source_code_republished":False,
        "analysis_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
(BASE/"server-full-file-audit.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
with (BASE/"server-full-file-index.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=["path","kind","group","bytes","date"]);w.writeheader();w.writerows(inventory)
lines=["# MSM server archive — every file except wordsFile.txt",
       "","Only metadata and derived observations are reproduced. The archive is not executed.","",
       "## File inventory", ""]
for x in inventory:lines.append("- "+x["path"]+" ("+str(x["bytes"])+" bytes)")
lines+=["","## Every Java source file",""]
for c in classes:
    lines.extend(["### "+c["path"],"",
      "Lines: "+str(c["lines"])+"; parsed methods: "+str(c["method_count"]),
      "Classes: "+", ".join(c["class_names"]),
      "Methods: "+(", ".join(c["methods"]) if c["methods"] else "(none parsed)"),
      "Topics: "+", ".join(c["topics"]),""])
lines+=["","## All Java libraries",""]
for j in jars:
    lines.extend(["### "+j["path"],"Class count: "+str(j.get("class_count")),
      "Packages: "+", ".join(j.get("class_package_groups",{}).keys()),""])
lines+=["","## XML, properties and SQL files",""]
for m in misc:lines.extend(["### "+m["path"],json.dumps(m,ensure_ascii=False),""])
lines+=["","## Development markers",""]
for m in comments:lines.append("- "+m["file"]+":"+str(m["line"])+" "+",".join(m["tags"]))
lines+=["","These source-code identifiers are leads, not confirmation of scrapped features."]
(BASE/"server-full-file-audit.md").write_text("\n".join(lines)+"\n")
print("DONE",len(inventory),"files",len(classes),"java",len(jars),"JAR",len(misc),"other; excluding",skipped)
print("GROUPS",dict(collections.Counter(x["group"] for x in inventory)))
print("JARS",json.dumps([{"path":j["path"],"classes":j.get("class_count"),"entries":j.get("entry_count")} for j in jars]))
print("OTHER",json.dumps(misc)[:8000])
print("COMMENT MARKERS",len(comments))
for c in classes:
    if any(k in c["keyword_counts"] for k in ["BATTLE","DARE","ABCDE","UNRELEASED","UNDERLING"]):
        print("CODE TERMS",c["path"],c["keyword_counts"])
