import sys, importlib.util, json
from kaggle_environments import make
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.agent if hasattr(m, 'agent') else m.act
cand = load(sys.argv[1], 'cand'); opp = load(sys.argv[2], 'opp')
w = l = t = 0; margins = []
for i in range(int(sys.argv[3])):
    seed = 56000 + i // 2; agents = [cand, opp] if i % 2 == 0 else [opp, cand]
    env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': seed}, debug=False)
    env.run(agents)
    last = env.steps[-1]
    r0 = last[0]['reward'] if isinstance(last[0], dict) else last[0].reward
    r1 = last[1]['reward'] if isinstance(last[1], dict) else last[1].reward
    rc, ro = (r0, r1) if i % 2 == 0 else (r1, r0)
    margins.append(rc - ro)
    w, l, t = w + (rc > ro), l + (rc < ro), t + (rc == ro)
    print(f'game {i+1}: rc={rc} ro={ro}', flush=True)
print(json.dumps({'w': w, 'l': l, 't': t, 'mean_margin': sum(margins)/len(margins)}))
