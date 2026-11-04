#!/usr/bin/env python3
"""Inspect public historical MSM/Monster Choir archives without executing packages.
Original binaries remain ephemeral and are never committed.
"""
import collections,hashlib,io,json,os,pathlib,re,shutil,subprocess,tempfile,urllib.parse,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
CASES=[
  {"id":"chinese_monster_choir","item":"Msmapks","filename":"Monsterchoirchina.uc.apk",
    "sha1":"e5dad967088db4318616f26b642d81080b31931f","bytes":113810411},
  {"id":"korean_monster_choir","item":"Monsterchoir_20231012","filename":"몬스터 합창단.apk",
    "sha1":"2e41a71fdc59be8d4904316adee168c686367e6","bytes":51720835},
  {"id":"msm_ps_vita","item":"msm-ps-vita-game-files","filename":"MSM PS VITA game files.zip",
    "sha1":"4d4bdbb3c4d90aad6743dda8e55dd2ed95605ff8","bytes":71805852}
]
class ArchiveRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self):self.count=0
    def redirect_request(self,req,fp,code,msg,headers,url):
        self.count+=1
        host=urllib.parse.urlsplit(url).hostname or ""
        if self.count>6 or not url.startswith("https://") or not (host=="archive.org" or host.endswith(".archive.org")):raise ValueError("Unexpected mirror/redirect host")
        return super().redirect_request(req,fp,code,msg,headers,url)
OPENER=urllib.request.build_opener(ArchiveRedirect())
def safe_zip_inspection(file_path):
    with zipfile.ZipFile(file_path) as z:
        x=z.infolist()
        if len(x)>35000:raise ValueError("Excessive ZIP entries")
        allnames=[f.filename for f in x if not f.is_dir()]
        sizes=collections.Counter()
        folders=collections.Counter()
        for f in x:
            if f.is_dir():continue
            suffix=pathlib.PurePosixPath(f.filename).suffix.lower()
            sizes[suffix]+=1
            folders["/".join(f.filename.split("/")[:2])]+=1
        suspicious=[n for n in allnames if re.search(r"(?i)(?:unused|scrap|cut_|beta|prototype|testasset|old_|deprecated|placeholder|debug)",n)]
        # metadata only; do not include any credentials, server address or accounts.
        safe_suspicious=[n for n in suspicious if not re.search(r"(?i)password|secret|config|token|auth|credential|account",n)]
        keys=[n for n in allnames if n.lower() in ("androidmanifest.xml","param.sfo","sce_sys/param.sfo")]
        sample_paths=allnames[:65]
        audio=[n for n in allnames if n.lower().endswith((".ogg",".wav",".mid",".mp3"))]
        image=[n for n in allnames if n.lower().endswith((".png",".jpg",".tga",".webp",".pvr"))]
        report={"file_entries":len(allnames),"directory_entries":len(x)-len(allnames),
             "uncompressed_bytes":sum(f.file_size for f in x if not f.is_dir()),
             "extensions":dict(sizes.most_common()),"top_folders":dict(folders.most_common(45)),
             "sample_paths":sample_paths,
             "potential_dev_filename_matches":safe_suspicious[:120],
             "audio_files_count":len(audio),"audio_samples":audio[:45],
             "image_files_count":len(image),"image_samples":image[:45],
             "metadata_files":keys}
        if "AndroidManifest.xml" in z.namelist():
            manifest=z.read("AndroidManifest.xml")
            # String table excerpts only, never source code or any keys.
            ascii_hits=re.findall(rb"(?:com[.][a-zA-Z0-9._]+|versionName|versionCode|My Singing Monsters|Monster Choir|yodo1)",manifest,re.I)
            utf16_hits=re.findall(rb"(?:c\x00o\x00m\x00[.\x00a-zA-Z0-9_]{8,140})",manifest,re.I)
            report["manifest_struct"]={"bytes":len(manifest),"starts_with_binary_xml":manifest[:4].hex(),
                     "ascii_package_hints":[h.decode("ascii","ignore")[:100] for h in ascii_hits[:12]],
                     "utf16_hint_count":len(utf16_hits)}
    return report
rows=[]
with tempfile.TemporaryDirectory() as folder:
 for c in CASES:
    fpath=pathlib.Path(folder)/(c["id"]+("_source.zip" if c["id"]=="msm_ps_vita" else ".apk"))
    url="https://archive.org/download/"+urllib.parse.quote(c["item"],safe="-_")+"/"+urllib.parse.quote(c["filename"],safe="")
    try:
      req=urllib.request.Request(url,headers={"User-Agent":"MSM-Historical-ReadOnly-Asset-Inventory/1.0"})
      with OPENER.open(req,timeout=120) as resp, fpath.open("wb") as dst:
          hasher=hashlib.sha1();count=0
          while True:
              block=resp.read(1024*1024)
              if not block:break
              count+=len(block)
              if count>145_000_000:raise ValueError("Unexpected download size")
              hasher.update(block);dst.write(block)
      good=count==c["bytes"] and hasher.hexdigest()==c["sha1"]
      if not good:raise ValueError("Archive checksum mismatch (not safe to interpret contents)")
      ins=safe_zip_inspection(fpath)
      # local preinstalled Android tooling only; never execute app.
      tool=shutil.which("aapt")
      if not tool and os.environ.get("ANDROID_HOME"):
          root=pathlib.Path(os.environ["ANDROID_HOME"])/"build-tools"
          tools=sorted(root.glob("*/aapt"),reverse=True)
          if tools:tool=str(tools[0])
      if tool and c["id"] in ("chinese_monster_choir","korean_monster_choir"):
          try:
              p=subprocess.run([tool,"dump","badging",str(fpath)],capture_output=True,text=True,timeout=18)
              matches=[]
              for line in p.stdout.splitlines():
                  if line.startswith(("package: ","sdkVersion: ","targetSdkVersion: ","application-label: ")):
                      matches.append(line[:260])
              ins["android_badging"]=matches[:12]
          except Exception as e:ins["android_badging_error"]=type(e).__name__
      rows.append({"id":c["id"],"item":c["item"],"filename":c["filename"],"verified_sha1":hasher.hexdigest(),
                   "size":count,"confirmed":good,"inventory":ins})
      print("DONE",c["id"],"bytes",count,"hash",hasher.hexdigest(),
            "files",ins["file_entries"],"extensions",json.dumps(ins["extensions"]),
            "badging",ins.get("android_badging",[])[:4],flush=True)
    except Exception as e:
      rows.append({"id":c["id"],"item":c["item"],"filename":c["filename"],"error":type(e).__name__+" "+str(e)[:180]})
      print("ERROR",c["id"],type(e).__name__,str(e)[:160],flush=True)
    try:fpath.unlink()
    except:pass
(ROOT/"msm-candidate-static-verified-contents.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n")
print("OUTPUT",json.dumps([{k:v for k,v in row.items() if k!="inventory"} for row in rows]))
