import json, re, collections, itertools
import numpy as np
P=[json.loads(l) for l in open('frozen_final_2026_08_29/bank/revision_v2_3_1_final_504_dedup/pairs.jsonl',encoding='utf-8')]
rows={p['pair_id']:p['candidate'] for p in P}; pids=sorted(rows)
def toks(s): return set(re.findall(r"[a-z']+", s.casefold()))
T={p:toks(rows[p]['english_prompt']) for p in pids}; TR={p:toks(rows[p]['romanized_hindi_prompt']) for p in pids}
def jac(a,b,D):
    A,B=D[a],D[b]; return len(A&B)/max(1,len(A|B))
def clusters(th):
    par={p:p for p in pids}
    def f(x):
        while par[x]!=x: par[x]=par[par[x]]; x=par[x]
        return x
    for a,b in itertools.combinations(pids,2):
        if jac(a,b,T)>=th or jac(a,b,TR)>=th:
            ra,rb=f(a),f(b)
            if ra!=rb: par[rb]=ra
    g=collections.defaultdict(list)
    for p in pids: g[f(p)].append(p)
    return list(g.values())
S=[json.loads(l) for l in open('frozen_final_2026_08_29/run/revision_v2_targets_final/scores.jsonl',encoding='utf-8')]
D={(r['pair_id'],r['model'],r['language']):r['score'] for r in S}
M=['qwen/qwen3-30b-a3b-instruct-2507','openai/gpt-oss-20b','nvidia/nemotron-3-nano-30b-a3b']
gap={m:np.array([(D[(p,m,'en')]==0)-(D[(p,m,'rh')]==0) for p in pids],float) for m in M}
idx={p:i for i,p in enumerate(pids)}
print(f'{"th":>5} {"K":>5} | {"GPTOSS gap p":>14} | {"GPTOSS-NEMO CI":>22} {"p":>9}')
for th in [1.01,0.80,0.70,0.65,0.60,0.55,0.50,0.45]:
    cl=[[p] for p in pids] if th>1 else clusters(th)
    K=len(cl); groups=[np.array([idx[p] for p in c]) for c in cl]
    rng=np.random.default_rng(3)
    def sf(v,B=50000):
        cs=np.array([v[g].sum() for g in groups]); n=len(v); obs=v.mean(); cnt=0
        for s0 in range(0,B,5000):
            b=min(5000,B-s0); s=rng.choice([-1.0,1.0],size=(b,K))
            cnt+=np.sum(np.abs((s@cs)/n)>=abs(obs))
        return (cnt+1)/(B+1)
    r2=np.random.default_rng(4); Bt=4000
    draws=r2.integers(0,K,size=(Bt,K)); cn=np.array([len(g) for g in groups],float)
    def boot(v):
        cs=np.array([v[g].sum() for g in groups]); return cs[draws].sum(axis=1)/cn[draws].sum(axis=1)*100
    d=boot(gap[M[1]])-boot(gap[M[2]]); lo,hi=np.percentile(d,[2.5,97.5])
    p_go=sf(gap[M[1]]); p_c=sf(gap[M[1]]-gap[M[2]])
    print(f'{th:5} {K:5d} | {p_go:14.5g} | [{lo:8.2f},{hi:8.2f}] {p_c:9.4g}')
