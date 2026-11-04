#!/usr/bin/env python3
"""Compare dated XML file listings across public My Singing Monsters server-data snapshots."""
import collections,datetime,json,pathlib,re,urllib.parse,urllib.request
ROOT=pathlib.Path(__file__).resolve().parent
URL="https://archive.org/metadata/msm_dat_files"
with urllib.request.urlopen(urllib.request.Request(URL,headers={"User-Agent":"MSM-Server-Data-Archive-Inventory/1.0"}),timeout=80) as r:doc=json.loads(r.read(14_000_000))
groups=collections.defaultdict(dict);other=[]
for f in doc.get("files",[]):
    n=f.get("name","")
    m=re.fullmatch(r"(\d{4}-\d{2}-\d{2})/([^/]+)\.(xml|json|bin|txt)",n,re.I)
    if m:
        groups[m.group(1)][m.group(2)+"."+m.group(3).lower()]={"sha1":f.get("sha1"),"size":int(f.get("size") or 0),"file":n}
    elif n.endswith((".xml",".json",".bin")):other.append(n)
dates=sorted(groups)
name_all=collections.defaultdict(list)
for date,files in groups.items():
    for n,f in files.items():name_all[n].append(date)
oneoffs={n:v for n,v in name_all.items() if len(v)==1}
last_only={n:v for n,v in name_all.items() if dates[-1] not in v}
transitions=[]
prev=None
for date in dates:
    files=groups[date]
    if prev:
        older=groups[prev]
        added=sorted(set(files)-set(older))
        removed=sorted(set(older)-set(files))
        changed=sorted(n for n in set(files)&set(older) if files[n]["sha1"]!=older[n]["sha1"])
        transitions.append({"from":prev,"to":date,"added_names":added,"removed_names":removed,
            "changed_count":len(changed),"changed_names":changed[:120]})
    prev=date
results={
    "source":URL,"total_archive_entries":len(doc.get("files",[])),
    "snapshot_dates":dates,
    "snapshot_files":{date:{"count":len(groups[date]),"names":sorted(groups[date])} for date in dates},
    "unique_data_file_names":len(name_all),"one_snapshot_names":oneoffs,
    "not_present_in_last_snapshot":last_only,
    "change_trends":transitions,"unclassified_xml_or_json":other[:100],
    "note":"File names and SHA-1 from archive metadata only. Snapshot coverage is uploader-selected; absence does not prove removed from live game."}
(ROOT/"msm-dated-server-data-file-diff.json").write_text(json.dumps(results,ensure_ascii=False,indent=2)+"\n")
print("SNAPSHOTS",json.dumps([{ "date":d,"count":len(groups[d])} for d in dates]))
print("ONEOFFS",json.dumps(oneoffs))
print("MISSING_LATEST",json.dumps(last_only))
print("TRANSITIONS",json.dumps(transitions))
