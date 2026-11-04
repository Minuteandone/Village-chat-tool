#!/usr/bin/env python3
"""Historic MSM SQL schema + game-content row counts + source comment context. Never execute archived files or disclose player records."""
import bisect,collections,datetime,hashlib,io,json,pathlib,re,urllib.parse,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
URL='https://archive.org/download/monster-game-server/monster-game-server.zip'
SHA='df086c9ca4581733f73f2e8aaea1408382232e4d'
class Redirect(urllib.request.HTTPRedirectHandler):
    count=0
    def redirect_request(self,req,fp,code,msg,hdrs,url):
        self.count+=1
        h=urllib.parse.urlsplit(url).hostname or ''
        if self.count>5 or not (h=='archive.org' or h.endswith('.archive.org')) or not url.startswith('https://'):
            raise ValueError('Not an archive redirect')
        return super().redirect_request(req,fp,code,msg,hdrs,url)
req=urllib.request.Request(URL,headers={'User-Agent':'MSM-Historical-Schema-Review/1.0'})
with urllib.request.build_opener(Redirect()).open(req,timeout=80) as resp:
    b=resp.read(20000001)
if len(b)>20000000 or hashlib.sha1(b).hexdigest()!=SHA:raise ValueError('Invalid historical ZIP')
z=zipfile.ZipFile(io.BytesIO(b))
interested={'monsters','islands','breeding_combinations','entities','structures','quest_types','quests','store_groups','store_items','level_xp','island_monsters','island_structures','game_settings'}
private_tables={'users','user_contact_info','user_friends','user_messages','user_monsters','user_islands','user_quests','user_structures'}
method=re.compile(r'\b(?:public|private|protected)\s+(?:(?:static|final|synchronized)\s+)*(?:[\w\[\]<>,.?]+\s+)+([A-Za-z_]\w*)\s*\(',re.M)
marker=re.compile(r'\b(TODO|FIXME|HACK|unused|disabled|unreleased|temporary|testing)\b',re.I)
sensitive=re.compile(r'token|password|credential|secret|auth|account|email|facebook|aws|api.?key|session|server.?url',re.I)
details=[]
for f in z.infolist():
    if not f.filename.endswith('.java') or f.file_size>1000000:continue
    raw=z.read(f).decode('utf-8','replace')
    matches=list(method.finditer(raw))
    at=[raw.count('\n',0,m.start())+1 for m in matches]
    srcname=pathlib.PurePosixPath(f.filename).name
    for i,line in enumerate(raw.splitlines(),1):
        found=list(dict.fromkeys(m.upper() for m in marker.findall(line)))
        if not found or sensitive.search(line) or not (line.lstrip().startswith(('//','/*','*')) or 'TODO' in line or 'FIXME' in line):continue
        ix=bisect.bisect_right(at,i)-1
        last_method=matches[ix].group(1) if ix>=0 else '(class-level)'
        if sensitive.search(last_method):last_method='(redacted)'
        details.append({'file':srcname,'line':i,'nearest_method':last_method,'markers':found})
sql_meta=[]
def count_insert_rows(src,start):
    q=None;escape=False;depth=0;count=0;i=start
    while i<len(src):
        ch=src[i]
        if q:
            if escape:escape=False
            elif ch=='\\':escape=True
            elif ch==q:
                if i+1<len(src) and src[i+1]==q:i+=1
                else:q=None
        elif ch in "'\"":q=ch
        elif ch=='(':
            if depth==0:count+=1
            depth+=1
        elif ch==')':
            depth=max(0,depth-1)
        elif ch==';' and depth==0:break
        i+=1
    return count
for file in z.infolist():
    if not file.filename.endswith('.sql'):continue
    src=z.read(file).decode('utf-8','replace')
    create=re.compile(r'\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?\x60?([A-Za-z_][A-Za-z_0-9]*)\x60?\s*\((.*?)\)\s*(?:ENGINE|TYPE|;)',re.I|re.S)
    schema={}
    for m in create.finditer(src):
        name=m.group(1)
        cols=re.findall(r'(?m)^\s*\x60([A-Za-z_][A-Za-z_0-9]*)\x60\s+\w+',m.group(2))
        if name in private_tables: schema[name]={'column_count':len(cols),'columns':'(not displayed: player records)'}
        else:schema[name]={'column_count':len(cols),'columns':cols[:90]}
    inserts=re.compile(r'\bINSERT\s+INTO\s+\x60?([A-Za-z_][A-Za-z_0-9]*)\x60?\s*(?:\([^;]*?\)\s*)?VALUES\s*',re.I|re.S)
    for m in inserts.finditer(src):
        name=m.group(1)
        if name in schema and name not in private_tables:
            schema[name]['approx_record_count']=schema[name].get('approx_record_count',0)+count_insert_rows(src,m.end())
    sql_meta.append({'name':pathlib.PurePosixPath(file.filename).name,'size':file.file_size,'schema':schema})
out={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':URL,
     'sql_schema_metadata':sql_meta,'development_marker_method_context':details,
     'notes':'Static analysis of archived game code. No database row values, account records or code source bodies exported.'}
(ROOT/'server-gameplay-details.json').write_text(json.dumps(out,indent=2)+'\n')
lines=['# Historical MSM server: SQL game-data schema and development-marker context','',
       'Source: '+URL,'','Code was not executed. Player tables and row data are not reproduced.','']
for item in sql_meta:
    lines+=['## '+item['name'],'']
    for tbl,info in item['schema'].items():
        lines+=['- '+tbl+': '+str(info['column_count'])+' columns, '+str(info.get('approx_record_count','not counted'))+' seed records']
    lines+=['']
lines+=['## Development markers mapped to nearby methods','']
for x in details[:160]:
    lines+=['- '+x['file']+':'+str(x['line'])+' in '+x['nearest_method']+' ('+', '.join(x['markers'])+')']
lines+=['','A marker or a strange method name does not itself indicate scrapped content.']
(ROOT/'server-gameplay-details.md').write_text('\n'.join(lines)+'\n')
for s in sql_meta:
    print('SQL',s['name'])
    for table,meta in s['schema'].items():
        if table in interested:print(' ',table,'rows',meta.get('approx_record_count'),'columns',meta['columns'])
print('MARKER CONTEXT')
for x in details[:95]:print(' ',x['file'],x['line'],x['nearest_method'],x['markers'])
