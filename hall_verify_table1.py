# -*- coding: utf-8 -*-
"""Cross-check hall_results.json against JCHS Table 1 (arXiv math/0504579,
Math. Comp. 78 (2009) 2435-2444). Items with b < B_MAX and half-integer C
should have been rediscovered by our scan (x <= 1 is skipped by design).
Usage: python3 hall_verify_table1.py [B_MAX]
"""
import json, sys

# (#, x, r, b, C) from Table 1
TABLE1 = [
    (1, 2, 1.41, None, None),
    (2, 5234, 4.26, 26, 0.5),
    (3, 8158, 3.76, 28, 0.5),
    (4, 93844, 1.03, 53, 1),
    (5, 367806, 2.93, 117, 0.5),
    (6, 421351, 1.05, 26, 0.5),
    (7, 720114, 3.77, 42, 0.5),
    (8, 939787, 3.16, 115, 2),
    (9, 28187351, 4.87, 159, 5),
    (10, 110781386, 1.23, 95, 0.5),
    (11, 154319269, 1.08, 228, 0.5),
    (12, 384242766, 1.34, 728, 0.5),
    (13, 390620082, 1.33, 730, 0.5),
    (14, 3790689201, 2.20, 1155, 4),
    (15, 65589428378, 2.19, 5235, 8.5),
    (16, 952764389446, 1.15, 1448, 2.5),
    (17, 12438517260105, 1.27, 13415, 6),
    (18, 35495694227489, 1.15, 97266, 0.5),
    (19, 53197086958290, 1.66, 13777, 1),
    (20, 5853886516781223, 46.60, 137035, 9),
    (21, 12813608766102806, 1.30, 6291, 17.5),
    (22, 23415546067124892, 1.46, 1315447, 32),
    (23, 38115991067861271, 6.50, 321346, 0.5),
    (24, 322001299796379844, 1.04, 1313479, 11),
    (25, 471477085999389882, 1.38, 3281374, 47.5),
    (26, 810574762403977064, 4.66, 5346121, 24.5),
    (27, 9870884617163518770, 1.90, 4928788, 54.5),
    (28, 42532374580189966073, 3.47, 583876, 4.5),
    (29, 51698891432429706382, 1.75, 19061951, 29),
    (30, 44648329463517920535, 1.79, 11744301, 13),
    (31, 231411667627225650649, 3.71, 11694866, 173.5),
    (32, 601724682280310364065, 1.88, 7496613, 13),
    (33, 4996798823245299750533, 2.17, 76010518, 33.5),
    (34, 5592930378182848874404, 1.38, 93203798, 69.5),
    (35, 14038790674256691230847, 1.27, 61769318, 26.5),
    (36, 77148032713960680268604, 10.18, 184388019, 4),
    (37, 180179004295105849668818, 5.65, 292889921, 22.5),
    (38, 372193377967238474960883, 1.33, 2554989, 4),
    (39, 664947779818324205678136, 16.53, 678534061, 39.2),
    (40, 2028871373185892500636155, 1.14, 490670918, 27.5),
    (41, 37223900078734215181946587, 1.87, 530793746, 728.5),
    (42, 3690445383173227306376634720, 1.51, 685266726, 0.5),
    (43, 1114592308630995805123571151844, 1.04, 52019836686, 737.5),
    (44, 6078673043126084065007902175846955, 1.03, 8144029787, 3),
]

def main():
    B_MAX = int(sys.argv[1]) if len(sys.argv) > 1 else 200000
    res = set()
    for e in json.load(open("hall_results.json")):
        r2, x, y, k, meta = e
        res.add(x)
    print(f"hall_results.json distinct x: {len(res)}")
    found, missing, skipped = [], [], []
    for num, x, r, b, C in TABLE1:
        if x <= 1:
            skipped.append(num); continue
        if b is None or b >= B_MAX:
            continue
        if C is not None and (2 * C) != int(2 * C):
            continue  # non-half-integer C not in our Cnum grid
        (found if x in res else missing).append((num, x, r, b, C))
    print(f"Table1 items with 2 < x, b < {B_MAX}, half-int C: {len(found) + len(missing)}")
    print(f"  rediscovered: {len(found)}")
    for num, x, r, b, C in found:
        print(f"    #{num:>2}  x={x}  (r={r})")
    print(f"  NOT rediscovered: {len(missing)}")
    for num, x, r, b, C in missing:
        print(f"    #{num:>2}  x={x}  (r={r})  b={b} C={C}")
    # also: new x's in results not in Table 1 (potential new examples!)
    tabx = {x for _, x, _, _, _ in TABLE1}
    newx = sorted(res - tabx)
    print(f"\nresults x NOT in Table 1 (candidates): {len(newx)}")
    import math
    for x in newx[:10]:
        e = [e for e in json.load(open("hall_results.json")) if e[1] == x][0]
        r2, xx, y, k, meta = e
        print(f"    x={x}  r={r2**0.5:.3f}  k={k}  y={y}  meta={meta}")

if __name__ == "__main__":
    main()
