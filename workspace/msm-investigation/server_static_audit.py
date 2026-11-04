#!/usr/bin/env python3
"""Static public MSM backend ZIP inspection. Never execute archived code."""
import collections,datetime,hashlib,io,json,pathlib,re,urllib.parse,urllib.request,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
URL='https://archive.org/download/monster-game-server/monster-game-server.zip'
HASH='df086c9ca4581733f73f2e8aaea1408382232e4d'
class Redirect(urllib.request.HTTPRedirectHandler):
    count=0
    def redirect_request(self,req,fp,code,msg,hdrs,url):
        self.count+=1
        host=urllib.parse.urlsplit(url).hostname or ''
        if self.count>5 or not (host=='archive.org' or host.endswith('.archive.org')) or not url.startswith('https://'):
            raise RuntimeError('Redirect is not within Internet Archive')
        return super().redirect_request(req,fp,code,msg,hdrs,url)
def main():
    req=urllib.request.Request(URL,headers={'User-Agent':'MSM-Public-Historical-Code-Audit/1.0'})
    with urllib.request.build_opener(Redirect()).open(req,timeout=90) as res:
        data=res.read(20000001)
    if len(data)>20000000 or hashlib.sha1(data).hexdigest()!=HASH:
        raise ValueError('Wrong archive size or SHA1')
    z=zipfile.ZipFile(io.BytesIO(data))
    METHOD=re.compile(r'\b(?:public|private|protected)\s+(?:(?:static|final|synchronized|native|abstract)\s+)*(?:[\w\[\]<>,.?]+\s+)+([A-Za-z_]\w*)\s*\(',re.M)
    FLAG=re.compile(r'\b(?:TODO|FIXME|HACK|XXX|unimplemented|temporary|unused|disabled|unreleased|deprecated|legacy|testing)\b',re.I)
    SENSITIVE=re.compile(r'token|password|secret|credential|auth|account|email|facebook|google|aws|access.?key|private|session|endpoint|host|server.?address',re.I)
    IMPORTANT=['MSMExtension.java','GameStateHandler.java','MSMServerEventHandler.java','Monster.java','MonsterLookup.java','BreedingLookup.java','MemoryMinigameFunctions.java','ScratchTicketFunctions.java','TribalQuestLookup.java','MonsterRareData.java','MSMAdminCatchUnreleasedAccount.java','PlayerMonster.java','PlayerIsland.java','QuestLookup.java','PromoLookup.java','ShortenedFuzingList.java','PlayerEgg.java','PlayerFuzeBuddy.java']
    classes={};flags=[]
    for file in z.infolist():
        if not file.filename.endswith('.java') or file.file_size>1500000:continue
        source=z.read(file).decode('utf-8','replace')
        name=pathlib.PurePosixPath(file.filename).name
        classes[name]={'bytes':file.file_size,'methods':list(dict.fromkeys(METHOD.findall(source)))}
        for i,line in enumerate(source.splitlines(),1):
            marks=sorted(set(x.upper() for x in FLAG.findall(line)))
            if not marks or SENSITIVE.search(line):continue
            if line.strip().startswith(('//','/*','*')) or 'TODO' in line or 'FIXME' in line:
                flags.append({'file':name,'line':i,'markers':marks})
    sql=[]
    for f in z.infolist():
        if not f.filename.endswith('.sql') or f.file_size>1000000:continue
        src=z.read(f).decode('utf-8','replace')
        names=re.findall(r'(?im)\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?\x60?([A-Za-z_]\w*)\x60?',src)
        statements=collections.Counter(re.findall(r'(?im)\bINSERT\s+INTO\s+\x60?([A-Za-z_]\w*)\x60?',src))
        sql.append({'file':pathlib.PurePosixPath(f.filename).name,'tables':names,'insert_statement_counts':dict(statements)})
    out={'archive_url':URL,'verified_sha1':HASH,'archive_bytes':len(data),'java_count':len(classes),
         'selected_classes':{k:{'bytes':v['bytes'],'methods':[m for m in v['methods'] if not SENSITIVE.search(m)]} for k,v in classes.items() if k in IMPORTANT},
         'other_java_files':sorted(set(classes)-set(IMPORTANT)), 'sql_schemas':sql,
         'comment_flag_count':len(flags),'comment_flags':flags[:180],
         'file_years':dict(collections.Counter(str(f.date_time[0]) for f in z.infolist() if not f.is_dir())),
         'inspected_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'safety':'Only names/metadata; no extracted code, SQL records, credentials, or connection details.'}
    (ROOT/'server-static-audit.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    lines=['# Archived MSM server source: static review','','ZIP hash verified. No server code executed or republished.','',
            'Java source files: '+str(len(classes)),'Archive size: '+str(len(data))+' bytes','','## Game-system method names','']
    for k,v in sorted(out['selected_classes'].items()):
        lines+=['### '+k,'',', '.join(v['methods'][:80]),'']
    lines+=['## SQL tables','']
    for s in sql:lines+=['### '+s['file'],'',', '.join(s['tables']),'']
    lines+=['## Development marker locations','']
    for f in flags[:100]:lines+=['- '+f['file']+':'+str(f['line'])+' ('+', '.join(f['markers'])+')']
    lines+=['','These identifiers alone do not prove that a feature was cut or unfinished.']
    (ROOT/'server-static-audit.md').write_text('\n'.join(lines)+'\n')
    print('VERIFIED',len(data),'BYTES',len(classes),'JAVA SOURCES')
    for s in sql:print('SQL',s['file'],len(s['tables']),'TABLES',s['tables'][:100])
    for k,v in sorted(out['selected_classes'].items()):print('CLASS',k,','.join(v['methods'][:50]))
    print('FLAGS',len(flags),dict(collections.Counter(x for f in flags for x in f['markers'])))
if __name__=='__main__':main()
