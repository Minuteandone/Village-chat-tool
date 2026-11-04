#!/usr/bin/env python3
"""Read-only compare two historical official-looking Monster Choir APKs.
No installation/execution or redistribution. Checks original public SHA1.
"""
import collections,hashlib,json,os,pathlib,re,shutil,subprocess,tempfile,urllib.parse,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
ITEM="Msmapks"
CASES=[("korean","MONSTERCHOIRSOUTHKORIEA.apk","2e41a71fdc59be8d4904316adee168c686367e6e",51720835),
       ("chinese","Monsterchoirchina.uc.apk","e5dad967088db4318616f26b642d81080b31931f",113810411)]
class Redirect(urllib.request.HTTPRedirectHandler):
  count=0
  def redirect_request(self,req,fp,code,msg,hdrs,u):
    self.count+=1
    h=urllib.parse.urlsplit(u).hostname or ""
    if self.count>7 or not u.startswith("https://") or not (h=="archive.org" or h.endswith(".archive.org")):
      raise ValueError("Unexpected redirect")
    return super().redirect_request(req,fp,code,msg,hdrs,u)
opener=urllib.request.build_opener(Redirect())
results={}
with tempfile.TemporaryDirectory() as temp:
 for label,filename,expect,size in CASES:
    url="https://archive.org/download/"+ITEM+"/"+urllib.parse.quote(filename)
    file=pathlib.Path(temp)/(label+".apk")
    try:
      req=urllib.request.Request(url,headers={"User-Agent":"Historical-Monster-Choir-APK-Static-Comparison/1.0"})
      with opener.open(req,timeout=140) as stream,file.open("wb") as output:
        dig=hashlib.sha1();total=0
        while True:
          data=stream.read(1024*1024)
          if not data:break
          total+=len(data)
          if total>120_000_000:raise ValueError("Download too large")
          output.write(data);dig.update(data)
      if total!=size or dig.hexdigest()!=expect:raise ValueError("Size/SHA1 mismatch")
      tool=shutil.which("aapt")
      if not tool and os.environ.get("ANDROID_HOME"):
        paths=sorted((pathlib.Path(os.environ["ANDROID_HOME"])/"build-tools").glob("*/aapt"),reverse=True)
        if paths:tool=str(paths[0])
      badging=[]
      if tool:
        p=subprocess.run([tool,"dump","badging",str(file)],text=True,capture_output=True,timeout=22)
        badging=[x for x in p.stdout.splitlines() if x.startswith(("package: ","sdkVersion: ","targetSdkVersion: ","application-label: "))][:15]
      with zipfile.ZipFile(file) as z:
        names=[x.filename for x in z.infolist() if not x.is_dir()]
        nameset=set(names)
        relevant={n for n in names if n.startswith(("assets/gfx/monsters/","assets/audio/music/","assets/xml_resources/","assets/xml_bin/"))}
        weird=[n for n in names if re.search(r"(unused|scrapped|old_|beta|test|proto|_kor|_chi|_uc|gacha)",n,re.I) 
                    and not re.search(r"(?i)key|token|pass|secret|auth|account|credential",n)]
        results[label]={"verified_sha1":expect,"bytes":size,"aapt_badging":badging,"file_count":len(names),
            "extensions":dict(collections.Counter(pathlib.PurePosixPath(n).suffix.lower() for n in names)),
            "monster_sprite_files":sorted(n for n in names if n.startswith("assets/gfx/monsters/"))[:230],
            "monster_audio_files_count":sum(n.startswith("assets/audio/music/") for n in names),
            "monster_audio_file_names":sorted(n for n in names if n.startswith("assets/audio/music/"))[:400],
            "potentially_interesting_file_names":weird[:150],"relevant_path_count":len(relevant)}
        results[label]["_filenames_relevant"]=relevant
      print("COMPLETED",label,total,results[label]["file_count"],badging[:4],flush=True)
    except Exception as e:
      results[label]={"error":type(e).__name__+" "+str(e)[:220]}
      print("FAILED",label,results[label]["error"],flush=True)
    file.unlink(missing_ok=True)
if all("_filenames_relevant" in x for x in results.values()):
  a,b=results["chinese"]["_filenames_relevant"],results["korean"]["_filenames_relevant"]
  results["comparison"]={"in_chinese_only_count":len(a-b),"in_korean_only_count":len(b-a),
      "shared_path_count":len(a&b),
      "chinese_only_monster_sprite_paths":sorted(n for n in a-b if "/gfx/monsters/" in n)[:100],
      "korean_only_monster_sprite_paths":sorted(n for n in b-a if "/gfx/monsters/" in n)[:100],
      "chinese_only_audio_names":[n for n in sorted(a-b) if "/audio/music/" in n][:100],
      "korean_only_audio_names":[n for n in sorted(b-a) if "/audio/music/" in n][:100]}
for d in results.values():d.pop("_filenames_relevant",None)
(ROOT/"msm-choir-apk-content-comparison.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n")
print("SUMMARY",json.dumps({k:({x:v for x,v in d.items() if x not in ("monster_sprite_files","monster_audio_file_names","potentially_interesting_file_names")} if isinstance(d,dict) else d) for k,d in results.items()},ensure_ascii=False)[:12000])
