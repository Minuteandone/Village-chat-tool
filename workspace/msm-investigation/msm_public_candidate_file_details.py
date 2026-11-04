#!/usr/bin/env python3
"""Inventory the exact files of publicly listed MSM archival candidates, with metadata only."""
import datetime, json, pathlib, re, time, urllib.parse, urllib.request
BASE=pathlib.Path(__file__).resolve().parent
IDS=[
 "Msmapks","msm_dat_files","msm-ps-vita-game-files",
 "Monsterchoir_20231012","monster_choir_korean_sprites",
 "com.bigbluebubble.singingmonsters.full",
 "MySingingMonsters","1.4.3_202310",
 "my-singing-monsters-official-guide-v1.3.0",
 "com.bigbluebubble.my-singing-monsters-ios4.0-clutch-2.0.4",
 "My_Muppets_Show_1.1.6_ios_5.1","my-muppets-show-base",
 "msm-sandbox-classic","my-song.band_202608","plant-island-beta-version",
 "20240421","msm-dof-baby-forms","com.bigbluebubble.-my-singing-monsters-v-3.0.5-i-os-9.0-clutch-2.0.4"
]
rows=[]
for ident in IDS:
    url="https://archive.org/metadata/"+urllib.parse.quote(ident,safe="-_")
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"MSM-Preservation-Metadata-Research/1.0"})
        with urllib.request.urlopen(req,timeout=32) as response:
            dat=json.loads(response.read(8_000_000))
        m=dat.get("metadata",{})
        files=[]
        for f in dat.get("files",[]):
            name=f.get("name","")
            if not name or name.endswith(("_meta.xml","_files.xml","_reviews.xml","_archive.torrent","_thumb.jpg","_itemimage.jpg")):continue
            files.append({"name":name,"size":f.get("size"),"sha1":f.get("sha1"),"md5":f.get("md5"),
                          "source":f.get("source"),"format":f.get("format")})
        rows.append({"identifier":ident,"title":m.get("title"),"publicdate":m.get("publicdate"),
            "description_excerpt":str(m.get("description",""))[:380],
            "file_total":len(dat.get("files",[])),"selected_files":files[:300]})
    except Exception as e:
        rows.append({"identifier":ident,"error":str(e)[:200]})
    time.sleep(0.1)
(BASE/"msm-public-candidate-file-details.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False)+"\n")
for r in rows:
    print(json.dumps({"identifier":r["identifier"],"title":r.get("title"),"file_total":r.get("file_total"),
          "files":r.get("selected_files",[])[:100],"error":r.get("error")},ensure_ascii=False))
