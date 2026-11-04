#!/usr/bin/env python3
"""Extract only gameplay identifiers (never user data) from archived MSM SQL seed."""
import datetime,hashlib,io,json,pathlib,re,urllib.parse,urllib.request,zipfile
BASE=pathlib.Path(__file__).resolve().parent
SRC='https://archive.org/download/monster-game-server/monster-game-server.zip'
HASH='df086c9ca4581733f73f2e8aaea1408382232e4d'
class R(urllib.request.HTTPRedirectHandler):
    count=0
    def redirect_request(self,req,fp,code,msg,hdrs,url):
        self.count+=1;h=urllib.parse.urlsplit(url).hostname or ''
        if self.count>5 or not (h=='archive.org' or h.endswith('.archive.org')) or not url.startswith('https://'):
            raise ValueError('Unexpected redirect')
        return super().redirect_request(req,fp,code,msg,hdrs,url)
with urllib.request.build_opener(R()).open(urllib.request.Request(SRC,headers={'User-Agent':'MSM-2012-Seed-Research/1.0'}),timeout=80) as resp: raw=resp.read(20000001)
if len(raw)>20000000 or hashlib.sha1(raw).hexdigest()!=HASH:raise ValueError('Archive invalid')
z=zipfile.ZipFile(io.BytesIO(raw))
f=next(x for x in z.namelist() if x.endswith('my_singing_monsters_clean_20120810.sql'))
sql=z.read(f).decode('utf-8','replace')
ALLOW=['islands','monsters','entities','structures','breeding_combinations','quests','quest_types','island_monsters']
def split_rows(body,limit=4000):
    rows=[];col=[];row=[];quoted=False;escape=False;depth=0
    for ch in body:
        if quoted:
            if escape:
                col.append(ch);escape=False
            elif ch=='\\':escape=True
            elif ch=="'":quoted=False
            else:col.append(ch)
        elif ch=="'":quoted=True
        elif ch=='(':
            if depth==0:row=[];col=[]
            else:col.append(ch)
            depth+=1
        elif ch==')':
            depth-=1
            if depth==0:
                row.append(''.join(col).strip())
                rows.append(row)
                if len(rows)>=limit:break
            else:col.append(ch)
        elif ch==',' and depth==1:
            row.append(''.join(col).strip());col=[]
        elif ch==';' and depth==0:break
        elif depth>0:col.append(ch)
    return rows
def safe(t):
    if not isinstance(t,str):return None
    t=t.strip().replace('\n',' ')
    if not re.fullmatch(r'[A-Za-z0-9 _.-]{0,100}',t):return '(non-identifier)'
    return t
game={}
for table in ALLOW:
    schema=re.search(r'CREATE\s+TABLE\s+\x60?'+re.escape(table)+r'\x60?\s*\((.*?)\)\s*(?:ENGINE|TYPE|;)',sql,re.I|re.S)
    if not schema:continue
    cols=re.findall(r'(?m)^\s*\x60([A-Za-z_]\w*)\x60\s+\w+',schema.group(1))
    insert=re.search(r'INSERT\s+INTO\s+\x60?'+re.escape(table)+r'\x60?\s*(?:\([^;]*?\)\s*)?VALUES\s*',sql,re.I|re.S)
    if not insert:continue
    rows=split_rows(sql[insert.end():])
    chosen = {
      'islands':['island_id','name','genes','enabled'],
      'monsters':['monster_id','entity','genes','beds'],
      'entities':['entity_id','entity_type','name','description'],
      'structures':['structure_id','structure_type','entity','upgrades_to'],
      'breeding_combinations':['breeding_combination_id','monster_1','monster_2','result','probability'],
      'quests':['id','name','type','initial','visible'],
      'quest_types':['type_id','name','depricated'],
      'island_monsters':['island_monster_id','island','monster','instrument']
    }[table]
    indices=[cols.index(x) for x in chosen if x in cols]
    labels=[cols[i] for i in indices]
    records=[{key:safe(row[i]) for key,i in zip(labels,indices) if i<len(row)} for row in rows]
    if table=='breeding_combinations':
        preview=records[:8];game[table]={'count':len(rows),'examples':preview,
              'nonzero_probability_count':sum(1 for x in records if (x.get('probability') not in (None,'0','0.0','0.00','0.000','NULL'))),
              'quint_as_result':sum(1 for x in records if x.get('result')=='30'),
              'quint_as_parent':sum(1 for x in records if x.get('monster_1')=='30' or x.get('monster_2')=='30'),
              'quint_possible_breedings':sum(1 for x in records if x.get('result')=='30' and x.get('probability') not in ('0','0.0','0.00','0.000','NULL',''))}
    elif table=='quests':
        game[table]={'count':len(rows),'first':records[:125],'suspicious_names':[x for x in records if re.search('test|debug|dummy|placeholder|unused|legacy',x.get('name',''),re.I)][:40]}
    elif table=='entities':
        game[table]={'count':len(rows),'first':records[:170],'types':sorted(set(x.get('entity_type') or '' for x in records))}
    else:
        game[table]={'count':len(rows),'records':records[:120]}
game['analysed_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
game['note']='Only game data fields from an archived SQL seed; player data not read or published.'
(BASE/'server-2012-game-seed.json').write_text(json.dumps(game,indent=2)+'\n')
lines=['# My Singing Monsters archived 2012-labelled seed data','',
       'Only non-personal game-data IDs and public-facing names; no player records or full SQL code.','']
for tbl,info in game.items():
    if not isinstance(info,dict):continue
    lines+=['## '+tbl+' — '+str(info['count'])+' records','']
    for obj in (info.get('records') or info.get('first') or info.get('examples') or [])[:55]:
        lines+=['- '+', '.join(f'{k}: {v}' for k,v in obj.items())]
    lines+=['']
(BASE/'server-2012-game-seed.md').write_text('\n'.join(lines)+'\n')
for name in ['islands','monsters','entities','quests','quest_types','structures','island_monsters','breeding_combinations']:
    if name in game:
        d=game[name]
        print(name,'count',d['count'])
        print('SAMPLE',json.dumps((d.get('records') or d.get('first') or d.get('examples') or [])[:(35 if name in ('monsters','islands') else 12)])[:6000])
        if d.get('suspicious_names'):print('SUSPICIOUS',d['suspicious_names'][:10])
