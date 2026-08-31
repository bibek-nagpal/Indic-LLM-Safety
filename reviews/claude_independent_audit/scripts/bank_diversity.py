import json, re, unicodedata, collections, itertools, statistics
import numpy as np
P=[json.loads(l) for l in open('frozen_final_2026_08_29/bank/revision_v2_3_1_final_504_dedup/pairs.jsonl',encoding='utf-8')]
rows=[]
for p in P:
    c=p['candidate']
    rows.append(dict(pid=p['pair_id'],cat=c['category'],strat=c['strategy'],
                     en=c['english_prompt'],rh=c['romanized_hindi_prompt']))
def norm(s): return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',s).casefold()).strip()
print('unique pair_ids',len({r["pid"] for r in rows}))
print('unique norm EN',len({norm(r["en"]) for r in rows}))
print('unique norm RH',len({norm(r["rh"]) for r in rows}))
# lengths
enl=np.array([len(r['en']) for r in rows]); rhl=np.array([len(r['rh']) for r in rows])
enw=np.array([len(r['en'].split()) for r in rows]); rhw=np.array([len(r['rh'].split()) for r in rows])
print(f'EN chars mean {enl.mean():.1f} med {np.median(enl):.0f}  RH chars mean {rhl.mean():.1f} med {np.median(rhl):.0f}')
print(f'EN words mean {enw.mean():.1f}  RH words mean {rhw.mean():.1f}')
from scipy import stats
print('paired wilcoxon chars', stats.wilcoxon(enl,rhl))
print('mean RH/EN char ratio', (rhl/enl).mean(), 'median', np.median(rhl/enl))

def toks(s): return set(re.findall(r"[a-z']+", s.casefold()))
def jac(a,b):
    A,B=toks(a),toks(b); return len(A&B)/max(1,len(A|B))
# Hinglish-ness: fraction of RH tokens that are also English-dictionary-ish (appear in EN prompt corpus)
en_vocab=collections.Counter()
for r in rows: en_vocab.update(re.findall(r"[a-z']+", r['en'].casefold()))
shared=[]
for r in rows:
    t=re.findall(r"[a-z']+", r['rh'].casefold())
    if t: shared.append(sum(1 for w in t if en_vocab[w]>=3)/len(t))
print(f'RH tokens that are common English corpus tokens: mean {np.mean(shared)*100:.1f}%  (proxy for code-switch depth)')

# within-cell EN-EN similarity
cells=collections.defaultdict(list)
for r in rows: cells[(r['cat'],r['strat'])].append(r)
allsim=[]; cellsim={}
for k,v in cells.items():
    s=[jac(a['en'],b['en']) for a,b in itertools.combinations(v,2)]
    cellsim[k]=(np.mean(s),np.max(s),sum(1 for x in s if x>0.6))
    allsim+=s
print()
print('WITHIN-CELL English-prompt Jaccard similarity (42 prompts/cell, 861 pairs each):')
for k,(m,mx,n6) in sorted(cellsim.items()): print(f'  {k[0]:17s} {k[1]:16s} mean={m:.3f} max={mx:.3f} n(sim>0.6)={n6}')
print(f'  ALL within-cell mean={np.mean(allsim):.3f}')
# cross-cell baseline
import random
random.seed(0)
bl=[jac(random.choice(rows)['en'],random.choice(rows)['en']) for _ in range(5000)]
print(f'  random cross-bank baseline mean={np.mean(bl):.3f}')
# top most-similar EN pairs overall
best=[]
for k,v in cells.items():
    for a,b in itertools.combinations(v,2):
        j=jac(a['en'],b['en'])
        if j>0.62: best.append((j,k,a['en'][:110],b['en'][:110]))
best.sort(reverse=True)
print(f'\nn EN prompt pairs with Jaccard>0.62 within cell: {len(best)}')
for j,k,a,b in best[:8]:
    print(f'  {j:.3f} {k}\n     A: {a}\n     B: {b}')
