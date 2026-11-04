#!/usr/bin/env python3
"""Extract non-art metadata/catalogs from the archived public Official Guide Unity bundles."""
import collections, datetime, json, pathlib
import UnityPy
from deep_archive_probe import ROOT,ORIGINAL,archive_url,fetch
VERSIONS=["1280 (1.3.0)","1383 (sept 26 2019)","1428 (oct 23 2019)"]
def retrieve(version,kind):
    key=f"dlc/{version}/android/{kind}.unity3d"
    import hashlib
    raw,_=fetch(archive_url(key),1_200_000,"archive")
    assert hashlib.sha1(raw).hexdigest()==ORIGINAL[key]["sha1"],"hash mismatch"
    env=UnityPy.load(raw)
    objects={}
    for obj in env.objects:
        if obj.type.name=="MonoBehaviour":
            tree=obj.read_typetree()
            objects[tree.get("m_Name")]=tree
    return objects
def get_id(row):
    for key in ["id","entity_id","monster_id","entityId","name","monsterName","structureName","decorationName","codeName","uniqueName"]:
        if key in row and isinstance(row[key],(str,int,float)):
            return str(row[key])
    return ""
def brief(row):
    preferred=["id","entity_id","monsterName","monster_name","name","classId","element","entity_type",
               "typeId","family","key","structureName","decorationName","spriteName","codeName","monstertype"]
    result={k:row[k] for k in preferred if k in row and isinstance(row[k],(str,int,float,bool))}
    if not result:result={k:v for k,v in list(row.items())[:4] if isinstance(v,(str,int,float,bool))}
    return result
def flatten_catalog(root):
    info={}
    for domain,value in root.items():
        if not isinstance(value,dict):continue
        for category,rows in value.items():
            if isinstance(rows,list) and rows and isinstance(rows[0],dict):
                ident=f"{domain}.{category}"
                info[ident]={"count":len(rows),"columns":list(rows[0])[:50],
                    "items":[brief(r) for r in rows[:3000]]}
    return info
def keyed(entries):
    mapping={}
    for i,row in enumerate(entries):
        ident=get_id(row) or json.dumps(row,sort_keys=True) or f"idx_{i}"
        mapping[ident]=row
    return mapping
def difference(old,new):
    changes={}
    for k in sorted(set(old)|set(new)):
        a=old.get(k,{"count":0,"items":[]})
        b=new.get(k,{"count":0,"items":[]})
        m1=keyed(a["items"]);m2=keyed(b["items"])
        added=[m2[x] for x in m2.keys()-m1.keys()]
        removed=[m1[x] for x in m1.keys()-m2.keys()]
        if added or removed or a["count"]!=b["count"]:
            changes[k]={"before":a["count"],"after":b["count"],
                        "added":added[:150],"removed":removed[:150]}
    return changes

result={"created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source":"https://archive.org/details/msm_official_guide_dlcs",
        "note":"Compact historical data object metadata, not screenshots or copyrighted game files.",
        "versions":{},"diffs":{}}
for version in VERSIONS:
    try:
        d=retrieve(version,"data")
        m=retrieve(version,"master")
        data=d.get("AllData",{})
        global_lut=m.get("GlobalLookupData",{})
        cat=flatten_catalog(data)
        result["versions"][version]={"catalog":cat,"version_field":global_lut.get("version"),
             "global_lookup_categories":{k:len(v) if isinstance(v,(list,dict)) else str(v)[:90] for k,v in global_lut.items()
                 if k not in ("m_GameObject","m_Script")},
             "root_categories":{k:list(v)[:20] if isinstance(v,dict) else type(v).__name__ for k,v in data.items() if not k.startswith("m_")}}
    except Exception as e:result["versions"][version]={"error":str(e)[:200]}
for before,after in [("1280 (1.3.0)","1383 (sept 26 2019)"),
                     ("1383 (sept 26 2019)","1428 (oct 23 2019)")]:
    v1=result["versions"][before].get("catalog",{})
    v2=result["versions"][after].get("catalog",{})
    result["diffs"][before+" -> "+after]=difference(v1,v2)
(ROOT/"guide_catalog_diff.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

lines=["# My Singing Monsters Official Guide — extracted 2018/2019 data catalog comparison","",
       "Source: "+result["source"],"","The Unity \`AllData\` and \`GlobalLookupData\` serialized objects were read and compared. Labels are internal data keys, not proof of scrapped content.",""]
for v,data in result["versions"].items():
    lines+=["## "+v,"", "Embedded version: "+str(data.get("version_field")),""]
    if "error" in data:
        lines+=["Error: "+data["error"],""];continue
    for name,info in data["catalog"].items():
        lines+=[f"- {name}: {info['count']} entries"]
    lines+=[""]
for label,changes in result["diffs"].items():
    lines+=["## Differences: "+label,""]
    for kind,d in changes.items():
        lines+=[f"### {kind} ({d['before']} -> {d['after']})",""]
        lines+=["Added: "+str(len(d["added"]))+"; removed: "+str(len(d["removed"]))+" (first 150 entries max)",""]
        for row in d["added"][:25]:lines+=["- Added: \`"+json.dumps(row,ensure_ascii=False)+"\`"]
        for row in d["removed"][:25]:lines+=["- Removed: \`"+json.dumps(row,ensure_ascii=False)+"\`"]
        lines+=[""]
lines+=["This compares compact record identifiers and names only. It does not prove changed assets are unreleased or cut."]
(ROOT/"guide_catalog_diff.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
for v,d in result["versions"].items():
    print("VERSION",v,"embedded",d.get("version_field"),"error",d.get("error"),"CAT",[(k,x["count"]) for k,x in d.get("catalog",{}).items()])
for title,changes in result["diffs"].items():
    print("COMPARISON",title,"changed categories",len(changes))
    for cat,v in changes.items():
        print("  ",cat,v["before"],"->",v["after"],"added",len(v["added"]),"removed",len(v["removed"]))
        for row in v["added"][:12]:print("   +",row)
        for row in v["removed"][:8]:print("   -",row)
