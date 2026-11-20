import re,sys,collections
D='/home/claude/normcore-cls/docs/'
rd=lambda f: open(D+f,encoding='utf-8').read()
srs,uc,ts,plan,calc=rd('srs.md'),rd('use-cases.md'),rd('test-scenarios.md'),rd('implementation-plan.md'),rd('calculation-rules.md')
reqs=collections.OrderedDict(); dup=[]
for line in srs.splitlines():
    if line.startswith('| FR-'):
        c=[x.strip() for x in line.strip().strip('|').split('|')]
        if c[0] in reqs: dup.append(c[0])
        reqs[c[0]]=dict(short=c[1],prio=c[3],kind='FR')
    elif line.startswith('| NFR-'):
        c=[x.strip() for x in line.strip().strip('|').split('|')]
        if c[0] in reqs: dup.append(c[0])
        s=c[2]; s=s if len(s)<=70 else s[:67].rsplit(' ',1)[0]+'…'
        reqs[c[0]]=dict(short=c[1]+': '+s,prio=c[3],kind='NFR')
idre=re.compile(r'N?FR-[A-Z]+-\d{3}')
def expand(text):
    out=[]
    for m in re.finditer(r'(N?FR-[A-Z]+-)(\d{3})(?:\.\.(\d{3}))?',text):
        a=int(m.group(2)); b=int(m.group(3) or m.group(2))
        out+= [f'{m.group(1)}{i:03d}' for i in range(a,b+1)]
    return out
ucmap=collections.defaultdict(list); cur=None; ucs=[]
for line in uc.splitlines():
    m=re.match(r'### (UC-\d+):',line)
    if m: cur=m.group(1); ucs.append(cur)
    if line.startswith('- **Truy vết:**'):
        for i in idre.findall(line): ucmap[i].append(cur)
tsmap=collections.defaultdict(list); tss=[]
for line in ts.splitlines():
    if line.startswith('| TS-'):
        c=[x.strip() for x in line.strip().strip('|').split('|')]; tss.append(c[0])
        for i in idre.findall(c[-1]): tsmap[i].append(c[0])
planmap=collections.defaultdict(list)
for line in plan.splitlines():
    m=re.match(r'\| (E\d) \|',line)
    if m:
        c=[x.strip() for x in line.strip().strip('|').split('|')]
        for i in expand(c[2]): planmap[i].append(m.group(1))
err=[]
if dup: err.append('DUP '+str(dup))
for name,mp in (('UC',ucmap),('TS',tsmap),('PLAN',planmap)):
    bad=[i for i in mp if i not in reqs]
    if bad: err.append(f'{name} refs unknown: {bad}')
fr=[i for i in reqs if reqs[i]['kind']=='FR']
print('FR',len(fr),'NFR',len(reqs)-len(fr),'UC',len(ucs),'TS',len(tss))
print('by prio',collections.Counter(reqs[i]['prio'] for i in fr))
print('FR no UC:',[i for i in fr if i not in ucmap])
print('FR no plan:',[i for i in fr if i not in planmap])
print('FR multi plan:',[i for i in fr if len(planmap[i])>1])
print('Must FR no TS:',[i for i in fr if reqs[i]['prio']=='M' and i not in tsmap])
print('S/C FR no TS:',[i for i in fr if reqs[i]['prio']!='M' and i not in tsmap])
# rule refs
alltxt=srs+uc+ts+plan
for pre,defs in (('QT',set(re.findall(r'### (QT-\d\d)',calc))),('KT',set(re.findall(r'\| (KT-\d\d) \|',calc))),('TV',set(re.findall(r'\| (TV-\d\d) \|',calc)))):
    used=set(re.findall(pre+r'-\d\d',alltxt+calc))
    print(pre,'defined',len(defs),'undefined refs',sorted(used-defs))
# KT FR column check
for m in re.finditer(r'\| (KT-\d\d) \|.*\| (FR-[A-Z]+-\d{3}) \|',calc):
    if m.group(2) not in reqs: err.append('KT bad FR '+m.group(0))
print('ERR',err)
src=lambda i: 'BA bổ sung theo danh mục chuẩn' if (i.startswith('NFR') or re.match(r'FR-(SEC|AUD|IMP)-',i)) else 'Tài liệu ý tưởng Phân hệ E (13/11/2026)'
out=['# Ma trận truy vết yêu cầu (RTM) – Normcore Phân hệ E','',
'> Nguồn: docs/srs.md, docs/use-cases.md, docs/implementation-plan.md, docs/test-scenarios.md · Cập nhật: 13/11/2026 · Sinh tự động bằng scripts/build_rtm.py.',
'> Cột Design ref và Test ref do các bước thiết kế và nghiệm thu điền sau. Cột Plan ref lấy theo kế hoạch sơ bộ, bước implementation-planning sẽ ghi lại. Cột Kịch bản là kịch bản nghiệm thu dự kiến, chưa phải kết quả kiểm thử.','',
'| Req ID | Yêu cầu (ngắn) | ƯT | Trạng thái | Nguồn | Use case | Design ref | Plan ref | Kịch bản | Test ref |',
'| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |']
for i,r in reqs.items():
    out.append(f"| {i} | {r['short']} | {r['prio']} | Active | {src(i)} | {', '.join(ucmap[i]) or '—'} | _TBD_ | {(', '.join(planmap[i])+' (sơ bộ)') if planmap[i] else '_TBD_'} | {', '.join(tsmap[i]) or '—'} | _TBD_ |")
open(D+'rtm.md','w',encoding='utf-8').write('\n'.join(out)+'\n')
# compact for doc
comp=['| Req ID | Yêu cầu (ngắn) | ƯT | Use case | Epic | Kịch bản |','| --- | --- | --- | --- | --- | --- |']
for i,r in reqs.items():
    comp.append(f"| {i} | {r['short']} | {r['prio']} | {', '.join(ucmap[i]) or '—'} | {', '.join(planmap[i]) or '—'} | {', '.join(tsmap[i]) or '—'} |")
open('/home/claude/normcore-cls/scripts/rtm_compact.md','w',encoding='utf-8').write('\n'.join(comp)+'\n')
import os; print({f:os.path.getsize(D+f) for f in os.listdir(D)})
