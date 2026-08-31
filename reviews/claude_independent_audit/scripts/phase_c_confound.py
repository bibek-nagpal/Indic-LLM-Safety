import json, collections
import numpy as np
from scipy import stats
rows=json.load(open('reviews/claude_independent_audit/scripts/deduped_response_rows.json'))
D={(r['pid'],r['model'],r['lang']):r for r in rows}
pids=sorted({r['pid'] for r in rows}); M=sorted({r['model'] for r in rows})
print("Does the Phase C 'length asymmetry' survive restricting to pairs the judge calls SAFE in BOTH languages?")
print("(If EN<80 & RH>500 shapes appear among EN=0 & RH=0 pairs, length tracks verbosity, not safety.)\n")
for m in M:
    both0=[p for p in pids if D[(p,m,'en')]['score']==0 and D[(p,m,'rh')]['score']==0]
    f=sum(1 for p in both0 if D[(p,m,'en')]['n']<80 and D[(p,m,'rh')]['n']>500)
    r=sum(1 for p in both0 if D[(p,m,'rh')]['n']<80 and D[(p,m,'en')]['n']>500)
    p=stats.binomtest(f,f+r,0.5).pvalue if f+r else 1.0
    # full
    F=sum(1 for q in pids if D[(q,m,'en')]['n']<80 and D[(q,m,'rh')]['n']>500)
    R=sum(1 for q in pids if D[(q,m,'rh')]['n']<80 and D[(q,m,'en')]['n']>500)
    print(f'{m.split("/")[1][:24]:24s} ALL pairs {F:3d}:{R:3d}  |  concordant-SAFE pairs (n={len(both0):3d}) {f:3d}:{r:3d}  p={p:.3g}')
print()
print('Overall verbosity by language (median chars, ALL responses incl. safe ones):')
for m in M:
    e=np.array([D[(p,m,"en")]["n"] for p in pids]); h=np.array([D[(p,m,"rh")]["n"] for p in pids])
    w=stats.wilcoxon(e,h)
    print(f'  {m.split("/")[1][:24]:24s} EN {np.median(e):6.0f}  RH {np.median(h):6.0f}  paired Wilcoxon p={w.pvalue:.3g}')
print()
print('Verbosity among concordant-SAFE (both score 0) only:')
for m in M:
    both0=[p for p in pids if D[(p,m,'en')]['score']==0 and D[(p,m,'rh')]['score']==0]
    e=np.array([D[(p,m,"en")]["n"] for p in both0]); h=np.array([D[(p,m,"rh")]["n"] for p in both0])
    if len(e)>10:
        w=stats.wilcoxon(e,h)
        print(f'  {m.split("/")[1][:24]:24s} n={len(both0):3d} EN {np.median(e):6.0f}  RH {np.median(h):6.0f}  p={w.pvalue:.3g}')
