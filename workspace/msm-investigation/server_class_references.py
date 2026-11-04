#!/usr/bin/env python3
"""Cross-reference every game-specific Java class in the historical MSM archive."""
import hashlib,io,json,pathlib,re,urllib.parse,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
URL="https://archive.org/download/monster-game-server/monster-game-server.zip"
SHA="df086c9ca4581733f73f2e8aaea1408382232e4d"
class Redirect(urllib.request.HTTPRedirectHandler):
    count=0
    def redirect_request(self,req,fp,code,msg,hdrs,url):
        self.count+=1
        host=urllib.parse.urlsplit(url).hostname or ""
        if self.count>5 or not url.startswith("https://") or not (host=="archive.org" or host.endswith(".archive.org")):raise ValueError("Bad redirect")
        return super().redirect_request(req,fp,code,msg,hdrs,url)
req=urllib.request.Request(URL,headers={"User-Agent":"Public-MSM-Source-Reference-Audit/1.0"})
with urllib.request.build_opener(Redirect()).open(req,timeout=80) as resp:data=resp.read(20000001)
if len(data)>20000000 or hashlib.sha1(data).hexdigest()!=SHA:raise ValueError("Archive mismatch")
z=zipfile.ZipFile(io.BytesIO(data))
source={}
for name in z.namelist():
    if name.endswith(".java"):
        path="/".join(name.split("/")[1:])
        source[path]=z.read(name).decode("utf-8","replace")
game={p:s for p,s in source.items() if p.startswith("src/com/bigbluebubble/mysingingmonsters/")}
checks=[]
for path,body in game.items():
    name=pathlib.PurePosixPath(path).stem
    refs=[{"file":p.split("/")[-1],"occurrences":len(re.findall(r"\b"+re.escape(name)+r"\b",text))}
          for p,text in source.items() if p!=path and re.search(r"\b"+re.escape(name)+r"\b",text)]
    methods=list(dict.fromkeys(re.findall(r"\b(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?[\w\[\]<>,.?]+\s+([A-Za-z_]\w*)\s*\(",body)))
    checks.append({"class":name,"path":path,"lines":len(body.splitlines()),"methods":methods,
                  "referenced_in_other_files":len(refs),"references":refs[:80]})
focus=["BreedAvailabilityEvent","BreedProbabilityChangeEvent","MonsterRareData","MonsterIslandData",
       "BrandedAdvertisementGroup","MSMAdminCatchUnreleasedAccount","PlayerIslandFactory",
       "MonsterMegaData","StoreReplacements","TimedEventListBuilder"]
focusitems=[x for x in checks if x["class"] in focus]
output={"game_java_files":len(game),"source_sha1":SHA,"files":checks,
    "focus":focusitems,"unreferenced":[x for x in checks if x["referenced_in_other_files"]==0],
    "note":"Static references only. Reflective/dynamic usages can escape this scan. No code contents or account data included."}
(ROOT/"server-class-references.json").write_text(json.dumps(output,indent=2)+"\n")
lines=["# Full MSM game-class cross-reference analysis","",
       "Every MSM Java class is included; no code contents, player records or credentials are reproduced.",
       "","## Interesting classes",""]
for x in focusitems:
    lines.extend(["### "+x["class"],"","Source lines: "+str(x["lines"])+
      "; parsed method names: "+", ".join(x["methods"])+
      "; referencing files: "+str(x["referenced_in_other_files"]),
      "References: "+", ".join(q["file"] for q in x["references"]),""])
lines+=["## All classes and cross-references",""]
for x in checks:
    lines.append("- "+x["class"]+": "+str(x["referenced_in_other_files"])+" other Java source files; "+
                 str(len(x["methods"]))+" parsed methods")
(ROOT/"server-class-references.md").write_text("\n".join(lines)+"\n")
print("FULL GAME CODE CLASS REFERENCES",len(checks))
print("FOCUS",json.dumps(focusitems))
print("NO OTHER CLASS REFS",json.dumps([{"class":x["class"],"lines":x["lines"],"method_count":len(x["methods"])} for x in output["unreferenced"]]))
