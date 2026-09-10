
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

## 2026-09-10 (9): screen2 hill-climb V6 → V7 (t1 buy85→buy60), screen3 mikro-grid
- Screen2 `opening2` (29 wariantów × 15 kontroli, 13920 gier, seedy 57000): rank1 t1b60 (DN 24-8, hyb 31-1, mirrory V5+V6 31-1).
  Ustalenia: t2 IRRELEVANT (t2GJ/t2V16 ≡ base); t0-sell 45-90 flat; single-buy t0 łamie himanshu (19-13, potwierdzenie load-bearing struktury V16-t0); triple-buy psuje DN (17-15 — DOKŁADNIE 2 buy'e to sweet spot); t1-buy100 łamie hybrydę (klif 85→100); WSZYSTKIE edge-stackingi z V16 FAIL (v4/v3/hyb leżą — potwierdzenie ostrzeżenia z ablacji: lokalny edge H2H nie transferuje); t1-ogon (BUY5) knife-edge (usunięcie = 0-32 wszędzie).
- Holdout screen2 (fresh 58000+, 128×15): t1b60 SWEEP — bije V6 128-0 i V5 128-0 (koniec klątwy lustra!), hyb 128-0, G15 128-0, DN 100-28 = V6; eksplozje marży: subin +77k, himanshu +73k (×11-15 vs V6).
- Trace t1b60-vs-subin (seed 58000): dzień 0 IDENTYCZNY (+390, ±5 złota), potem monotoniczne dokładanie 29 dni (+99k vs +10k V6) BEZ skoku kaskady i BEZ upadku przeciwnika (subin rośnie gładko do 48k) — sygnatura realnego edge'u, ta sama klasa co ekstrakcja v3-vs-DN.
- Panel TOP15 (fresh 59000+, 128×15): t1b60 1770-150 (+458k) vs V6 1690-230 (+197k) — ściśle lepszy w KAŻDEJ z 15 kontroli (cooked 128-0 +63k, terry 128-0 +68k, pensukesan 128-0 +77k, him_top15 128-0 +75k, DN 91-37 held). t0b14-20 ODRZUCONY (cooked 85-43 regresja, mniej winów niż V6).
- Slow-G2 (16 gier): 16-0 +152k/g; G2-83 (taśma + patch shed, BEZ crasha — legit play) zapada się do 87-15k we wszystkich grach.
- MECHANIZM (insight strukturalny): t1-buy-85 V5/V6 to DOTACJA dla taśm dump-zależnych (subin/him/cook/terry/pens/G2-83 balansują dzień 0 na cenie t1); buy-60 wstrzymuje popyt → ich ekonomia dnia 0 nie domyka się (fail hire/krowy), nasza rośnie gładko. t1b60 nigdy nie zapada się sam (30 taśm × 128 gier, zero dipów).
- KORONACJA: `agents/champion_tape_v7.py` = V6 + t1 buy60. Submit-queue: v3 (A/B#1, spójność) → V7 (A/B#2). V6 pozostaje fallbackiem.
- Screen3 `opening3` (mikro-grid t1 buy×sell, 11×16, 5632 gier, seedy 60000): sufit — wszystkie warianty 32-0 ze światem oprócz DN; buy40 rank1 (DN 21-11 +2 = szum, T-mirror 32-0), sell 75-150 flat, buy70+ gubi lustra. b40 → holdout screen3-holdout (seedy 61000+, w drodze).

## 2026-09-10 (10): peer 0712c audit + b40 rejection
- Gałąź 0712c „V7 market probe” jest byte-for-byte identyczna z naszym `champion_tape_v7.py` (SHA taśmy `0ef9d8afb6134e1e`). Nie jest to konkurencyjny nowy mistrz, lecz niezależny import naszego t1b60.
- Ich pełny audit 105 polityk TOP15 × 8 seedów × oba seaty potwierdził V7: 1603-77/1680, +27435/g vs V6 1527-153, V3 1510-170, V2/V16 1471-209. Reużywalny insight: pełne 105-policy corpus gate jest silniejszy niż 15 reprezentantów.
- Lokalny slow-G2 b40: 16-0, +153393/g (uruchomiony lokalnie, nie Actions).
- b40 panel TOP15 fresh 62000+: ODRZUCONY jako następca V7 mimo wygrania lustra 127-1. Regresja MTMR 88-40 +4305 vs V7 101-27 +12531; niższa marża cooked 61920 vs 64927. Wniosek: buy40 przesuwa rock-paper-scissors, nie dominuje populacyjnie.
- Następnie: panel kompromisów t1 buy45/50/55 vs V7 × TOP15, fresh 63000+.

## 2026-09-10 (11): peer-V6 crossover result; b55 only survivor
- Peer V6 differs from V7 exclusively at t1 market: peer `SELL13, BUY5`; V7 `BUY60, SELL90, BUY5`. Wszystkie 718 pozostałych tur i hands są identyczne.
- Cross panel fresh 64000+ (8 peer hybrids + b55 + V7 × TOP15 + mirrors): exact peer V6 899-189 (+12845), wyraźnie słabszy od V7; wszystkie hybrydy SELL13 z dodatkowym buy są niestabilne/katastrofalne. Kolejność jest load-bearing: BUY po SELL jest szczególnie fatalny (postb60 2-1086, -101k/g). Nie przenosić bloku peer-V6 do V7.
- Micro panel fresh 63000+: b55 1791-129 (+31050/g) vs V7 1789-131 (+30738/g); b45/b50 po 1712-208. b55 zachowuje cooked/DN/MTMR i poprawia GJ (128-0 +8450 vs 126-2 +3736), lecz przewaga tylko 2/1920.
- b40 final panel fresh 62000+: 1762-158 (+30533/g) vs V7 1777-143 (+31508/g). ODRZUCONY: bezpośrednie lustro 127-1 było pułapką; regresja MTMR przeważa edge GJ.
- Kolejny gate: b55 vs V7 × TOP15 + V2/V3/V4/V5/V6, 128 gier/parę, fresh 65000+.

## 2026-09-10 (12): newest 84-policy TOP7 → V8 market-tail breakthrough
- New corpus from peer branch: 7 current teams × 12 latest replay policies = 84 tapes. Initial fresh audit (8 seeds, both seats): V7 1175-169 (+26779) > V2 1170-174 (+17874) > V3 1162-182 > V6 1121-223. b55 exactly same W/L as V7 and -0.71 gold paired: no V8 promotion.
- Population split: V7 crushes new Himanshu 192-0 +77621; V2 better feel-the-agi (154 vs 127 wins), Mengfei (174 vs 172), Otter (176 vs 172). Motivated V7-opening + V2-tail decomposition.
- Crossover screen (6 fresh seeds, 10080 games): `v7-v2market2` 941-67, score .9335, +29819 vs V7 925-83, .9177, +29137. Team deltas W/144: Him 144=, Mengfei 135>128, Otter 138=, Spa 142=, Unknown 114>112, binghua 144>140, feel 124>121. Worst-team .792 > .778.
- Mechanism isolated: V2 hands from t2 ≡ V7 exactly (1008/1008 equal); V2 market from t2 accounts for complete gain. Tail cuts t2/day1/day2/day3/day5 are identical in realized games, day10 slightly worse: useful market divergence is early and stabilizes before day5.
- Candidate V8m = V7 t0+t1 + V2 market from t2 + V7 hands. Gates launched: newest TOP7 12 fresh seeds 133000+ and old TOP15+V2/V3/V6 panel 128 games fresh 66000+.

## 2026-09-10 (13): V8 day6 holdout + action ablation
- Fresh newest-TOP7 holdout 12 seeds/84 policies: V7 1846-170 (+28685); d6/d56/d510 each 1843-173, but margins +29088/+29081/+29121. D6 improves paired margin +403 in 1283 vs 673 cases, yet loses 3 binary wins (Otter -2, feel -1): no promotion.
- Old TOP15 window screen: d6 (t144-168) 926-34 vs V7 923-37; DN 58-6 vs 54-10, Kanno 64-0 held. Day7 block negative. Thus tradeoff localized to 10 differing market actions on day6, mostly timing of FERTILIZER sells plus step166 FERTILIZER2→WOOL2.
- Launched single-action/group ablation (10 singles + fertilizer groups) vs old TOP15, fresh 68000+; survivors then go to newest TOP7.
- Peer 0712c reactive V8: learned selector `opponent money >=2800` picks V6 at t1; evolutionary holdout 1630-50 but static V7 also 1630-50 and higher margin. Independent Python gate initially failed 840 games; retry run pending. Treat as unconfirmed until zero-error independent gate.

## 2026-09-10 (14): day6 action ablation → fertilizer-add finalists
- Old TOP15 single/group ablation fresh 68000+: `fert-add` (V2 additions at t144,152,153,154; retain all V7 sells) 896-64 vs V7 892-68, DN 52-12 vs 50-14, Kanno 64-0 held. `fert-early` also 896-64 but lower margin; single t153 894-66. Singles t144/145/150/152/154/155/157/166/167 mostly binary-neutral. `fert-remove` catastrophic 802-158 (Kanno 50-14, GJ 48-16).
- Structural conclusion: edge is extra early-day6 FERTILIZER dumping, not replacement/timing removal and not WOOL at t166. Preserve V7 baseline sells.
- Newest TOP7 finalist holdout launched: fert-add, fert-early, s153, V7 ×84 policies×12 seeds, fresh 135000+.

## 2026-09-10 (15): static pulse rejected broadly; conditional-router foundation
- Final old representative holdout fresh 69000+: V7 2191-113 vs s153/fert-add 2189-115; DN pulse 99-29 vs V7 101-27. Slow-G2 s153 passed 16-0 +152282/g, but binary broad gate wins over slow gate.
- Independent peer complete 105-policy TOP15 ×12 seeds: V7 2387-133 vs exact s153 pulse 2379-141; pulse +134 own reward but -58 margin. TOP30 binary identical 178-122, pulse -23 reward/-16 margin. Static t153 REJECTED as V8; it was screen-selected noise on 15/84 policy subsets.
- The earlier 941-67 market-tail breakthrough was a valid selection-screen result, later invalidated by independent old-population holdout (Kanno 70-58). Its value was causal localization t2→day5-10→day6→t153, not promotion.
- Next direction: fail-closed state-gated t153 pulse. Added Rust `MarketOverlay` primitive with pulse turn/qty and public opponent-money, fertilizer-market-inventory, own-fertilizer bounds; default disabled. Unit test verifies activation and fail-closed path. CI foundation queued.

## 2026-09-10 (16): shallow pulse router newest-TOP7 search
- Rust router CI green (fmt/test/clippy/full simulator CI).
- Search 100464 games on 84-policy newest TOP7: every holdout finalist tied V7 binary at 1278-66; no router creates wins. Best economic rule: pulse iff opponent money <=100 at t153, own fertilizer >=1 (own>=1/2/3 equivalent): +76.6 own reward, +98.0 margin, zero team regressions. Inventory>=10050: +46 reward/+90 margin. These are economic/selectivity signals, not promotion.
- Next: independent full 105-policy TOP15 search with same fixed grid and fresh seeds. Require rule-family transfer across corpora; otherwise abandon t153 router rather than overfit.

## 2026-09-10 (17): independent full-TOP15 router search → fixed cross-corpus gate
- Full 105-policy TOP15 independent search (125580 games): best pulse profiles 1622-58 vs identity V7 1620-60, zero team regressions; many thresholds collapsed to identical behavior (`money<=2500..20000`, `inventory>=9900..10020`), indicating sparse/discrete activation rather than a stable calibrated boundary.
- Newest-TOP7 winner `money<=100` was not selected among TOP15 finalists; no direct rule-family transfer established. Do not promote.
- Launched preregistered fixed-rule final gate: identity, unconditional-own1, money<=100/500/2500, inventory>=10050 and two intersections; combined 84+105=189 policies, 32 fresh seeds, both seats (~96768 games). No post-hoc threshold selection. If no binary cross-corpus gain, abandon t153 router.

## 2026-09-10 (18): fixed router gate closes t153; all-turn mutation scan
- Preregistered combined gate: 189 policies ×32 seeds ×2 seats ×8 profiles = 96768 games. `money<=100` exactly ties V7 binary globally and per corpus: 11175-921; +61 own reward/+39 margin overall, zero team regressions. New7 margin +93, full15 margin -4. No ranking win → t153 router CLOSED (economic curiosity only).
- Broader rules overactivate: unconditional/`money<=2500` lose 8 wins (11167-929); inventory>=10050 shifts +2 wins new7 but -2 full15 and regresses 2 teams. Confirms no transferable binary edge.
- Next unbiased search launched: transplant each individual differing V2 market action into V7 across all 719 turns; screen directly on combined 84+105 policy corpora, then fresh-seed holdout top30. This generalizes the successful causal ablation beyond hand-picked day6.

## 2026-09-10 (19): all-turn scan + repaired V4/V5 audit
- All 114 differing V2 market turns scanned singly on combined 189 policies (183708 games). Holdout: t153 2834-190 vs V7 2830-194, t154/t152 2833-191, but this conflicts with preregistered 32-seed gate where t153 tied exactly and prior full gate where it lost. Confirms seed variance/selection winner's curse; no promotion. Late screen winners t649/650 did not survive holdout.
- Exact structural audit: V5 differs from V7 ONLY at t0,t1; remaining 717 turns identical. Therefore V7 is already repaired V5.1. buy55 remains alternate t1 microvariant, not confirmed better.
- V4 differs from V7 at 43 turns (40 market, 4 hands including overlap), so repaired V4 is a genuinely distinct body. Created `v4safe01` (V7 t0+t1), `v4safe0`, `v4safe1`, plus raw control. Broad matched audit launched on latest uploaded TOP7 and full 105-policy TOP15, 8 fresh seeds each, controls V7+b55.
- Latest TOP7 manifest generated 2026-09-10 18:19 UTC: SpaTaro 3113.9, Otter 3018.8, Unknown 2989.3, feel 2982.4, Himanshu 2976.6, Mengfei 2972.4, binghua 2966.4.

## 2026-09-10 (20): repaired V4 broad audit → component scan
- Latest TOP7 (84 policies×8 seeds): V7/b55 1205-139; v4safe01 1204-140 (-347 margin/-441 reward); v4safe0 1158-186; v4safe1 1148-196; raw V4 1158-186.
- Full TOP15 (105×8): V7=b55=v4safe01 exactly 1584-96 binary; v4safe01 -391 margin/-282 reward. t0-only 1514-166; t1-only 1335-345; raw 1417-263. Both opening fixes jointly necessary; safe01 near-binary but economically dominated.
- V5 differs from V7 only t0/t1, so V7 literally is repaired V5.1; buy55 is a neutral microvariant, not current champion.
- Launched V4 post-opening component scan: every individual differing market/hands/farmer component after t1 transplanted into V7, directly screened on combined latest 84-policy TOP7 + full 105-policy TOP15, fresh screen/holdout seeds. Goal: separate cancelling good/bad V4 body features.

## 2026-09-10 (21): V4 components result and fixed final gate
- 42 post-opening components, 189 policies, 126252 games. Holdout identity 2767-257. V4 market t401 and t409 each 2769-255 (+2); t360 2767-255 (+2 ties); all other leading components binary-neutral. This remains post-selection evidence only.
- Preregistered final gate launched on fresh 32 seeds for latest TOP7 and full TOP15 separately: identity, m401, m409, m401+m409, m360. No threshold/router fitting.
- Peer branch latest TOP7 baseline (2688 games/candidate): V7 2427-261, V6 2412-276, V3 2408-280, V16 2432-256. V7 exceeds V6 by 15 wins and ~3411 reward/~7759 margin per game. Peer-v6 differs from formal V6 only at t1 and is identical to V7, so there is no third hidden V6.

## 2026-09-10 (22): peer branch structured hybrid audit
- Peer branch achievement: static V7 opening + V16 tail from t2 scored 3642-390 vs V7 3607-425 on latest TOP7 (+35) but 4688-352 vs 4710-330 on TOP15 (-22); reject static hybrid.
- Fixed t1 router (`own money in [3000,3010]`) independent holdout: TOP7 +8 wins/+848 reward/+791 margin/+41 q10; TOP15 +2 wins/+66 reward/+112 margin/-96 q10. Not promotion-grade: one team regressed by 4 wins on TOP7, one by 2 on TOP15. Peer pivoted to richer public t120 trajectory fingerprints across all 189 policies.
- Avoid duplicating peer t120 search. This branch will finish independent V4 gate, then independently gate peer's eventual frozen candidate.
- Azure/GitHub log and artifact downloads both return EOF. Gate diagnostic is now emitted in small check annotations to expose the actual evaluator error without changing candidates or seeds.

## 2026-09-10 (23): current-meta reprioritization
- User correction accepted: complete TOP15 consists of ~2-day-old strategies now plausibly TOP200-500 and is historical compatibility evidence, not an equal-weight veto. Promotion priority is latest TOP7, previous TOP7, fresh seeds/both seats, then live leaderboard; old TOP15/TOP30 are secondary.
- Reclassify static V7-open/V16-tail hybrid as strongest current V8 candidate: latest TOP7 3642-390 vs V7 3607-425 (+35), +882 reward, +983 margin, improves six current teams with only -3 net wins over two teams. Old TOP15 -22 is specialization evidence, not automatic rejection.
- Imported exact peer structured hybrid for independent testing. Launched 24-seed matched gate on the immediately previous TOP7 generation versus V7 and V16; no reuse of old TOP15 as primary selector.
- V4 fixed gate failure diagnosed: evaluator requires control named `identity`; script used `v7`, causing post-simulation `StopIteration`. Corrected label only; candidates and seed range unchanged.

## 2026-09-10 (24): hybrid confirmed on second TOP7
- Previous-generation TOP7 independent 24-seed gate: hybrid 3672-360, V7 3648-384, V16 3585-447. Hybrid +24 wins, +300 reward, +483 margin vs V7 over 4032 games.
- Together with latest TOP7 +35/4032, structured V7-open + V16-market-tail is now the experimental V8 baseline; old TOP15 regression is secondary historical specialization evidence.
- Launched two-current-generation boundary scan: all actual V7/V16 differing market turns tested as (a) later hybrid start and (b) earlier return to V7. Combined latest+previous TOP7 screen; top 30 plus controls receive disjoint 8-seed holdout.
- Fixed V4 gate control label `v7`→`identity` after diagnostic StopIteration and added script path trigger.
