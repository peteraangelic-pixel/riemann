# Sweep: v10_b21_rating_finalists
base=agent_v9_b21_s16.py  baseline=agent_v9_b21_s16.py  workers=16
screen=30 seeds, promote=120 seeds, finals=175 seeds, top_k=3
untouched_base_variant=False  finals_control_anchor=True
promotion_objective=rating

3 configurations:
  b18s13                 {"BUY_WHEAT": 18, "SELL_WHEAT": 13}
  b19s14                 {"BUY_WHEAT": 19, "SELL_WHEAT": 14}
  b20s15                 {"BUY_WHEAT": 20, "SELL_WHEAT": 15}

[1/3] SCREEN: 3 variants x 30 seeds x 2 seats = 180 games ...

  variant                    W-L-T  score%      Wilson95   margin err
  b18s13                    56-4-0    93.3         84-97       +7   0
  b19s14                    56-4-0    93.3         84-97       +5   0
  b20s15                    56-4-0    93.3         84-97       +3   0

  top 3 advance: b18s13, b19s14, b20s15

[2/3] PROMOTE: 3 variants x 120 seeds x 2 seats = 720 games (Wilson gate vs baseline; objective=rating) ...

  variant                    W-L-T  score%      Wilson95   margin  gate
  b18s13                  218-22-0    90.8         87-94      +20  PASS
  b19s14                  218-22-0    90.8         87-94      +18  PASS
  b20s15                  218-22-0    90.8         87-94       +8  PASS

  -> 3 variants passed the promotion gate

  anchored finalist: CONTROL_B21_S16 (agent_v9_b21_s16.py)

[3/3] FINALS: round-robin of 4 variants, 175 seeds x 2 seats per pair = 2100 games ...

  Bradley-Terry strengths (geomean-normalized; >1 beats the field):
    b18s13                 13.277
    b19s14                 2.209
    b20s15                 0.453
    CONTROL_B21_S16        0.075

  pairwise win % (row vs column):
                    b18s13    b19s14    b20s15 CONTROL_B
  b18s13                --       94%       94%       94%
  b19s14                6%        --       94%       94%
  b20s15                6%        6%        --       94%
  CONTROL_B21_S16        6%        6%        6%        --

  WINNER: b18s13

elapsed 1359s
