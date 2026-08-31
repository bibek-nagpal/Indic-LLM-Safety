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
cl=clusters(0.55); K=len(cl); print('clusters@0.55:',K)
groups=[np.array([idx[p] for p in c]) for c in cl]
rng=np.random.default_rng(11)
# cluster sign-flip permutation test on mean gap (H0: symmetric within cluster-level sign flip)
def cluster_signflip_p(v,B=100000):
    cs=np.array([v[g].sum() for g in groups]); n=len(v)
    obs=v.mean()
    cnt=0
    for start in range(0,B,5000):
        b=min(5000,B-start)
        s=rng.choice([-1.0,1.0],size=(b,K))
        perm=(s@cs)/n
        cnt+=np.sum(np.abs(perm)>=abs(obs))
    return (cnt+1)/(B+1)
for m in M:
    print(f'{m.split("/")[1]:34s} gap={gap[m].mean()*100:6.2f} cluster-signflip p={cluster_signflip_p(gap[m]):.5g}')
# contrasts
rng2=np.random.default_rng(12)
B=4000
draws=rng2.integers(0,K,size=(B,K))
cn=np.array([len(g) for g in groups],float)
def boot(v):
    cs=np.array([v[g].sum() for g in groups])
    return cs[draws].sum(axis=1)/cn[draws].sum(axis=1)*100
bo={m:boot(gap[m]) for m in M}
for a,b in [(0,1),(0,2),(1,2)]:
    d=bo[M[a]]-bo[M[b]]; lo,hi=np.percentile(d,[2.5,97.5])
    print(f'CONTRAST {M[a].split("/")[1][:10]} - {M[b].split("/")[1][:10]}: {gap[M[a]].mean()*100-gap[M[b]].mean()*100:6.2f} clusterCI [{lo:.2f},{hi:.2f}]')
    v=gap[M[a]]-gap[M[b]]
    print(f'    cluster-signflip p={cluster_signflip_p(v):.5g}')
