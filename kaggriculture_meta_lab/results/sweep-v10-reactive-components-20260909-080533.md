# Sweep: v10-reactive-components
base=agent_v7.py  baseline=agent_v7.py  workers=4
screen=4 seeds, promote=100 seeds, finals=100 seeds, top_k=2
untouched_base_variant=False  finals_control_anchor=True
promotion_objective=balanced

4 configurations:
  reno_labor             {"LABOR_MODE": "RENOIR"}
  subin_herd             {"ANIMAL_TARGET": 12, "ANIMAL_TARGETS": {"COW": 6, "GOOSE": 2, "SHEEP": 4}}
  opponent_adapt         {"ADAPT_COW_THRESHOLD": 4, "ADAPT_SHEEP_THRESHOLD": 4, "OPPONENT_MELON_THRESHOLD": 4}
  reno_subin_herd        {"ANIMAL_TARGET": 12, "ANIMAL_TARGETS": {"COW": 6, "GOOSE": 2, "SHEEP": 4}, "LABOR_MODE": "RENOIR"}

[1/3] SCREEN: 4 variants x 4 seeds x 2 seats = 32 games ...

  variant                    W-L-T  score%      Wilson95   margin err
  reno_labor                 2-6-0    25.0          7-59     -810   0
  subin_herd                 2-6-0    25.0          7-59    -3388   0
  reno_subin_herd            0-8-0     0.0          0-32    -3102   0
  opponent_adapt             0-8-0     0.0          0-32   -10624   0


elapsed 66s
