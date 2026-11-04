#!/usr/bin/env python3
"""Read-only metadata deep inspection of checksum-verified PS Vita historical MSM archive."""
import collections,hashlib,io,json,pathlib,re,sqlite3,struct,tempfile,urllib.parse,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
URL="https://archive.org/download/msm-ps-vita-game-files/MSM%20PS%20VITA%20game%20files.zip"
EXPECTED="4d4bdbb3c4d90aad6743dda8e55dd2ed95605ff8"
class Redirect(urllib.request.HTTPRedirectHandler):
    count=0
    def redirect_request(self,req,fp,code,msg,hdrs,u):
        self.count+=1;host=urllib.parse.urlsplit(u).hostname or ""
        if self.count>5 or not u.startswith("https://") or not(host=="archive.org" or host.endswith(".archive.org")):raise ValueError("Bad redirect")
        return super().redirect_request(req,fp,code,msg,hdrs,u)
req=urllib.request.Request(URL,headers={"User-Agent":"MSM-Vita-Historical-Static-Inspection/1.0"})
with urllib.request.build_opener(Redirect()).open(req,timeout=120) as r:raw=r.read(80_000_000)
if hashlib.sha1(raw).hexdigest()!=EXPECTED:raise ValueError("SHA1 mismatch")
z=zipfile.ZipFile(io.BytesIO(raw))
files=[p for p in z.namelist() if not p.endswith("/")]
d={"source":URL,"sha1":EXPECTED,"files":len(files),"metadata":{}}
psf=next((p for p in files if p.lower().endswith("sce_sys/param.sfo")),None)
if psf:
    buf=z.read(psf)
    if len(buf)>20 and buf[:4]==b"\x00PSF":
        magic,ver,keys_start,data_start,n=struct.unpack_from("<4sIIII",buf)
        values={}
        if n<200:
            for i in range(n):
                off=20+i*16
                if off+16>len(buf):break
                keyoff,kind,sz,maxsz,dataoff=struct.unpack_from("<HHIII",buf,off)
                key_end=buf.find(b"\x00",keys_start+keyoff)
                key=buf[keys_start+keyoff:key_end].decode("ascii","replace")
                if re.search(r"(?i)account|secret|token|auth|key|licen",key):continue
                value=buf[data_start+dataoff:data_start+dataoff+min(sz,500)]
                if kind==0x0404 and len(value)>=4:val=int.from_bytes(value[:4],"little")
                else:val=value.rstrip(b"\x00").decode("utf-8","replace")
                values[key]=val
        d["metadata"]["ps_vita_param_sfo"]=values
    else:d["metadata"]["ps_vita_param_sfo_status"]="Unknown SFO format"
sql=next((p for p in files if p.lower().endswith("/msm.db")),None)
if sql:
    db=z.read(sql)
    d["metadata"]["msm_db"]={"bytes":len(db),"header_is_sqlite":db.startswith(b"SQLite format 3\x00")}
    if db.startswith(b"SQLite format 3\x00") and len(db)<50_000_000:
        with tempfile.TemporaryDirectory() as tmp:
            path=pathlib.Path(tmp)/"game.db";path.write_bytes(db)
            try:
                con=sqlite3.connect("file:"+str(path)+"?mode=ro",uri=True)
                tables=con.execute("SELECT name,type FROM sqlite_master WHERE type IN ('table','view') ORDER BY name").fetchall()
                d["metadata"]["msm_db"]["table_count"]=len(tables)
                d["metadata"]["msm_db"]["table_names"]=[t[0] for t in tables if not re.search(r"(?i)user|account|auth|login|token|secret",t[0])][:180]
                con.close()
            except Exception as e:d["metadata"]["msm_db"]["sqlite_error"]=type(e).__name__
tracks=[p for p in files if p.lower().endswith((".vag",".mid",".mp3",".wav")) and "/audio/" in p]
prefix=collections.Counter()
for p in tracks:
    n=p.split("/")[-1]
    match=re.match(r"([A-Za-z0-9]+)[-_]",n)
    if match:prefix[match.group(1)]+=1
d["metadata"]["audio"]={"count":len(tracks),"extensions":dict(collections.Counter(pathlib.PurePosixPath(p).suffix.lower() for p in tracks)),"prefixes":dict(prefix.most_common(80)),
                       "midi_files":[p for p in tracks if p.lower().endswith(".mid")],
                       "vag_first_names":[p.split("/")[-1] for p in tracks if p.lower().endswith(".vag")][:60]}
sprites=[p for p in files if "/gfx/monsters/" in p.lower()]
d["metadata"]["sprites"]={"monster_sprites_count":len(sprites),"extensions":dict(collections.Counter(pathlib.PurePosixPath(p).suffix.lower() for p in sprites)),
                          "sprite_file_names":[p.split("/")[-1] for p in sprites[:180]]}
(ROOT/"msm-vita-metadata-deep.json").write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n")
print(json.dumps(d,indent=2,ensure_ascii=False)[:23000])
