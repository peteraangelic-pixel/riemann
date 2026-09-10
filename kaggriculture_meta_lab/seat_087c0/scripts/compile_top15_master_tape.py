#!/usr/bin/env python3
"""Compile open-loop master tapes from a TOP15 replay corpus (correct alignment).

Usage: python3 compile_top15_master_tape.py [corpus_dir]  (default /tmp/top15/TOP15)
The replay corpus itself is not committed (user-supplied TOP15.7z).

Mapping (empirically verified on SpaTaro replay_07_107210201: exact 144820/131575
reproduction): replay row zero is initialization; the action executed at step N
is recorded in row N+1 (rows[min(N+1, n_rows-1)]). Agent ignores seat and always
returns the recorded team seat's stream (duplicated), exactly like the audited
lab backend (rust_backend._source / agents._make_tape on this corpus).
"""
import copy, json, glob, os, re, sys
from pathlib import Path

CORPUS = Path('/tmp/top15/TOP15')
OUT = Path('/tmp/tapec/agents')
OUT.mkdir(parents=True, exist_ok=True)

def load(p):
    return json.load(open(p))

def seats_of(replay, team_name):
    names = replay.get('info', {}).get('TeamNames') or []
    seats = [i for i, n in enumerate(names) if n == team_name]
    return seats

def extract_actions(replay, seat):
    steps = replay['steps']
    out = []
    for row in steps[1:]:
        a = row[seat].get('action') if isinstance(row, list) and len(row) > seat else None
        if isinstance(a, dict):
            out.append({
                'farmer': list(a.get('farmer', ['PASS'])),
                'hands': copy.deepcopy(a.get('hands', [])),
                'market': copy.deepcopy(a.get('market', [])),
            })
        else:
            out.append({'farmer': ['PASS'], 'hands': [], 'market': []})
    return out

def slug(name):
    return re.sub(r'[^0-9A-Za-z]+', '_', name).strip('_').lower()

chosen = {}
for mpath in sorted(glob.glob(str(CORPUS / '*/manifest.json'))):
    m = load(mpath)
    team = m['team_name']
    best = max(m['active_submissions'], key=lambda s: s['public_score'])
    eps = [e for e in m['selected_episodes'] if e['submission_id'] == best['submission_id']]
    best_ep = None; best_rew = -1e18; best_seat = None
    for e in eps:
        rp = CORPUS / m['folder'] / e['file']
        r = load(rp)
        seats = seats_of(r, team)
        if len(seats) == 1:
            seat = seats[0]
        elif seats == [0, 1]:
            seat = 0
        else:
            continue
        rew = float(r['steps'][-1][seat].get('reward') or 0.0)
        if rew > best_rew:
            best_rew = rew; best_ep = e; best_seat = seat; best_replay = rp
    assert best_ep is not None, team
    r = load(best_replay)
    actions = extract_actions(r, best_seat)
    name = slug(team)
    # small module; actions inline JSON
    body = '''"""Open-loop tape: %s (rank %d, best-listed sub %d, public %.1f).

Episode %d (file %s), recorded seat %d, reward %.0f. Compiled with replay
row alignment step N -> row N+1 (verified exact on SpaTaro 107210201).
"""
import copy
_ACTIONS = %s

def agent(observation, configuration=None):
    # _ACTIONS = replay rows 1..N; action for observed step s is row s+1,
    # i.e. _ACTIONS index s (clamped).
    step = min(int(observation.get("step", 0)), len(_ACTIONS) - 1)
    return copy.deepcopy(_ACTIONS[step])

def act(observation, configuration=None):
    return agent(observation, configuration)
''' % (team, m['rank'], best['submission_id'], best['public_score'],
       best_ep['episode_id'], best_ep['file'], best_seat, best_rew,
       json.dumps(actions, separators=(',', ':')))
    out = OUT / (name + '.py')
    out.write_text(body)
    chosen[name] = {'team': team, 'rank': m['rank'], 'sub': best['submission_id'],
                    'score': best['public_score'], 'episode': best_ep['episode_id'],
                    'file': best_ep['file'], 'seat': best_seat, 'reward': best_rew,
                    'n_actions': len(actions), 'path': str(out)}
    print('%-16s rank %-2d rew %8.0f  %s' % (name, m['rank'], best_rew, best_ep['file']), flush=True)

json.dump(chosen, open('/tmp/tapec/chosen.json', 'w'), indent=1)
print('total teams:', len(chosen))
