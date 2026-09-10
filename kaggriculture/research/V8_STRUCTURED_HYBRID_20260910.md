# V8 structured V7/V16 hybrid — 2026-09-10

## Question

Re-test the earlier V7-opening/older-market-tail construction on the completely replaced latest TOP7, and determine whether its complementary strengths can support a conditional V8.

The candidate keeps V7 hands and market actions at turns 0–1, then uses the V16/V2 market tape from turn 2 onward. It differs from V7 in 226 seat/turn action records. This is the same causal family previously screened by branch 087c0, now evaluated on the latest uploaded corpus and complete TOP15 with substantially larger matched gates.

## Run

Actions run `34518137372`, Rust engine, zero errors:

- latest TOP7: 84 policies × 24 seeds × both seats = 4,032 games/candidate;
- complete TOP15: 105 policies × 24 seeds × both seats = 5,040 games/candidate;
- V7 and V16 controls use identical seeds.

## Latest TOP7

| Candidate | W–L | Own reward | Margin |
|---|---:|---:|---:|
| **hybrid** | **3642–390** | **107,749.91** | **+27,439.20** |
| V16/V2 | 3615–417 | 103,115.76 | +19,740.46 |
| V7 | 3607–425 | 106,868.04 | +26,455.88 |

Hybrid minus V7: **+35 wins**, +881.87 own reward and +983.32 margin. It improves six current teams and loses three net wins over two teams. This is a real, broad newest-meta signal, not merely the earlier five-win V16 fluctuation.

## Complete TOP15

| Candidate | W–L | Own reward | Margin |
|---|---:|---:|---:|
| **V7** | **4710–330** | 105,016.49 | +26,429.10 |
| hybrid | 4688–352 | **105,924.05** | **+27,148.18** |
| V16/V2 | 4388–652 | 97,214.44 | +10,577.90 |

Hybrid minus V7: **−22 wins**, despite +907.57 own reward and +719.08 margin. Most binary damage is concentrated in one old opening family (−32), partly offset by gains elsewhere.

## Opening-strategy signatures mined from replay sources

Grouping matched outcomes by the opponent's recorded turn-0 market action reveals a strong separable pattern:

- a single wheat purchase of 13: hybrid +21 latest-TOP7 wins and +6 complete-TOP15 wins;
- cow purchase of 2: +8 latest and +2 TOP15;
- several high-hire/animal openings: positive or neutral on both corpora;
- wheat purchase 13 followed by wheat purchase 60 and sale 60: **−37 TOP15 wins**;
- wheat purchase 13 followed by sale 6: −6 TOP15 wins;
- the buy-13/sell-13/buy-13 family is approximately neutral overall, although V7 remains important on selected current policies.

Several opposing openings have the same net wheat-inventory effect, so wheat inventory alone cannot distinguish them. Their transaction order changes post-turn-0 money, while high-hire openings also expose a different public hand count. This supplies a concrete feature basis for the next selector: opponent money plus hand count and selected market inventories after turn 0.

## Revised decision after corpus-age correction

The complete TOP15 archive is roughly two days older than the latest TOP7 and represents a substantially older leaderboard population. It remains useful as a legacy robustness/adversarial stress test, but it must **not veto a candidate that transfers across the latest and immediately previous TOP7 generations**. Earlier wording gave TOP15 too much promotion authority and understated the hybrid.

The static hybrid is therefore restored as the primary V8 candidate. It dominates V7 on the latest TOP7 screen in wins, own reward and margin; branch evidence also showed a win gain on the immediately previous TOP7 generation. TOP15 is reported separately as legacy-regression evidence and may motivate a router, but is no longer the main objective.

The required two-generation gate subsequently passed in run `34527997807`:

| TOP7 generation | Hybrid | V7 | Win delta | Reward delta | Margin delta |
|---|---:|---:|---:|---:|---:|
| latest, 32 seeds | **4906–470** | 4845–531 | **+61** | +1,014.21 | +1,231.04 |
| immediately previous, 24 seeds | **3645–387** | 3620–412 | **+25** | +644.72 | +837.61 |

Across the two principal current-meta generations the hybrid gains **86 wins** over V7 while improving both own reward and margin in each independently seeded gate. V16 itself loses to V7 on both generations, confirming that the gain comes from the structured V7-opening/V16-market-tail combination rather than simply selecting the older complete policy.

The policy was neutrally packaged as `agent_v8_market_tail.py`. Its decoded action SHA-256 is exactly identical to the tested LAB hybrid (`2f23d0850e9dbd3d32571fab602652af76062f10b9982925b3073175d20a488b`). Run `34528613807` then executed the exact promoted source through Kaggle Environments 1.32.7 against 14 latest-TOP7 replay policies in both physical seats: 28 games, **zero agent errors**. V8 market-tail is therefore promoted as the current local champion under the corrected current-meta objective.

The fail-closed selector remains valuable if it can preserve current-meta gains while cheaply retaining historical robustness. Candidate selection and final gates still require disjoint seeds, and exact generated Python source requires an independent execution check.

## First fixed router and independent holdout

Exact Rust traces of the public post-turn-0 state exposed a compact selection signal. A preregistered first router latched the hybrid tail when own money after turn 0 was in `[3000, 3010]`; otherwise it retained V7. Selection evidence predicted gains on both corpora, so it was frozen before run `34521271714`.

Independent 16-seed holdout:

| Corpus | Router | V7 | Win delta | Reward delta | Margin delta | q10 delta |
|---|---:|---:|---:|---:|---:|---:|
| latest TOP7 | 2431–257 | 2423–265 | **+8** | +848.00 | +791.39 | +41 |
| complete TOP15 | 3176–184 | 3174–186 | **+2** | +66.02 | +111.59 | **−96** |

The router preserved an aggregate gain on unseen seeds. Under the corrected corpus priority, its +8 latest-TOP7 wins and simultaneous improvements in reward, margin and q10 are positive current-meta evidence. A four-win per-team shift and the shrinkage from +35 to +8 still require a larger current/previous-TOP7 holdout. The two-win TOP15 gain with lower TOP15 q10 is retained as secondary historical-risk evidence, not as a promotion veto.

A safer post-opening rule (`opponent money <= 2200`) was diagnostically team-safe on the TOP15 holdout (+4 wins and +39 q10), but still inherited the same four-win latest-TOP7 regression because distinct current policies share an identical turn-0 fingerprint. It must not be selected post hoc without another holdout.

This identifies the technical limitation of turn-1 routing: materially different replay tails can produce the same immediate public fingerprint. Branch 087c0 previously established that hybrid tails starting at turns 2 through 120 often realize identically, so the next experiment delays the decision to turn 120 and uses the evolved public trajectory (money, hands, unlocked land, tile composition and market vector). Exact turn-120 traces were collected in run `34521812851` for all 189 policies and both seats.

## Latest peer-branch check

Branch `arena/01a087c0-riemann` through `09e2c56` scanned all 42 post-opening V4 components over 189 policies (126,252 games). Steps 401 and 409 showed only +2 post-selection holdout wins; step 360 converted losses to ties. Its preregistered component gate has failed three times at the evaluation step and has not produced final evidence, so none of these components is imported yet.

## Artifacts

- `kaggriculture_meta_lab/agents/candidates/agent_v8_lab_safe_open_old_market.py`
- `kaggriculture_meta_lab/agents/candidates/agent_v8_market_tail.py` — promoted current local champion
- `kaggriculture_meta_lab/agents/candidates/agent_v8_tail_router.py`
- `kaggriculture_meta_lab/results/v8-tail-router-new7-composite-holdout-20260910.json`
- `kaggriculture_meta_lab/results/v8-tail-router-top15-composite-holdout-20260910.json`
- `kaggriculture_meta_lab/results/v8-trajectory120-latest-top7-20260910.json`
- `kaggriculture_meta_lab/results/v8-trajectory120-top15-20260910.json`
- `kaggriculture_meta_lab/results/v8-structured-hybrid-latest-top7-20260910.json`
- `kaggriculture_meta_lab/results/v8-structured-hybrid-top15-20260910.json`
- `kaggriculture_meta_lab/results/v8-two-top7-latest-20260910.json`
- `kaggriculture_meta_lab/results/v8-two-top7-previous-20260910.json`
- `kaggriculture_meta_lab/results/v8-market-tail-python-validation-20260910.json`

## Korekta po najnowszym TOP12: router stanowy V9

Najnowszy TOP12 odwrócił wynik bezwarunkowego V8: V7 wygrał 5743/6912, a V8
5713/6912. Regresja była skupiona w dwóch stabilnych odciskach stanu po turze
zerowej. Pierwszy ma własne pieniądze 2957, pieniądze przeciwnika 323 i sześć
rąk; drugi ma po obu stronach 3000 i zero rąk przeciwnika. Nazwy zespołów nie
są częścią agenta ani jego publicznego opisu.

`agent_v9_market_adaptive.py` zatrzaskuje wybór po obserwacji tury 1. Dla tych
dwóch klas zachowuje V7, a dla pozostałych używa ciała V8. Jest to selekcja
wyłącznie na podstawie publicznego stanu gry i kończy się bezpiecznie na V7 po
wyjątku. Tablice obu gałęzi są bitowo/action-wise identyczne z V7 i V8; ich
pierwsze dziesięć tur także jest identyczne. Dlatego złożenie odpowiadających
wierszy z istniejącej bramki matched jest dokładnym kontrfaktycznym wynikiem,
a nie przybliżeniem:

- TOP12: **5811–1101**, średnia nagroda **103892.31**, margines **21482.91**;
- rangi 1–7 nowego TOP12: **3186–846**, nagroda **105070.97**, margines
  **22501.76**;
- wobec V7 daje to odpowiednio **+68** i **+21** zwycięstw;
- na wcześniejszym TOP7 wszystkie zebrane odciski wybierają V8, więc V9
  zachowuje wcześniejszą przewagę V8 **+61** zwycięstw nad V7.

Pełny audyt per-team jest w
`kaggriculture_meta_lab/results/v9-state-router-exact-counterfactual-20260910.json`.
To nadal bramka przeciw taśmom open-loop; router nie powinien być promowany bez
małego testu silnika Python i porównania z żywym punktem odniesienia G2.
Pełna dynamiczna bramka Python została przerwana przez limit czasu, nie przez
błąd agenta; do szerokich badań należy używać dokładnego składania statycznych
gałęzi albo dodać natywne wsparcie routerów w porcie Rust.

### Bramka zamkniętej pętli względem G2

Run Actions `34534701779` wykonał 64 gry na 32 rozłącznych seedach i obu
miejscach przeciw dokładnemu źródłu G2. V9 wygrał **64–0**, bez błędów;
średnia nagroda V9 wyniosła **156406.11**, G2 **2650.84**, a margines
**153755.27**. To potwierdza poprawne wykonanie dynamicznego routera w silniku
Kaggle Python i eliminuje G2 jako bezpośredni kontrprzykład H2H. Nie oznacza
to automatycznie lepszego wyniku publicznego: ranking jest mieszanką innych
przeciwników, a wcześniejszy wynik live G2 pozostaje ważnym ostrzeżeniem przed
utożsamianiem lokalnego H2H z ratingiem.

## Oficjalny V8 z gałęzi 087c0 i decyzja przed wysłaniem (2026-09-11)

Zaimportowano i sprawdzono promowany w `arena/01a087c0-riemann` wariant z
commita `30b6f79`: V7 do tury 400, a następnie późny ogon rynku. Na wspólnym
panelu 276 polityk, 16 seedach i obu miejscach osiągnął 7932-900 wobec
7850-981-1 V7. Rozbicie: najnowszy TOP7 +19 wygranych, poprzedni TOP7 +14,
TOP12 +49. Pełny ogon od tury 2 miał tylko +38 łącznie i przegrał wszystkie
288 gier z jednym nowym odciskiem strategii; późny wariant nie ma tej awarii.

Utworzono neutralny `agent_v10_late_market_adaptive.py`: zachowuje późny V8,
ale dla odcisku otwarcia 3000 pieniędzy i zero rąk przeciwnika wraca do V7.
Dokładne złożenie matched rows daje na TOP12 2948-508, czyli +51 wygranych nad
V7 i +2 nad oficjalnym późnym V8; oba TOP7 pozostają identyczne z późnym V8.
Bramka Kaggle Python `34535750918` zakończyła się bez błędów: 32-0 z G2 oraz
2-2-28 bezpośrednio z V9 (średni margines zero). Rekomendowana kolejność prób:
V10 adaptive late-market, oficjalny statyczny late-market V8, następnie V9 jako
bardziej agresywny i odmienny eksperyment. Nie wyłączać stabilnych zgłoszeń
V16/G2 przed ustabilizowaniem nowych ratingów.
