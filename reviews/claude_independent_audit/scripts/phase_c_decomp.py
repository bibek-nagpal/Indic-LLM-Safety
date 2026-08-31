import json
import numpy as np
from scipy import stats
rows=json.load(open('reviews/claude_independent_audit/scripts/deduped_response_rows.json'))
D={(r['pid'],r['model'],r['lang']):r for r in rows}
pids=sorted({r['pid'] for r in rows}); M=['qwen/qwen3-30b-a3b-instruct-2507','openai/gpt-oss-20b','nvidia/nemotron-3-nano-30b-a3b']
def strat(p,m):
    e=D[(p,m,'en')]['score']; h=D[(p,m,'rh')]['score']
    if e==0 and h==0: return 'both-safe (0/0)'
    if e==0 and h>=2: return 'forward flip'
    if h==0 and e>=2: return 'reverse flip'
    return 'other'
print(f'{"model":24s} {"stratum":18s} {"n":>5} {"fwd-shape":>9} {"rev-shape":>9}')
for m in M:
    for s in ['both-safe (0/0)','forward flip','reverse flip','other']:
        sub=[p for p in pids if strat(p,m)==s]
        f=sum(1 for p in sub if D[(p,m,'en')]['n']<80 and D[(p,m,'rh')]['n']>500)
        r=sum(1 for p in sub if D[(p,m,'rh')]['n']<80 and D[(p,m,'en')]['n']>500)
        print(f'{m.split("/")[1][:24]:24s} {s:18s} {len(sub):5d} {f:9d} {r:9d}')
    print()
