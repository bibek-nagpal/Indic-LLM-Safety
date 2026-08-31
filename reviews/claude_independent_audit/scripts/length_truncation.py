import json, collections
import numpy as np
from scipy import stats
T=[json.loads(l) for l in open('frozen_final_2026_08_29/run/revision_v2_targets_final/traces.jsonl',encoding='utf-8')]
print('traces',len(T))
S=[json.loads(l) for l in open('frozen_final_2026_08_29/run/revision_v2_targets_final/scores.jsonl',encoding='utf-8')]
SC={(r['pair_id'],r['model'],r['language']):r['score'] for r in S}
fr=collections.Counter()
byml=collections.defaultdict(collections.Counter)
rows=[]
for t in T:
    for lang,k in (('en','english'),('rh','romanized_hindi')):
        b=t[k]; fr[b['finish_reason']]+=1; byml[(t['model'],lang)][b['finish_reason']]+=1
        rows.append(dict(pid=t['pair_id'],model=t['model'],lang=lang,fin=b['finish_reason'],
                         n=len(b['content'] or ''),score=SC[(t['pair_id'],t['model'],lang)]))
print('finish reasons overall',fr)
for k,v in sorted(byml.items()): print('  ',k,dict(v))
import itertools
M=sorted({r['model'] for r in rows})
print('\n--- TRUNCATION (finish_reason=length) by model/language, and score distribution ---')
for m in M:
    for lg in ('en','rh'):
        sub=[r for r in rows if r['model']==m and r['lang']==lg]
        tr=[r for r in sub if r['fin']=='length']
        sd=collections.Counter(r['score'] for r in tr)
        print(f'{m.split("/")[1][:24]:24s} {lg} n_trunc={len(tr):4d}/{len(sub)}  score dist of truncated={dict(sorted(sd.items()))}')
print('\n--- Response length (chars) ---')
for m in M:
    e=np.array([r['n'] for r in rows if r['model']==m and r['lang']=='en'])
    h=np.array([r['n'] for r in rows if r['model']==m and r['lang']=='rh'])
    print(f'{m.split("/")[1][:24]:24s} EN med {np.median(e):7.0f} mean {e.mean():7.0f} | RH med {np.median(h):7.0f} mean {h.mean():7.0f}')
# zero-length / empty
z=[r for r in rows if r['n']==0]
print('\nempty responses:',len(z), collections.Counter((r['model'],r['lang'],r['fin'],r['score']) for r in z))
