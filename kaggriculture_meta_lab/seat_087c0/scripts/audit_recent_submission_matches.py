#!/usr/bin/env python3
"""Read-only audit of episodes belonging to selected Kaggriculture submissions."""
from __future__ import annotations
import argparse, json, os, tempfile, zipfile
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--submissions', required=True, help='JSON list of submission ids')
    ap.add_argument('--output', type=Path, required=True)
    a=ap.parse_args(); wanted={int(x) for x in json.loads(a.submissions)}
    token=''.join(os.environ.get('KAGGLE_API_TOKEN','').split())
    if not token: raise SystemExit('KAGGLE_API_TOKEN missing')
    os.environ['KAGGLE_API_TOKEN']=token
    import pandas as pd
    from kaggle import api
    with tempfile.TemporaryDirectory(prefix='kg-eps-') as td:
        api.dataset_download_files('georgymamarin/kaggriculture-episodes', path=td, quiet=True)
        zips=list(Path(td).glob('*.zip'))
        if zips:
            with zipfile.ZipFile(zips[0]) as z: z.extractall(td)
        agents=pd.read_csv(Path(td)/'agents.csv')
        eps=pd.read_csv(Path(td)/'episodes.csv')
        mine=agents[agents.submission_id.isin(wanted)].copy()
        selected=set(mine.episode_id.astype(int))
        all_rows=agents[agents.episode_id.isin(selected)].copy()
        # Preserve all available public columns; convert NaN to null through JSON roundtrip.
        matches=[]
        eps_by={int(r['episode_id']):r for r in eps.to_dict('records')}
        for eid, group in all_rows.groupby('episode_id'):
            rows=group.to_dict('records'); ours=[r for r in rows if int(r['submission_id']) in wanted]
            if not ours: continue
            own=ours[0]; opponents=[r for r in rows if r is not own and int(r.get('agent_index',-1)) != int(own.get('agent_index',-2))]
            opp=opponents[0] if opponents else {}
            ob=own.get('final_bank'); xb=opp.get('final_bank')
            outcome=None
            try: outcome='W' if ob>xb else ('L' if ob<xb else 'T')
            except Exception: pass
            matches.append({'episode_id':int(eid),'submission_id':int(own['submission_id']),
              'seat':int(own.get('agent_index',-1)),'final_bank':ob,'rating_after':own.get('rating_after'),
              'opponent_submission_id':opp.get('submission_id'),'opponent_team_id':opp.get('team_id'),
              'opponent_final_bank':xb,'outcome':outcome,'episode':eps_by.get(int(eid),{})})
        summary={}
        for sid in sorted(wanted):
            mm=[m for m in matches if m['submission_id']==sid]
            summary[str(sid)]={'matches':len(mm),'w':sum(m['outcome']=='W' for m in mm),
              'l':sum(m['outcome']=='L' for m in mm),'t':sum(m['outcome']=='T' for m in mm),
              'seat0':sum(m['seat']==0 for m in mm),'seat1':sum(m['seat']==1 for m in mm),
              'latest_rating':next((m['rating_after'] for m in reversed(mm) if m.get('rating_after') is not None),None)}
        report={'as_of_utc':datetime.now(timezone.utc).isoformat(),'mode':'read-only',
                'dataset':'georgymamarin/kaggriculture-episodes','submission_ids':sorted(wanted),
                'summary':summary,'matches':matches}
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda x: None if pd.isna(x) else x))
        print(json.dumps(summary,indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
