# -*- coding: utf-8 -*-
"""
Wyprawa w głąb hipotezy Riemanna: weryfikacja numeryczna + "muzyka liczb pierwszych".
Wszystko, co tu robimy, jest spójne z artykułem Josepha Howletta (Świat Nauki 9/2026).
"""
import mpmath as mp
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

mp.mp.dps = 20
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------
# 0) Cache (pierwsze uruchomienie liczy, kolejne czytaja z dysku)
# ---------------------------------------------------------------
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache.npz")
N_ZEROS = 1200

# ---------------------------------------------------------------
# 1) Pierwsze zera na prostej krytycznej + weryfikacja zeta(1/2+ig) = 0
# ---------------------------------------------------------------
print("=" * 70)
print("1) PIERWSZE ZERA I WERYFIKACJA ZETA(1/2 + i*gamma) = 0")
print("=" * 70)
if os.path.exists(CACHE):
    C = np.load(CACHE)
    gammas, ts, Zt, Lam, isprime, psi_true = (C["gammas"], C["ts"], C["Zt"],
                                              C["Lam"], C["isprime"], C["psi"])
    print(f"  (odczytano z cache; {len(gammas)} zer)")
else:
    gammas = np.array([float(mp.im(mp.zetazero(n))) for n in range(1, N_ZEROS + 1)], dtype=float)
    ts = np.linspace(0.2, 62.0, 4000)
    Zt = np.array([float(mp.siegelz(t)) for t in ts])
    M = 10 ** 6
    Lam = np.zeros(M + 1)
    isprime = np.ones(M + 1, dtype=bool)
    isprime[:2] = False
    for i in range(2, int(M ** 0.5) + 1):
        if isprime[i]:
            isprime[i * i::i] = False
    for p in np.nonzero(isprime)[0]:
        lp = float(np.log(p)); pk = p
        while pk <= M:
            Lam[pk] += lp
            pk *= p
    psi_true = np.cumsum(Lam)
    np.savez(CACHE, gammas=gammas, ts=ts, Zt=Zt, Lam=Lam, isprime=isprime, psi=psi_true)
    print(f"  (policzono od zera; {len(gammas)} zer, psi do {M})")

resid = [abs(mp.zeta(mp.mpf("0.5") + 1j * mp.im(mp.zetazero(n)))) for n in range(1, 13)]
table = []
for n in range(1, 13):
    g = gammas[n - 1]
    r = resid[n - 1]
    print(f"zero #{n:2d}:  gamma = {g:10.6f}   |zeta(1/2+i*gamma)| = {mp.nstr(r, 3)}")
    table.append((n, g, float(r)))

# ---------------------------------------------------------------
# 2) Kontrola liczby zer: formuła Riemanna-von Mangoldta
#    N(T) = T/(2*pi) * log(T/(2*pi*e)) + 7/8 + S(T)
# ---------------------------------------------------------------
print()
print("=" * 70)
print("2) KONTROLA LICZBY ZER (Riemann-von Mangoldt)")
print("=" * 70)
print(" Funkcja siegela-theta -> liczba zer w pasie krytycznym do wysokosci T")
for T in (100, 200, 500, 1000, 1500):
    n_on_line = int(np.searchsorted(gammas, T))  # zer o gamma <= T
    est = T / (2 * np.pi) * np.log(T / (2 * np.pi * np.e)) + 7.0 / 8.0
    print(f" T = {T:5d}:  zer na prostej krytycznej = {n_on_line:4d}, "
          f"przewidywanie N(T) ~ {est:8.1f}, roznica = {n_on_line - est:+.2f}")

# ---------------------------------------------------------------
# 3) Riemann-Siegel Z(t): "dyrygent" orkiestry liczb pierwszych
# ---------------------------------------------------------------
print()
print("=" * 70)
print("3) RYSUNEK: funkcja Z(t) Riemanna-Siegla (real-valued zeta na prostej)")
print("=" * 70)
fig, ax = plt.subplots(figsize=(11, 5.2))
ax.plot(ts, Zt, lw=0.8, color="#1f4e79")
mask = gammas < 62.0
ax.plot(gammas[mask], np.zeros(mask.sum()), "o", ms=4, color="#c00000", zorder=5,
        label="zera: zeta(1/2 + i*gamma) = 0")
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel("t  (czesci urojona)")
ax.set_ylabel("Z(t)")
ax.set_title("Funkcja Z(t) Riemanna-Siegla: na prostej krytycznej zeta(1/2+it) = e^(-i*theta(t))*Z(t),\n"
             "wiec Z(t) jest rzeczywista - kazde przeciecie zera to jeden \"dzwiek\" w muzyce liczb pierwszych",
             fontsize=10)
ax.legend(loc="lower left")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(f"{OUT}/funkcja_Z.png", dpi=150)
plt.close(fig)
print("zapisano:", f"{OUT}/funkcja_Z.png")


# ---------------------------------------------------------------
# 4) "Muzyka liczb pierwszych": jawny wzór wykładniczy
#    psi(x) = x - sum_rho x^rho/rho - log(2pi) - 1/2 log(1-x^-2)
# ---------------------------------------------------------------
print()
print("=" * 70)
print("4) JAWNY WZOR / REKONSTRUKCJA psi(x) Z ZER (x <= 150)")
print("=" * 70)
M = len(Lam) - 1  # z cache
print(f" kontrola: psi(10) = {psi_true[10]:.3f} (powinno byc 7.832 = 3log2+2log3+log5+log7)")

xmax = 150
xs = np.arange(2, xmax + 1) + 0.5  # punkty polowkowe (unikanie punktow nieciaglosci)
logxs = np.log(xs)

def psi_from_zeros(n_zeros):
    g = gammas[:n_zeros]
    rho = 0.5 + 1j * g
    # suma 2*Re(x^rho/rho) po parach sprzezonych; wektoryzowane po x
    term = np.exp(np.outer(logxs, rho)) / rho  # (len(xs), n_zeros)
    s = 2.0 * np.real(term.sum(axis=1))
    return xs - s - np.log(2 * np.pi) - 0.5 * np.log(1.0 - xs ** -2)

fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8))

# lewy panel: zbliżenie, na którym widać różnice między liczbą zer
ax = axes[0]
ax.step(xs, psi_true[np.floor(xs).astype(int)], where="mid",
        color="k", lw=2.2, label="prawdziwa psi(x)")
for nz, c, ls, lw in ((20, "#c00000", "--", 2.0),
                      (150, "#ff7f0e", "-.", 1.6),
                      (1200, "#1f4e79", "-", 1.2)):
    ax.plot(xs, psi_from_zeros(nz), color=c, ls=ls, lw=lw,
            label=f"wzor z {nz:4d} zerami")
ax.set_xlim(30, 95)
ax.set_xlabel("x"); ax.set_ylabel("psi(x)")
ax.set_title("Rekonstrukcja psi(x) ze wzoru jawnego (zbliżenie)", fontsize=10)
ax.legend(fontsize=8, loc="upper left"); ax.grid(alpha=0.3)

# prawy panel: błąd rekonstrukcji
ax = axes[1]
for nz, c in ((20, "#c00000"), (150, "#ff7f0e"), (1200, "#1f4e79")):
    err = psi_from_zeros(nz) - psi_true[np.floor(xs).astype(int)]
    ax.plot(xs, err, color=c, lw=1.0, label=f"{nz} zer")
ax.axhline(0, color="k", lw=0.8)
ax.set_xlim(2, xmax)
ax.set_xlabel("x"); ax.set_ylabel("blad: wzor - psi(x)")
ax.set_title("Blad rekonstrukcji: zbiega do zera wraz z liczba zer", fontsize=10)
ax.legend(fontsize=8); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(f"{OUT}/jawny_wzor.png", dpi=150)
plt.close(fig)
print("zapisano:", f"{OUT}/jawny_wzor.png")

# ---------------------------------------------------------------
# 5) Blad psi(x)-x wzgledem sqrt(x): RH <=> blad = O(x^(1/2+eps))
# ---------------------------------------------------------------
print()
print("=" * 70)
print("5) BLAD |psi(x) - x| vs PIERWIASTEK Z x  (RH: blad < x^(1/2+eps))")
print("=" * 70)
xarr = np.arange(2, M + 1, dtype=float)
err = np.abs(psi_true[2:] - xarr)
ratio = err / np.sqrt(xarr)
print(f" dla x <= {M}:  max |psi(x)-x|/sqrt(x) = {ratio.max():.3f}")
idx = np.argmax(ratio)
print(f"  (najgorzej okolo x = {xarr[idx]:.0f})")

fig, ax = plt.subplots(figsize=(11, 4.6))
xidx = np.arange(2, M + 1)
ax.loglog(xidx, np.abs(psi_true[2:] - xidx), lw=0.7, color="#1f4e79",
          label="|ψ(x) − x|  (dokładna wartość)")
ax.loglog(xidx, 0.6 * np.sqrt(xidx), lw=1.4, color="#c00000", ls="--",
          label="0.6·√x  (rzędna wielkości zgodna z RH)")
ax.set_xlabel("x")
ax.set_ylabel("|ψ(x) − x|")
ax.set_title("Błąd w aproksymacji ψ(x) ≈ x: rośnie wolniej niż √x — dokładnie to "
             "przepowiada hipoteza Riemanna")
ax.legend()
ax.grid(alpha=0.3, which="both")
fig.tight_layout()
fig.savefig(f"{OUT}/blad_psi.png", dpi=150)
plt.close(fig)
print("zapisano:", f"{OUT}/blad_psi.png")

# ---------------------------------------------------------------
# 6) pi(x) vs Li(x) — tabela Gaussa z artykulu
# ---------------------------------------------------------------
print()
print("=" * 70)
print("6) pi(x) vs. Li(x) — przyklad: ile liczb pierwszych do x?")
print("=" * 70)
pi = np.cumsum(isprime.astype(np.int64))
for xx in (10 ** 2, 10 ** 3, 10 ** 4, 10 ** 5, 10 ** 6):
    li = float(mp.li(xx))
    print(f" x = {xx:8d}:  pi(x) = {pi[xx]:8d},  Li(x) = {li:12.1f},  roznica = {li - pi[xx]:+.2f}")

# ---------------------------------------------------------------
# 7) Zapis danych do raportu
# ---------------------------------------------------------------
import json
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "wyniki.json"), "w") as f:
    json.dump({"first13": table,
               "gamma_of_zeros_1_to_1200": gammas.tolist()}, f, indent=1)
print("\nGotowe.")
