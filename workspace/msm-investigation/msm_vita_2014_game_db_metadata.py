#!/usr/bin/env python3
"""Read-only compare checksum-confirmed official-looking 2014 Vita MSM sqlite game database.
Do not execute source code, write imported DB, or publish user/account data.
"""
import collections,hashlib,io,json,pathlib,re,sqlite3,tempfile,urllib.parse,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
URL="https://archive.org/download/msm-ps-vita-game-files/MSM%20PS%20VITA%20game%20files.zip"
EXPECTED="4d4bdbb3c4d90aad6743dda8e55dd2ed95605ff8"
class Redirect(urllib.request.HTTPRedirectHandler):
  count=0
  def redirect_request(self,req,fp,code,msg,head,url):
    self.count+=1
    h=urllib.parse.urlsplit(url).hostname or ""
    if self.count>5 or not url.startswith("https://") or not (h=="archive.org" or h.endswith(".archive.org")):
      raise ValueError("Unexpected archive redirect")
    return super().redirect_request(req,fp,code,msg,head,url)
req=urllib.request.Request(URL,headers={"User-Agent":"Public-MSM-Vita-2014-GameData-Research/1.0"})
with urllib.request.build_opener(Redirect()).open(req,timeout=140) as stream:raw=stream.read(80_000_000)
if hashlib.sha1(raw).hexdigest()!=EXPECTED:raise ValueError("Unverified archive")
with zipfile.ZipFile(io.BytesIO(raw)) as z:
  name=next(x for x in z.namelist() if x.endswith("/msm.db"))
  datab=z.read(name)
  if not datab.startswith(b"SQLite format 3\x00"):raise ValueError("Not an SQLite database")
  with tempfile.TemporaryDirectory() as tmp:
    path=pathlib.Path(tmp)/"game.db";path.write_bytes(datab)
    con=sqlite3.connect("file:"+str(path)+"?mode=ro&immutable=1",uri=True)
    con.row_factory=sqlite3.Row
    allowed=["achievement_ids","breeding_combinations","entities","game_settings","game_settings_offers",
      "genes","island_monsters","island_structures","island_torches","islands","level_xp",
      "monster_island_2_island_map","monster_levels","monsters","quests","scratch_offs","seasonal_monster_info",
      "store_currency","store_groups","store_items","structure_levels","structures"]
    report={"archive_sha1":EXPECTED,"db_bytes":len(datab),
      "table_stats":{},"monster_combinations":{},"island_summary":{},"special_gene_mentions":[],
      "note":"Only approved static game-data tables. No personal records, source binaries, or account information."}
    for table in allowed:
      if not re.fullmatch("[a-z_0-9]+",table):raise ValueError("bad table")
      present=con.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone()[0]
      if not present:continue
      columns=[{"name":r["name"],"type":r["type"]} for r in con.execute("PRAGMA table_info("+table+")")]
      count=con.execute("SELECT count(*) FROM "+table).fetchone()[0]
      report["table_stats"][table]={"rows":count,"columns":columns}
    for table in ["monsters","islands","breeding_combinations","island_monsters"]:
      if table not in report["table_stats"]:continue
      columns=[x["name"] for x in report["table_stats"][table]["columns"]]
      check=[c for c in columns if re.search(r"(?i)gene|element|combination|monster|island|entity|name|bed|enable|breed",c)]
      safe_cols=[c for c in check if not re.search(r"(?i)person|user|account|auth|token|host|password|secret|email|login",c)]
      if not safe_cols:continue
      # Limit rows and cap printed values to avoid dumping the whole DB.
      rows=con.execute("SELECT "+",".join('"'+c+'"' for c in safe_cols)+" FROM "+table+" LIMIT 300")
      item=[{k:str(r[k])[:90] if r[k] is not None else None for k in safe_cols} for r in rows]
      if table=="monsters":
        report["monster_combinations"]={"columns":safe_cols,"rows":item[:65]}
      elif table=="islands":
        report["island_summary"]={"columns":safe_cols,"rows":item[:35]}
      elif table=="breeding_combinations":
        # Count and summarize references without copying individual 1000+ breeding rules.
        match=[x for x in item if any("ABCDE" in (v or "") for v in x.values())]
        report["special_gene_mentions"].append({"table":table,"first_300_rows_matching_ABCDE":len(match),"examples":match[:8]})
      elif table=="island_monsters":
        report["island_monsters_preview"]={"columns":safe_cols,"sample":item[:20]}
    con.close()
(ROOT/"msm-vita-2014-game-db-metadata.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
print("VITA DB TABLES",json.dumps({k:v["rows"] for k,v in report["table_stats"].items()}))
print("MONSTERS",json.dumps(report["monster_combinations"],ensure_ascii=False)[:18000])
print("ISLANDS",json.dumps(report["island_summary"],ensure_ascii=False)[:10000])
print("SPECIAL",json.dumps(report["special_gene_mentions"]))
