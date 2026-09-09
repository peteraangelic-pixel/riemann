# Sweep: v10-reactive-subin-ablation
base=agent_v10_reactive_subin.py  baseline=agent_v7.py  workers=4
screen=4 seeds, promote=100 seeds, finals=100 seeds, top_k=3
untouched_base_variant=True  finals_control_anchor=False
promotion_objective=balanced

5 configurations:
  opening_off            {"SUBIN_OPENING_STEPS": 0}
  adaptation_off         {"ADAPT_COW_THRESHOLD": 999, "ADAPT_SHEEP_THRESHOLD": 999, "OPPONENT_MELON_THRESHOLD": 999}
  labor_auto             {"LABOR_MODE": "AUTO"}
  v7_herd                {"ANIMAL_TARGET": 14, "ANIMAL_TARGETS": {"COW": 8, "SHEEP": 6}}
  opening_only           {"ADAPT_COW_THRESHOLD": 999, "ADAPT_SHEEP_THRESHOLD": 999, "ANIMAL_TARGET": 14, "ANIMAL_TARGETS": {"COW": 8, "SHEEP": 6}, "LABOR_MODE": "AUTO", "OPPONENT_MELON_THRESHOLD": 999}

[1/3] SCREEN: 6 variants x 4 seeds x 2 seats = 48 games ...

  variant                    W-L-T  score%      Wilson95   margin err
  opening_off                2-6-0    25.0          7-59    -5593   0
  v7_herd                    2-6-0    25.0          7-59   -10526   0
  labor_auto                 0-8-0     0.0          0-32    -5816   0
  adaptation_off             0-8-0     0.0          0-32    -8003   0
  opening_only               0-8-0     0.0          0-32   -12174   0
  BASE_agent_v10_reactive_subin     0-8-0     0.0          0-32   -14811   0


elapsed 97s
