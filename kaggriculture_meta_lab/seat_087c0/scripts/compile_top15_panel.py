#!/usr/bin/env python3
"""Compile one best-reward tape per TOP15 team from TOP15.7z.

Per team folder: read manifest.json (rank, team_name, leaderboard_score)
and all replay_*.json; identify the team's seat via info.TeamNames;
take actions from steps[1:] (719) and final reward from top-level
rewards[seat]. The replay with max team reward becomes the team's tape
(single-stream module in this seat's hardened format).

Outputs: <outdir>/<slug>_top15.py x 15 + panel.json with provenance.
"""
import io
import json
import re
import sys
import zipfile
from pathlib import Path

EMPTY = {"farmer": ["PASS"], "hands": [], "market": []}


def slug(name):
    s = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()
    return s or "team"


def main():
    archive, outdir = Path(sys.argv[1]), Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    import py7zr
    z = py7zr.SevenZipFile(archive, "r")
    names = z.getnames()
    teams = sorted({n.split("/")[1] for n in names
                    if n.startswith("TOP15/") and n.count("/") >= 2
                    and not n.endswith("manifest.json")
                    and n.split("/")[1] != "manifest.json"})
    panel = []
    for team in teams:
        elle = [n for n in names if n.startswith(f"TOP15/{team}/replay_")]
        man_name = f"TOP15/{team}/manifest.json"
        meta = {}
        if man_name in names:
            tmp = outdir / "_tmpman.json"
            zz = py7zr.SevenZipFile(archive, "r")
            zz.extract(path=str(outdir), targets=[man_name])
            meta = json.loads((outdir / man_name).read_text())
            (outdir / man_name).unlink()
        best = None
        for ename in sorted(elle):
            tmpf = outdir / "_tmprep.json"
            zz = py7zr.SevenZipFile(archive, "r")
            zz.extract(path=str(outdir), targets=[ename])
            # extract nests TOP15/<team>/... under outdir
            got = outdir / ename
            d = json.loads(got.read_text())
            got.unlink()
            tns = (d.get("info") or {}).get("TeamNames", [])
            seat = next((i for i, t in enumerate(tns)
                         if t.casefold() == team.casefold()), None)
            if seat is None:
                # fall back: team folder name may differ in case/alias
                seat = next((i for i, t in enumerate(tns)
                             if slug(t) == slug(team)), None)
            if seat is None:
                print(f"  !! {team}: seat not found in {ename.split('/')[-1]} (teams={tns})")
                continue
            acts = [(row[seat].get("action") if isinstance(row, list) and len(row) > seat else None)
                    or dict(EMPTY) for row in d["steps"][1:]]
            rew = (d.get("rewards") or [None, None])[seat]
            opp = tns[1 - seat] if len(tns) == 2 else "?"
            status = (d.get("statuses") or [None, None])[seat]
            cand = {"file": ename.split("/")[-1], "seat": seat, "reward": rew,
                    "opp": opp, "status": status, "actions": acts}
            if best is None or (rew or -1) > (best["reward"] or -1):
                best = cand
        assert best is not None, f"no usable replay for {team}"
        assert len(best["actions"]) == 719, (team, len(best["actions"]))
        blob_src = json.dumps(best["actions"], separators=(",", ":"))
        import base64
        import zlib
        blob = base64.b85encode(zlib.compress(blob_src.encode(), 9)).decode()
        doc = (f"TOP15 panel tape: {team} (rank {meta.get('rank')}, "
               f"lb {meta.get('leaderboard_score')}).\n\nBest of {len(elle)} newest "
               f"episodes: {best['file']} seat {best['seat']} reward {best['reward']} "
               f"vs {best['opp']} ({best['status']}). Frozen LAB opponent; "
               f"compiled by compile_top15_panel.py.")
        src = (f'"""{doc}"""\nimport base64, copy, json, zlib\n'
               f"_BLOB = {blob!r}\n"
               "_ACTIONS = json.loads(zlib.decompress(base64.b85decode(_BLOB)).decode())\n\n"
               "def _safe_pass(observation):\n"
               "    try:\n"
               '        p = int(observation.get("player", 0))\n'
               '        hands = ((observation.get("farms") or [])[p] or {}).get("hands") or []\n'
               "        n = len(hands)\n"
               "    except Exception:\n"
               "        n = 0\n"
               '    return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}\n\n'
               "def agent(observation, configuration=None):\n"
               "    try:\n"
               '        step = min(int(observation.get("step", 0)), len(_ACTIONS) - 1)\n'
               "        action = copy.deepcopy(_ACTIONS[step])\n"
               '        p = int(observation.get("player", 0))\n'
               '        hands = ((observation.get("farms") or [])[p] or {}).get("hands") or []\n'
               '        action["hands"] = action.get("hands", [])[:len(hands)]\n'
               "        return action\n"
               "    except Exception:\n"
               "        return _safe_pass(observation)\n\n"
               "def act(observation, configuration=None):\n"
               "    return agent(observation, configuration)\n")
        (outdir / f"{slug(team)}_top15.py").write_text(src)
        panel.append({"team": team, "slug": slug(team), "rank": meta.get("rank"),
                      "lb_score": meta.get("leaderboard_score"), "file": best["file"],
                      "seat": best["seat"], "reward": best["reward"],
                      "opp": best["opp"], "status": best["status"]})
        print(f"{team}: {best['file']} s{best['seat']} r={best['reward']} vs {best['opp']}")
    (outdir / "panel.json").write_text(json.dumps(panel, indent=1))
    print(f"wrote {len(panel)} tapes + panel.json")


if __name__ == "__main__":
    main()
