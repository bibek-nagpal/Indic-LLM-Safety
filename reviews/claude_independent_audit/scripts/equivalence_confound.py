import json, collections
import numpy as np
from scipy import stats
P=[json.loads(l) for l in open('frozen_final_2026_08_29/bank/revision_v2_3_1_final_504_dedup/pairs.jsonl',encoding='utf-8')]
B={}
for p in P:
    c=p['candidate']
    B[p['pair_id']]=dict(pri=p['primary_audit'].get('score'), sec=p['secondary_audit'].get('score'),
        enl=len(c['english_prompt']), rhl=len(c['romanized_hindi_prompt']),
        cat=c['category'], strat=c['strategy'])
S=[json.loads(l) for l in open('frozen_final_2026_08_29/run/revision_v2_targets_final/scores.jsonl',encoding='utf-8')]
D={(r['pair_id'],r['model'],r['language']):r['score'] for r in S}
pids=sorted(B); M=['qwen/qwen3-30b-a3b-instruct-2507','openai/gpt-oss-20b','nvidia/nemotron-3-nano-30b-a3b']
pri=np.array([B[p]['pri'] for p in pids],float); sec=np.array([B[p]['sec'] for p in pids],float)
ratio=np.array([B[p]['rhl']/B[p]['enl'] for p in pids])
print('primary equivalence score: mean %.4f min %.3f  dist %s'%(pri.mean(),pri.min(),collections.Counter(np.round(pri,2)).most_common(6)))
print('secondary equivalence score: mean %.4f min %.3f  dist %s'%(sec.mean(),sec.min(),collections.Counter(np.round(sec,2)).most_common(6)))
print('corr(primary,secondary) = %.3f'%np.corrcoef(pri,sec)[0,1])
print('RH/EN prompt char ratio: mean %.3f sd %.3f min %.2f max %.2f'%(ratio.mean(),ratio.std(),ratio.min(),ratio.max()))
print()
print('Association of PAIR-LEVEL gap contribution (EN_refuse - RH_refuse) with audited equivalence and prompt-length ratio:')
for m in M:
    g=np.array([(D[(p,m,'en')]==0)-(D[(p,m,'rh')]==0) for p in pids],float)
    fwd=np.array([(D[(p,m,'en')]==0)and(D[(p,m,'rh')]>=2) for p in pids],float)
    for name,x in (('sec_equiv',sec),('pri_equiv',pri),('len_ratio',ratio)):
        r1,p1=stats.spearmanr(x,g); r2,p2=stats.spearmanr(x,fwd)
        print(f'  {m.split("/")[1][:22]:22s} {name:9s} rho(gap)={r1:+.3f} p={p1:.3g} | rho(fwd_flip)={r2:+.3f} p={p2:.3g}')
print()
print('Forward-flip rate by RH/EN prompt-length-ratio tercile (Qwen):')
for m in M:
    fwd=np.array([(D[(p,m,'en')]==0)and(D[(p,m,'rh')]>=2) for p in pids],float)
    q=np.quantile(ratio,[1/3,2/3])
    t=np.digitize(ratio,q)
    print(f'  {m.split("/")[1][:22]:22s} ' + '  '.join(f'T{i+1}(ratio<= {"%.2f"%q[i] if i<2 else "max"}) fwd={100*fwd[t==i].mean():.1f}%' for i in range(3)))
