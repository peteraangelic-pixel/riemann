
## 2026-09-10 (8): screen kombinatoryki otwarć (40 wariantów, 1 RUN) → V6
- Screen `opening1` (CI run 34489178779, 12800 gier, seedy 53000+, 10 kontroli): 40 wariantów t0/t1 na ciałach V5/V4/v3/v2.
  TOP: V5-syntetyki (t0 buy40/s60, buy15/s30, buy27/s60) + V5-s0V16s1GJ — wszystkie: DN 24-8, v4/v3/v2/hyb/b21/K15/G15/mkt WYGRANE.
  Odkrycie ROZPRZĘŻENIA: t0 rozstrzyga DN (kanno/syntetyk = fix), t1 rozstrzyga hybrydę (GJ t1 = win); V16-t0 + GJ-t1 bierze oba.
  Kontrola przyczynowości: v2/v3-t01GJ DOSTAJĄ chorobę DN 0-32 (potwierdzenie wektora); t0-bez-SELLA (b15s0) łamie v3 0-32; t01DN i t1-sell45 = katastrofa 0-32 wszędzie (niespójność otwarcie↔reszta, ta sama lekcja co V4.1).
- Holdout (run 34489350330, fresh 54000+, 128 gier × 13 kontroli): s0V16s1GJ CZYSTY (DN 94-34, v4 124-4, v3 125-3, v2 126-2, hyb 122-6, subin/yus/him 128-0).
  b40s60 ODRZUCONY: ukryta katastrofa subin/himanshu 0-128 (−28k!) — screen-panel był za wąski (lekcja: screen = szeroko, holdout = jeszcze szerzej).
  b15s30 ODRZUCONY: himanshu 66-62 (słaby). Struktura V16-t0 (DWA osobne BUY 7+20 + SELL 60) load-bearing — syntetyki z jednym BUY gorsze.
- Panel TOP15 (run 34489475005, fresh 55000+, 128×15): s0V16s1GJ 1725-194 vs V5 1614-306 — IDENTYCZNY jak V5 wszędzie OPRÓCZ DN: 109-19 (+10.5k) vs 0-128 (−45.6k). Strictly-better.
- Slow-G2 gate (lokalnie, KE 1.32.7, 16 gier): 16-0 (+6130/g). 5/5 bram zielonych.
- KORONACJA: `agents/champion_tape_v6.py` = V5-body + V16-t0 + GJ-t1.
- Nowe narzędzia: `scripts/screen_openings.py` + `specs/opening_screen1.json` + job `screen` w driverze + `scripts/slow_gate.py` (odtworzony minimalny harness slow po utracie brancha a20ab).
- Live: v2 champion; pierwsze A/B = v3 (spójność), drugie = V6. V5/V4 nie submitować.
