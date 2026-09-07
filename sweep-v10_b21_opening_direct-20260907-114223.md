# Sweep: v10_b21_opening_direct
base=agent_v9_b21_s16.py  baseline=agent_v9_b21_s16.py  workers=30
screen=18 seeds, promote=100 seeds, finals=68 seeds, top_k=4
untouched_base_variant=False  finals_control_anchor=True

23 configurations:
  b18s12                 {"BUY_WHEAT": 18, "SELL_WHEAT": 12}
  b18s13                 {"BUY_WHEAT": 18, "SELL_WHEAT": 13}
  b18s14                 {"BUY_WHEAT": 18, "SELL_WHEAT": 14}
  b19s13                 {"BUY_WHEAT": 19, "SELL_WHEAT": 13}
  b19s14                 {"BUY_WHEAT": 19, "SELL_WHEAT": 14}
  b19s15                 {"BUY_WHEAT": 19, "SELL_WHEAT": 15}
  b20s14                 {"BUY_WHEAT": 20, "SELL_WHEAT": 14}
  b20s15                 {"BUY_WHEAT": 20, "SELL_WHEAT": 15}
  b20s16                 {"BUY_WHEAT": 20, "SELL_WHEAT": 16}
  b21s15                 {"BUY_WHEAT": 21, "SELL_WHEAT": 15}
  b21s17                 {"BUY_WHEAT": 21, "SELL_WHEAT": 17}
  b22s16                 {"BUY_WHEAT": 22, "SELL_WHEAT": 16}
  b22s17                 {"BUY_WHEAT": 22, "SELL_WHEAT": 17}
  b22s18                 {"BUY_WHEAT": 22, "SELL_WHEAT": 18}
  b23s17                 {"BUY_WHEAT": 23, "SELL_WHEAT": 17}
  b23s18                 {"BUY_WHEAT": 23, "SELL_WHEAT": 18}
  b23s19                 {"BUY_WHEAT": 23, "SELL_WHEAT": 19}
  b24s18                 {"BUY_WHEAT": 24, "SELL_WHEAT": 18}
  b24s19                 {"BUY_WHEAT": 24, "SELL_WHEAT": 19}
  b24s20                 {"BUY_WHEAT": 24, "SELL_WHEAT": 20}
  b25s19                 {"BUY_WHEAT": 25, "SELL_WHEAT": 19}
  b25s20                 {"BUY_WHEAT": 25, "SELL_WHEAT": 20}
  b25s21                 {"BUY_WHEAT": 25, "SELL_WHEAT": 21}

[1/3] SCREEN: 23 variants x 18 seeds x 2 seats = 828 games ...

  variant                    W-L-T  score%      Wilson95   margin err
  b18s13                    32-4-0    88.9         75-96       +4   0
  b19s14                    32-4-0    88.9         75-96       +3   0
  b20s15                    32-4-0    88.9         75-96       +1   0
  b25s20                   17-19-0    47.2         32-63      -87   0
  b24s19                    8-28-0    22.2         12-38       -0   0
  b22s17                    4-32-0    11.1          4-25       -2   0
  b23s18                    4-32-0    11.1          4-25       -5   0
  b18s14                    0-36-0     0.0          0-10   -11379   0
  b20s16                    0-36-0     0.0          0-10   -11380   0
  b19s15                    0-36-0     0.0          0-10   -11382   0
  b21s17                    0-36-0     0.0          0-10   -11384   0
  b22s18                    0-36-0     0.0          0-10   -11385   0
  b23s19                    0-36-0     0.0          0-10   -11464   0
  b24s20                    0-36-0     0.0          0-10   -11467   0
  b25s21                    0-36-0     0.0          0-10   -11470   0
  b24s18                    0-36-0     0.0          0-10   -26538   0
  b25s19                    0-36-0     0.0          0-10   -26542   0
  b18s12                    0-36-0     0.0          0-10   -26958   0
  b22s16                    0-36-0     0.0          0-10   -26960   0
  b19s13                    0-36-0     0.0          0-10   -26960   0
  b20s14                    0-36-0     0.0          0-10   -26962   0
  b21s15                    0-36-0     0.0          0-10   -26964   0
  b23s17                    0-36-0     0.0          0-10   -26993   0

  top 4 advance: b18s13, b19s14, b20s15, b25s20

[2/3] PROMOTE: 4 variants x 100 seeds x 2 seats = 800 games (Wilson gate vs baseline) ...

  variant                    W-L-T  score%      Wilson95   margin  gate
  b18s13                  186-14-0    93.0         89-96      -14  fail
  b19s14                  186-14-0    93.0         89-96      -16  fail
  b20s15                  186-14-0    93.0         89-96      -21  fail
  b25s20                  98-102-0    49.0         42-56      -29  fail

  -> 0 variants passed the promotion gate

[3/3] FINALS skipped (no mutation passed the direct control gate)

elapsed 612s
