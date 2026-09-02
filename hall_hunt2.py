# -*- coding: utf-8 -*-
"""Hall's Conjecture hunt v2 — produkcyjne przeszukiwanie.
Algorytm: Jimenez Calvo / Herranz / Saez (arXiv:math/0504579), wzory (2.2)-(4.3).
Uruchomienie:  python3 hall_hunt2.py  B_START B_END C_MAX THREADS
Wyniki: hall_results.json (top-20), hall_hit.txt gdy r > 100.
"""
import sys, json, os, time, math
from math import gcd, isqrt
from multiprocessing import Pool
from sympy.ntheory.residue_ntheory import nthroot_mod

OUT = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(OUT, "hall_results.json")
HIT = os.path.join(OUT, "hall_hit.txt")

def factor_small(n):
    fac = {}
    d = 2
    while d * d <= n:
        if n % d == 0:
            e = 0
            while n % d == 0:
                n //= d
                e += 1
            fac[d] = e
        d += 1 if d == 2 else 2
    if n > 1:
        fac[n] = 1
    return fac

def _cbrt_mod_p(m, p):
    m %= p
    if p == 2 or p == 3:
        return [x for x in range(p) if pow(x, 3, p) == m]
    if p % 3 == 2:
        if m == 0:
            return [0]
        x = pow(m, (2 * p - 1) // 3, p)
        return [x] if pow(x, 3, p) == m else []
    # p == 1 (mod 3)
    return list(nthroot_mod(m, 3, p, all_roots=True))

def _hensel_cbrt(x0, m, p, e):
    mod = p
    x = x0 % mod
    for _ in range(1, e):
        mod2 = mod * p
        if p == 3:
            found = None
            for t in range(p):
                cand = x + t * mod
                if pow(cand, 3, mod2) == m % mod2:
                    found = cand
                    break
            if found is None:
                return None
            x = found
        else:
            f = (pow(x, 3, mod2) - m) % mod2
            inv = pow(3 * x * x % p, -1, p)
            x = (x - ((f // mod) % p) * inv * mod) % mod2
        mod = mod2
    return x

def _cbrt_mod_pk(m, p, e):
    m %= p ** e
    roots = _cbrt_mod_p(m, p)
    if not roots:
        return []
    out = []
    for r in roots:
        if r == 0:
            k = math.ceil(e / 3)
            base = p ** k
            if m % base == 0:
                out.extend(range(0, p ** e, base))
            continue
        rr = _hensel_cbrt(r, m, p, e)
        if rr is not None:
            out.append(rr)
    return out

def crt_pair(a1, m1, a2, m2):
    g = gcd(m1, m2)
    if (a2 - a1) % g != 0:
        return None
    q = m2 // g
    t = ((a2 - a1) // g * pow(m1 // g, -1, q)) % q
    return (a1 + m1 * t) % (m1 * q)

def cbrt_mod_square(m, b, bfac):
    b2 = b * b
    m %= b2
    mods = []
    for p, e in bfac.items():
        rs = _cbrt_mod_pk(m, p, 2 * e)
        if not rs:
            return []
        mods.append((rs, p ** (2 * e)))
    cur_roots, cur_mod = mods[0]
    for rs, m2 in mods[1:]:
        new = []
        for a in cur_roots:
            for b_ in rs:
                r = crt_pair(a, cur_mod, b_, m2)
                if r is not None:
                    new.append(r)
        cur_roots, cur_mod = new, cur_mod * m2
        if not cur_roots:
            return []
    return [r % b2 for r in cur_roots]

def calc_r(x):
    x3 = x ** 3
    y = isqrt(x3)
    k1 = x3 - y * y
    k2 = (y + 1) ** 2 - x3
    if k1 <= k2:
        k, yb = k1, y
    else:
        k, yb = k2, y + 1
    return yb, k

def scan_b(args):
    b, C_MAX, N_RANGE = args
    b2 = b * b
    bfac = factor_small(b)
    out = []
    Cnum = 1
    while Cnum <= 2 * C_MAX:
        if gcd(Cnum, b) == 1:
            if b % 2 == 0 and Cnum % 2 == 0:
                Cnum += 1
                continue
            a0s = cbrt_mod_square(Cnum, b, bfac)
            if a0s:
                for a0 in a0s:
                    if gcd(a0, b) != 1:
                        continue
                    alpha = (a0 * a0) % b2
                    top = 2 * a0 * a0 - alpha
                    d = gcd(3 * top, 2 * b)
                    num4 = 2 * a0 ** 3 - 3 * alpha * a0 + Cnum
                    if num4 % (d * b2):
                        continue
                    rhs = num4 // (d * b2)
                    M = 2 * b // d
                    td = 3 * top // d
                    if gcd(td, M) != 1:
                        continue
                    k0 = (-pow(td, -1, M) * rhs) % M
                    Cval = Cnum / 2.0
                    target = 3 * alpha * alpha / (8 * Cval) - a0 - k0 * b2
                    n0 = round(target * d / (2 * b ** 3))
                    for n in range(n0 - N_RANGE, n0 + N_RANGE + 1):
                        a = a0 + k0 * b2 + n * (2 * b ** 3) // d
                        if a <= 0 or gcd(a, b) != 1:
                            continue
                        aa = (a * a) % b2
                        x0 = (a * a - aa) // b2
                        if x0 <= 1:
                            continue
                        c1 = 2 if a % 2 == 0 else 1
                        c2 = 3 if b % 3 == 0 else 1
                        g = c1 * c2
                        rhs_num = 3 * a * aa - 2 * a ** 3 - Cnum
                        if rhs_num % (g * b2):
                            continue
                        rhs2 = rhs_num // (g * b2)
                        L = 3 * a // g
                        Mj = 2 * b // g
                        if gcd(L, Mj) != 1:
                            continue
                        j = (rhs2 * pow(L, -1, Mj)) % Mj
                        for w in (-1, 0, 1):
                            x = x0 + j + w * Mj
                            if x <= 1:
                                continue
                            yb, k = calc_r(x)
                            if k == 0:
                                continue
                            if k * k * 1 <= x:  # r >= 1
                                r2 = x / (k * k)
                                out.append((r2, x, yb, k, (b, Cnum, a0, n, j, w)))
        Cnum += 1
    return out

def main():
    b0, b1 = int(sys.argv[1]), int(sys.argv[2])
    C_MAX = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    N_RANGE = int(sys.argv[4]) if len(sys.argv) > 4 else 30
    TH = int(sys.argv[5]) if len(sys.argv) > 5 else 2
    t0 = time.time()
    best = []
    if os.path.exists(RES):
        try:
            best = json.load(open(RES))
        except Exception:
            best = []
    b_list = list(range(b0, b1))
    with Pool(TH) as pool:
        for i, res in enumerate(pool.imap_unordered(scan_b, [(b, C_MAX, N_RANGE) for b in b_list], chunksize=64)):
            if res:
                for (r2, x, yb, k, meta) in res:
                    best.append([r2, x, yb, k, list(meta)])
                    # HIT?
                    if x > 10000 * k * k:
                        with open(HIT, "w") as f:
                            json.dump({"x": x, "y": yb, "k": k, "meta": meta}, f)
                        print(f"\n!!!!!! HIT r>100: x={x} y={yb} k={k}\n")
            if i % 2000 == 0:
                best.sort(key=lambda t: -t[0])
                best = best[:30]
                json.dump(best[:30], open(RES, "w"))
                if i and i % 20000 == 0:
                    print(f"[{time.time()-t0:8.0f}s] b={b0+i} top_r={best[0][0]**0.5:.3f} x={best[0][1]}")
        best.sort(key=lambda t: -t[0])
        best = best[:30]
        json.dump(best[:30], open(RES, "w"))
    print(f"KONIEC b=[{b0},{b1})  czas={time.time()-t0:.0f}s  najlepsze:")
    for (r2, x, yb, k, meta) in best[:10]:
        print(f"  r={r2**0.5:8.3f}  x={x}  y={yb}  k={k}  meta={meta}")

if __name__ == "__main__":
    main()
