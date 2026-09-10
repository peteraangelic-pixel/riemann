#!/usr/bin/env python3
"""H2H: candidate tape(s) vs opponent(s). Sequential, flush per game, log file."""
import importlib.util, json, sys, time
from pathlib import Path

sys.path.insert(0, "/home/user/riemann/kaggriculture_meta_lab/seat_087c0")
from kaggle_environments import make

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.act if hasattr(m, 'act') else m.agent

def game(a, b, seed, swap):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    if swap:
        env.run([b, a]); r0, r1 = env.state[1].reward, env.state[0].reward
    else:
        env.run([a, b]); r0, r1 = env.state[0].reward, env.state[1].reward
    errs = [s.get('status') for s in env.state]
    return r0, r1, errs

def main():
    cand_files = json.loads(sys.argv[1])   # list of paths
    opp_files = json.loads(sys.argv[2])    # list of paths (usually 1)
    seeds = json.loads(sys.argv[3])        # list of ints
    logpath = sys.argv[4]
    opponents = [load(p, f"opp{i}") for i, p in enumerate(opp_files)]
    log = []
    for cpath in cand_files:
        cand = load(cpath, "cand")
        for opath, opp in zip(opp_files, opponents):
            if Path(cpath).stem == Path(opath).stem:
                continue
            w = l = t = 0; ms = 0.0; sc = so = 0.0; games = []
            for seed in seeds:
                for sw in (0, 1):
                    t0 = time.time()
                    r0, r1, errs = game(cand, opp, seed, sw)
                    if errs and any(e not in ('DONE', 'ACTIVE') for e in errs):
                        print(f"  !! error {cpath} vs {opath} seed {seed} swap {sw}: {errs}", flush=True)
                    if r0 > r1: w += 1
                    elif r0 < r1: l += 1
                    else: t += 1
                    ms += r0 - r1; sc += r0; so += r1
                    games.append({'seed': seed, 'swap': sw, 'r0': r0, 'r1': r1})
                    print(f"{Path(cpath).stem} vs {Path(opath).stem} seed {seed} swap {sw}: {r0:.0f}/{r1:.0f}  [{time.time()-t0:.0f}s]", flush=True)
            n = w + l + t
            line = {"cand": Path(cpath).stem, "opp": Path(opath).stem, "w": w, "l": l, "t": t,
                    "margin_sum": ms, "mean_cand": sc / n, "mean_opp": so / n, "games": games}
            log.append(line)
            print(json.dumps({k: v for k, v in line.items() if k != 'games'}), flush=True)
    Path(logpath).write_text(json.dumps(log, indent=1))

if __name__ == '__main__':
    main()
