# -*- coding: utf-8 -*-
"""
Hall's Conjecture hunt — implementacja algorytmu z artykulu
I. Jimenez Calvo, J. Herranz, G. Saez, "A new algorithm to search for small
nonzero |x^3 - y^2| values" (arXiv:math/0504579).

Cel: znalezc (x, y) z  sqrt(x)/|y^2-x^3| > 100   (rekord swiata: 46.60, Elkies).
"""
import math
from math import gcd, isqrt
from functools import lru_cache

# ----------------------------------------------------------------------
# pomocnicze: pierwiastki 3. stopnia modulo p^e
# ----------------------------------------------------------------------
def factor_small(n):
    """Faktoryzacja przez trial division (n <= 1e7)."""
    fac = {}
    d = 2
    while d * d <= n:
        if n % d == 0:
            e = 0
            while n % d == 0:
                n //= d; e += 1
            fac[d] = e
        d += 1 if d == 2 else 2
    if n > 1:
        fac[n] = 1
    return fac

def _cbrt_mod_p(m, p):
    """rozwiazanie x^3 == m (mod p), p pierwsze; zwraca liste rozwiazan (0..p-1)"""
    m %= p
    if p == 2 or p == 3:
        return [x for x in range(p) if pow(x, 3, p) == m]
    if p % 3 == 2:
        if m == 0:
            return [0]
        x = pow(m, (2 * p - 1) // 3, p)
        return [x] if pow(x, 3, p) == m else []
    else:  # p == 1 (mod 3): brute dla malych p (ograniczenie wydajnosciowe)
        if p > 20000:
            return None  # nie obslugiwane tutaj (skip)
        return [x for x in range(p) if pow(x, 3, p) == m]

def _hensel_cbrt(x0, m, p, e):
    """podnies x0 (root mod p) do root mod p^e dla x^3 == m (mod p^e)"""
    mod = p
    x = x0 % mod
    for _ in range(1, e):
        mod2 = mod * p
        # x^3 == m (mod mod2): x_new = x - (x^3-m)/(3x^2) (mod mod2), 3x^2 != 0 mod p (p!=3; p==3 case special)
        if p == 3:
            # mamy root tylko mod 3; lifting: sprawdzamy x, x+mod, x+2*mod (brute)
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
            df = (3 * x * x) % p
            inv = pow(df, -1, p)
            x = (x - ((f // mod) % p) * inv * mod) % mod2
        mod = mod2
    return x

def _cbrt_mod_pk(m, p, e):
    """x^3 == m (mod p^e); lista rozwiazan"""
    m %= p ** e
    roots = _cbrt_mod_p(m, p)
    if roots is None:
        return None
    out = []
    for r in roots:
        if r == 0:
            # x = p^ceil(e/3) * t:  tylko x≡0 moze byc gdy m≡0 mod p^3...
            # prosciej: tylko x≡0 (mod p^ceil(e/3))
            import math as _m
            k = _m.ceil(e / 3)
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
    l = m1 // g * m2
    p = m1 // g
    q = m2 // g
    t = ((a2 - a1) // g * pow(p, -1, q)) % q
    return (a1 + m1 * t) % l, l

def cbrt_mod_square(m, b, bfac=None):
    """x^3 == m (mod b^2). Zwraca liste rozwiazan x in [0, b^2)."""
    if b == 1:
        return [0]
    b2 = b * b
    m %= b2
    if bfac is None:
        bfac = factor_small(b)
    mods = []
    for p, e in bfac.items():
        rs = _cbrt_mod_pk(m, p, 2 * e)
        if rs is None:
            return None          # nieobslugiwany czynnik (p > 20000, p=1 mod 3)
        if not rs:
            return []
        mods.append((rs, p ** (2 * e)))
    # CRT po kolei
    cur_roots, cur_mod = mods[0]
    for rs, m2 in mods[1:]:
        new = []
        for a in cur_roots:
            for b_ in rs:
                r = crt_pair(a, cur_mod, b_, m2)
                if r is not None:
                    new.append(r[0])
        cur_roots, cur_mod = new, cur_mod * m2
        if not cur_roots:
            return []
    return [r % b2 for r in cur_roots]

# ----------------------------------------------------------------------
# glowny algorytm
# ----------------------------------------------------------------------
C_CAND = []
def build_C(maxC):
    """C in {1/2, 1, 3/2, 2, ...} reprezentowane jako (num, den), num/den <= maxC"""
    out = []
    num = 1
    while num <= 2 * maxC:
        den = 2
        val = num / den
        if val <= maxC:
            out.append((num, den))   # C = num/2  (1/2, 1, 3/2, 2, ...)
        num += 1
    return out

def hunt_b(b, maxC=40.0, verbose=False):
    """Zwraca liste (r, x, y, k, extra) znalezionych dla tego b (najlepsze)."""
    res = []
    b2 = b * b
    bfac = factor_small(b)
    for (Cnum, Cden) in build_C(maxC):
        if gcd(Cnum, b) != 1:
            continue
        m = Cnum  # 2C = Cnum/Cden*2 — uwaga: 2C = Cnum (gdy C = Cnum/2)
        # Kongruencja (4.2): a0^3 == 2C (mod b^2); 2C = Cnum (bo C = Cnum/2)
        a0s = cbrt_mod_square(Cnum, b, bfac)
        if a0s is None or not a0s:
            continue
        for a0 in a0s:
            if gcd(a0, b) != 1:
                continue
            alpha = (a0 * a0) % b2
            top = 2 * a0 * a0 - alpha          # (4.3): 3(2a0^2 - alpha)/d ...
            d = gcd(3 * top, 2 * b)
            top_d = 3 * top // d               # calkowite?
            if 3 * top % d != 0:
                continue
            num4 = 2 * a0 ** 3 - 3 * alpha * a0 + Cnum
            if num4 % (d * b2) != 0:
                continue
            rhs = num4 // (d * b2)
            # k0 == -inv(top_d, 2b/d) * rhs  (mod 2b/d)
            M = 2 * b // d
            if gcd(top_d, M) != 1:
                continue
            k0 = (-pow(top_d, -1, M) * rhs) % M
            # n0 ≈ (d/(2b^3)) * (3 alpha^2/(8C) - a0 - k0 b^2)
            Cval = Cnum / Cden
            target = 3 * alpha * alpha / (8 * Cval) - a0 - k0 * b2
            n0 = round(target * d / (2 * b ** 3))
            for n in range(n0 - 2, n0 + 3):
                a = a0 + k0 * b2 + n * (2 * b ** 3) // d
                if a <= 0:
                    continue
                if gcd(a, b) != 1:
                    continue
                alpha2 = (a * a) % b2
                x0 = (a * a - alpha2) // b2
                if x0 <= 0:
                    continue
                # j z (3.1): (3a/(c1c2)) j = (3a*alpha - 2a^3 - 2C)/(c1c2 b^2) (mod 2b/(c1c2))
                c1 = 2 if a % 2 == 0 else 1
                c2 = 3 if b % 3 == 0 else 1
                g = c1 * c2
                rhs_num = 3 * a * alpha2 - 2 * a ** 3 - Cnum   # 2C = Cnum
                if rhs_num % (g * b2) != 0:
                    continue
                rhs = rhs_num // (g * b2)
                L = 3 * a // g
                Mj = 2 * b // g
                if gcd(L, Mj) != 1:
                    continue
                j = (rhs * pow(L, -1, Mj)) % Mj
                bp = Mj  # b' = 2b/(c1c2)
                for w in (0, 1, -1):
                    x = x0 + j + w * bp
                    if x <= 1:
                        continue
                    x3 = x ** 3
                    y = isqrt(x3)
                    if y * y < x3:
                        k1 = x3 - y * y
                        k2 = y * y + 2 * y + 1 - x3
                    else:
                        k1 = y * y - x3
                        k2 = x3 - (y - 1) * (y - 1)
                    k = min(k1, k2)
                    if k == 0:
                        continue
                    # r > 100  <=>  x > (100*k)^2
                    if x > 10000 * k * k:
                        ok = True
                    else:
                        ok = False
                    r2 = x / (k * k)  # r^2
                    res.append((r2, x, y, k, (b, Cnum, a, n)))
                    if verbose and ok:
                        print(f"!!! HIT r>100: x={x} k={k}")
    res.sort(key=lambda t: -t[0])
    return res[:6]

if __name__ == "__main__":
    import sys
    b0, b1 = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (137035, 137036)
    best = []
    for b in range(b0, b1):
        for (r2, x, y, k, extra) in hunt_b(b):
            best.append((r2, x, y, k, extra))
            best.sort(key=lambda t: -t[0])
            best = best[:10]
    for (r2, x, y, k, extra) in best:
        print(f"r={r2**0.5:8.3f}  x={x}  k={k}  y={str(y)[:20]}...  extra={extra}")
