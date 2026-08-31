import json, collections
import numpy as np
from scipy import stats
T=[json.loads(l) for l in open('frozen_final_2026_08_29/run/revision_v2_targets_final/traces.jsonl',encoding='utf-8')]
print('raw trace rows',len(T))
k=collections.Counter((t['pair_id'],t['model']) for t in T)
print('unique (pair,model)',len(k),'  rows with >1 trace:',sum(1 for v in k.values() if v>1),' max',max(k.values()))
# dedupe: keep LAST occurrence (the successful retry)
last={}
for i,t in enumerate(T): last[(t['pair_id'],t['model'])]=t
print('after keep-last',len(last))
bad=[key for key,t in last.items() if (t['english'].get('error') or t['romanized_hindi'].get('error') or not (t['english']['content'] or '').strip() or not (t['romanized_hindi']['content'] or '').strip())]
print('kept-last rows still empty/errored:',len(bad))
# also check keep-first
first={}
for t in T: first.setdefault((t['pair_id'],t['model']),t)
badf=[key for key,t in first.items() if (t['english'].get('error') or not (t['english']['content'] or '').strip())]
print('keep-first empty/errored:',len(badf))

S=[json.loads(l) for l in open('frozen_final_2026_08_29/run/revision_v2_targets_final/scores.jsonl',encoding='utf-8')]
SC={(r['pair_id'],r['model'],r['language']):r['score'] for r in S}
rows=[]
for (pid,m),t in last.items():
    for lg,key in (('en','english'),('rh','romanized_hindi')):
        b=t[key]
        rows.append(dict(pid=pid,model=m,lang=lg,fin=b['finish_reason'],n=len(b['content'] or ''),score=SC[(pid,m,lg)]))
M=sorted({r['model'] for r in rows})
print('\n=== finish_reason after dedupe ===')
for m in M:
    for lg in ('en','rh'):
        c=collections.Counter(r['fin'] for r in rows if r['model']==m and r['lang']==lg)
        print(f'{m.split("/")[1][:24]:24s} {lg}: {dict(c)}')
print('\n=== TRUNCATION (finish_reason == "length") ===')
tot=collections.Counter()
for m in M:
    e=[r for r in rows if r['model']==m and r['lang']=='en']; h=[r for r in rows if r['model']==m and r['lang']=='rh']
    te=sum(1 for r in e if r['fin']=='length'); th=sum(1 for r in h if r['fin']=='length')
    # mcnemar on truncation
    de={r['pid']:r['fin']=='length' for r in e}; dh={r['pid']:r['fin']=='length' for r in h}
    b=sum(1 for p in de if de[p] and not dh[p]); c=sum(1 for p in de if dh[p] and not de[p])
    p=stats.binomtest(b,b+c,0.5).pvalue if b+c else 1
    print(f'{m.split("/")[1][:24]:24s} EN trunc {te:3d}/504  RH trunc {th:3d}/504  discordant {b}/{c} p={p:.3g}')
    sc_e=collections.Counter(r['score'] for r in e if r['fin']=='length'); sc_h=collections.Counter(r['score'] for r in h if r['fin']=='length')
    print(f'{"":24s}   truncated EN score dist {dict(sorted(sc_e.items()))} | RH {dict(sorted(sc_h.items()))}')
print('\n=== EMPTY responses after dedupe ===')
z=[r for r in rows if r['n']==0]
print(len(z), collections.Counter((r['model'],r['lang'],r['score']) for r in z))
print('\n=== response char lengths (deduped) ===')
for m in M:
    e=np.array([r['n'] for r in rows if r['model']==m and r['lang']=='en']); h=np.array([r['n'] for r in rows if r['model']==m and r['lang']=='rh'])
    print(f'{m.split("/")[1][:24]:24s} EN med {np.median(e):7.0f} p90 {np.percentile(e,90):7.0f} | RH med {np.median(h):7.0f} p90 {np.percentile(h,90):7.0f}')
# PHASE C recompute
print('\n=== PHASE C recompute (EN<80 & RH>500 forward; mirror reverse) ===')
for m in M:
    e={r['pid']:r['n'] for r in rows if r['model']==m and r['lang']=='en'}
    h={r['pid']:r['n'] for r in rows if r['model']==m and r['lang']=='rh'}
    f=sum(1 for p in e if e[p]<80 and h[p]>500); rv=sum(1 for p in e if h[p]<80 and e[p]>500)
    print(f'{m.split("/")[1][:24]:24s} forward-shaped {f}  reverse-shaped {rv}  p={stats.binomtest(f,f+rv,0.5).pvalue:.3g}')
json.dump([{k:(v if not isinstance(v,np.integer) else int(v)) for k,v in r.items()} for r in rows], open('reviews/claude_independent_audit/scripts/deduped_response_rows.json','w'))
