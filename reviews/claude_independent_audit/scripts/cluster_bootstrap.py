import json, re, collections, itertools
import numpy as np
P=[json.loads(l) for l in open('frozen_final_2026_08_29/bank/revision_v2_3_1_final_504_dedup/pairs.jsonl',encoding='utf-8')]
rows={p['pair_id']:p['candidate'] for p in P}
pids=sorted(rows)
def toks(s): return set(re.findall(r"[a-z']+", s.casefold()))
T={p:toks(rows[p]['english_prompt']) for p in pids}
TR={p:toks(rows[p]['romanized_hindi_prompt']) for p in pids}
def jac(a,b,D): 
    A,B=D[a],D[b]; return len(A&B)/max(1,len(A|B))

def clusters(th):
    parent={p:p for p in pids}
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def uni(a,b):
        ra,rb=find(a),find(b)
        if ra!=rb: parent[rb]=ra
    for a,b in itertools.combinations(pids,2):
        if jac(a,b,T)>=th or jac(a,b,TR)>=th: uni(a,b)
    g=collections.defaultdict(list)
    for p in pids: g[find(p)].append(p)
    return list(g.values())

S=[json.loads(l) for l in open('frozen_final_2026_08_29/run/revision_v2_targets_final/scores.jsonl',encoding='utf-8')]
D={(r['pair_id'],r['model'],r['language']):r['score'] for r in S}
MODELS=['qwen/qwen3-30b-a3b-instruct-2507','openai/gpt-oss-20b','nvidia/nemotron-3-nano-30b-a3b']
gapvec={m:np.array([ (D[(p,m,'en')]==0) - (D[(p,m,'rh')]==0) for p in pids],dtype=float) for m in MODELS}

print(f'{"thresh":>7} {"n_clusters":>10} {"largest":>7} ' + ' '.join(f'{m.split("/")[1][:12]:>26}' for m in MODELS))
rng=np.random.default_rng(7)
for th in [1.01,0.75,0.65,0.55,0.45]:
    if th>1:
        cl=[[p] for p in pids]
    else:
        cl=clusters(th)
    K=len(cl)
    idxmap=[[pids.index(p) for p in c] for c in cl]
    out=[]
    for m in MODELS:
        v=gapvec[m]
        # cluster bootstrap
        B=4000
        draws=rng.integers(0,K,size=(B,K))
        cs=np.array([v[ix].sum() for ix in idxmap]); cn=np.array([len(ix) for ix in idxmap],dtype=float)
        num=cs[draws].sum(axis=1); den=cn[draws].sum(axis=1)
        est=num/den*100
        lo,hi=np.percentile(est,[2.5,97.5])
        out.append(f'{v.mean()*100:7.2f} [{lo:6.2f},{hi:6.2f}]')
    print(f'{th:7} {K:10d} {max(len(c) for c in cl):7d} ' + ' '.join(f'{o:>26}' for o in out))
