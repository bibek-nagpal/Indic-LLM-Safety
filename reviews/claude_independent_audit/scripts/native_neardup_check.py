"""Re-check near-duplication using the SAME metric the generation-time gate uses."""
import json, re, itertools, collections
from difflib import SequenceMatcher
P=[json.loads(l) for l in open('frozen_final_2026_08_29/bank/revision_v2_3_1_final_504_dedup/pairs.jsonl',encoding='utf-8')]
def norm(t):
    t=t.lower(); t=re.sub(r"[^a-z0-9\s]"," ",t); return " ".join(t.split())
rows=[{'pid':p['pair_id'],'strat':p['candidate']['strategy'],'cat':p['candidate']['category'],
       'en':norm(p['candidate']['english_prompt']),'rh':norm(p['candidate']['romanized_hindi_prompt'])} for p in P]
by=collections.defaultdict(list)
for r in rows: by[r['strat']].append(r)   # gate screens within strategy, across categories
viol=[]; allsim=[]
for s,v in by.items():
    for a,b in itertools.combinations(v,2):
        sim=max(SequenceMatcher(None,a['en'],b['en']).ratio(), SequenceMatcher(None,a['rh'],b['rh']).ratio())
        allsim.append(sim)
        if sim>=0.85: viol.append((sim,s,a['cat'],b['cat'],a['pid'],b['pid']))
viol.sort(reverse=True)
import numpy as np
a=np.array(allsim)
print(f'within-strategy pairs compared: {len(a)}')
print(f'SequenceMatcher max(EN,RH) ratio: mean={a.mean():.3f} p99={np.percentile(a,99):.3f} max={a.max():.3f}')
print(f'PAIRS AT/ABOVE THE 0.85 GENERATION GATE STILL IN THE FINAL BANK: {len(viol)}')
for s,st,c1,c2,p1,p2 in viol[:20]:
    print(f'  {s:.3f} {st:16s} {c1}/{c2}  {p1} {p2}')
for th in (0.90,0.85,0.80,0.75,0.70):
    print(f'  n(sim>={th:.2f}) = {int((a>=th).sum())}')
