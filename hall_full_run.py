# -*- coding: utf-8 -*-
"""Full run: collect ALL examples (r >= 1) for b in [B0, B1) — no top-N cutoff.
Saves hall_all.json: {x: [k, [ (b, Cnum, ...) meta ] ]} and prints stats.
Usage: python3 hall_full_run.py B0 B1 C_MAX N_RANGE THREADS
"""
import sys, json, time
from multiprocessing import Pool
import hall_hunt2 as hh

def collect(args):
    b, C_MAX, N_RANGE = args
    res = []
    for (r2, x, yb, k, meta) in hh.scan_b(args):
        res.append((x, k, list(meta)))
    return b, res

def main():
    b0, b1 = int(sys.argv[1]), int(sys.argv[2])
    C_MAX = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    N_RANGE = int(sys.argv[4]) if len(sys.argv) > 4 else 30
    TH = int(sys.argv[5]) if len(sys.argv) > 5 else 2
    t0 = time.time()
    allx = {}
    with Pool(TH) as pool:
        for i, (b, res) in enumerate(pool.imap_unordered(collect,
                [(b, C_MAX, N_RANGE) for b in range(b0, b1)], chunksize=32)):
            for (x, k, meta) in res:
                allx.setdefault(x, []).append((k, meta))
            if (i + 1) % 10000 == 0:
                print(f"[{time.time()-t0:7.0f}s] b~{b0+i+1} distinct_x={len(allx)}", flush=True)
    # stats
    rows = []
    for x, lst in allx.items():
        k = min(k for k, _ in lst)
        import math
        r = math.sqrt(x) / k
        rows.append((x, k, r))
    rows.sort(key=lambda t: -t[2])
    json.dump({str(x): [k, [m for _, m in allx[x]]] for x, k, _ in rows},
              open("hall_all.json", "w"))
    print(f"KONIEC b=[{b0},{b1}): distinct x={len(rows)}, czas={time.time()-t0:.0f}s")
    print("top 15 by r:")
    for x, k, r in rows[:15]:
        print(f"  r={r:8.3f}  x={x}  k={k}")
    # Table-1 cross-check
    sys.path.insert(0, ".")
    import hall_verify_table1 as tv
    inres = set(allx)
    exp = [(num, x, r, b, C) for num, x, r, b, C in tv.TABLE1
           if x > 1 and b is not None and b < b1 and C is not None and 2*C == int(2*C)]
    found = [t for t in exp if t[1] in inres]
    missing = [t for t in exp if t[1] not in inres]
    print(f"Table1 (b<{b1}, half-int C, x>1): expected {len(exp)}, found {len(found)}, "
          f"missing {len(missing)}")
    for num, x, r, b, C in found:
        print(f"  FOUND  #{num:>2} x={x} (r={r})")
    for num, x, r, b, C in missing:
        print(f"  MISS   #{num:>2} x={x} (r={r}) table_b={b} C={C}")

if __name__ == "__main__":
    main()
