import json, collections, itertools
import numpy as np
from scipy import stats
G=[json.loads(l) for l in open('analysis/phase_d_run_archive/scores.jsonl',encoding='utf-8')]
print('gpt5mini score rows',len(G)); print('keys',sorted(G[0].keys()))
print(json.dumps(G[0],indent=1)[:900])
