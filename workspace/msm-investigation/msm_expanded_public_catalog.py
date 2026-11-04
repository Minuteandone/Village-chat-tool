#!/usr/bin/env python3
"""Public archive catalog and file listings for historical MSM/Monster Choir.
No apps/binaries downloaded, executed, or uploaded. Metadata only."""
import datetime,html,json,pathlib,re,time,urllib.parse,urllib.request,urllib.error
ROOT=pathlib.Path(__file__).resolve().parent
Q=[
 'title:"My Singing Monsters"',
 'title:"Dawn of Fire" AND mediatype:software',
 'title:"My Muppets Show"',
 'title:"Monster Choir"',
 'title:"怪兽合唱团"',
 'title:"몬스터 합창단"',
 'title:"Big Blue Bubble"',
 'identifier:msm* AND mediatype:software',
 'identifier:mysingingmonsters*',
 'title:"Thumpies"',
]
def fetch(url,max_bytes=3_000_000,timeout=28):
    req=urllib.request.Request(url,headers={"User-Agent":"MSM-Historical-Preservation-Metadata-Catalog/1.0"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        return r.read(max_bytes+1)[:max_bytes]
items={};errors={};query_counts={}
for q in Q:
    args=[("q",q),("fl[]","identifier"),("fl[]","title"),
          ("fl[]","mediatype"),("fl[]","publicdate"),("fl[]","date"),
          ("rows","200"),("page","1"),("output","json")]
    url="https://archive.org/advancedsearch.php?"+urllib.parse.urlencode(args)
    try:
        j=json.loads(fetch(url))
        docs=j.get("response",{}).get("docs",[])
        query_counts[q]={"numFound":j.get("response",{}).get("numFound"),"returned":len(docs)}
        for x in docs:
            ident=x.get("identifier")
            if not ident:continue
            name=x.get("title","")
            if isinstance(name,list):name="; ".join(name)
            d={"identifier":ident,"title":name,"mediatype":x.get("mediatype"),"publicdate":x.get("publicdate"),"date":x.get("date")}
            items[ident]=d
    except Exception as e:errors[q]=type(e).__name__+" "+str(e)[:130]
    time.sleep(0.2)
ordered=sorted(items.values(),key=lambda x:(x["title"] or "").lower())
out={"generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
     "searches":query_counts,"errors":errors,"unique_items":len(items),"results":ordered}
(ROOT/"msm-expanded-public-catalog.json").write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
# Follow metadata only on most likely candidate IDs based on title and apparent upload context.
candidates=[x for x in ordered if
    re.search(r"singing monsters|monster choir|muppets show|dawn of fire|怪兽合唱团|몬스터 합창단",x["title"],re.I)]
details=[]
for x in candidates[:35]:
    ident=x["identifier"]
    try:
        meta=json.loads(fetch("https://archive.org/metadata/"+urllib.parse.quote(ident),max_bytes=1_800_000,timeout=20))
        ff=meta.get("files",[])
        selected=[{"name":f.get("name"),"size":f.get("size"),"mtime":f.get("mtime"),"source":f.get("source")}
            for f in ff if re.search(r"\.(?:apk|ipa|zip|rar|7z|tar(?:\.gz)?|unity3d|assetbundle|obb|exe|bin|db|sqlite|mid|sql)$",f.get("name",""),re.I)]
        details.append({"identifier":ident,"title":x["title"],"publicdate":meta.get("metadata",{}).get("publicdate"),
                        "file_count":len(ff),"interesting_files":selected[:100]})
    except Exception as e:details.append({"identifier":ident,"error":type(e).__name__})
    time.sleep(0.12)
(ROOT/"msm-expanded-public-catalog-details.json").write_text(json.dumps(details,indent=2,ensure_ascii=False)+"\n")
print("CATALOG",json.dumps({"queries":query_counts,"errors":errors,"unique_items":len(items)},ensure_ascii=False))
print("RESULTS",json.dumps(ordered[:120],ensure_ascii=False))
print("DETAILS",json.dumps(details[:35],ensure_ascii=False))
