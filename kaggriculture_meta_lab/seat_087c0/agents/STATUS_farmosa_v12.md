# FarmOS v1 — seat 087c0 — status 2026-09-09

Agent: `agents/farmosa_v1.py` (aktualny kandydat = „v12”). Benchmark lokalny na
seeds 100–105 (vs pasywny przeciwnik, 720 kroków, kaggle_environments).

## Wyniki (final reward, 6 seedów)

| seed | v8 (zone rewrite) | v9 (+ew. dogrywanie/feeding) | v10 (+przewóz towarów) | **v12 (aktualny)** |
|------|------:|------:|------:|------:|
| 100  | 39288 | 47355 | 50253 | 49277 |
| 101  | —     | 46051 | 39970 | **46296** |
| 102  | —     | 37083 | 36730 | 35909 |
| 103  | —     | 36650 | 45848 | 43839 |
| 104  | —     | 27192 | 38729 | **39411** |
| 105  | —     | 50060 | 53922 | **60550** |
| **Σ** |       | **244391** | **265452** | **275282** |

v12 = v10 + start wieczornego „water sweepu” o h≥17 (zamiast h≥20).

## Co się sprawdziło w tej sesji

1. **Podział stref (v8)** — każdy robotnik ma prywatny, zbalansowany pas pól
   (row-major) i rano pracuje wyłącznie w swoim pasie; plus dedupe `claimed`
   w obrębie tury. Koniec „stada” robotników na jednym polu.
2. **Wieczorny water-sweep h≥17 (v12)** — gwarantowane podlewanie wszystkich
   roślin tego samego dnia, potem dobijanie karmienia. Największy pojedynczy
   zysk sesji (szczególnie seed 101: +6.3k i 105: +6.6k vs v10).
3. **Przewóz towarów h≥9 (v10)** — worker z ≥5 szt. produktów (poza pszenicą)
   w inwentarzu odwozi je do szopy zamiast stać z pełnym inwentarzem; odblokowuje
   zbieranie nawozu/mleka/wełny. Duży zysk na seed 104 (+12k vs v9).

## Co NIE działało (ślepe zaułki)

- **Zakup zwierząt w późniejszych, „staged” terminach** (COW d8, SHEEP d9/d15,
  GOOSE d12; szersze okna) — seed 100 spadł z ~47k do ~37k. Cofnięte.
- **Zwracanie pszenicy do szopy po nakarmieniu** — workerzy potem nie podlewali;
  katastrofa (wszystkie seedy <34k). Cofnięte.
- Feed = kupno tylko przy cenie ≤120 i tylko na bazie szopy; wymóg docelowy
  `feed_need + 8` pszenicy (siano trzymane w shed).

## Znane luki (następne kroki)

- Na seedzie 101/104 stado nie dochodzi do celu (8 krów / 5 owiec / 3 gęsi):
  po d13 1–2 sztuki potrafią tygodniami leżeć w shed — transport zwierząt
  przegrywa priorytet z podlewaniem/zbieraniem.
- Wieczorem (23:00) ~10 roślin zostaje niepodlanych w d14–28 mimo sweeepu —
  zbyt mało rąk na wodę vs. karmienie/zbieranie (12 robotników + farmer).
- Strawberry (d24–26) potrafią „zniknąć” (2 dni niepodlane → WEED) w fazie
  sadzenia marchwi — ręce są wtedy na wykopkach/zbieraniu.
- Finalna konwersja d29: zboże/owoce zostają w ziemi — warto dołożyć
  „liquidate sweep” w d28 wieczorem.

## Eksperyment v13 (nawożenie pól zamiast sprzedaży nawozu) — MIESZANY, nie promowany

Prototyp: `agents/variants/farmosa_v13_fert.py`. Robotnik z FERTILIZEREM
w inwentarzu (ze zbiórki przy zwierzętach) aplikuje go na najbliższą
nienawożoną pszenicę/marchew w oknie zbioru (zamiast zanosić do szopy).

Mechanika potwierdzona w silniku: WATER w oknie bonusowym daje +1 (+2 gdy
`fertilized_until_day >= day`); FERTILIZE działa 3 dni i zużywa nawóz
z inwentarza robotnika (nie z szopy). Ceny seed 100: FERT ~85, WHEAT ~44,
CARROT ~58.

| seed | v12 | v13 (fert) | Δ |
|------|-----|-----|-----|
| 100 | 49277 | 53322 | +4045 |
| 101 | 46296 | 52180 | +5884 |
| 102 | 35909 | 32381 | −3528 |
| 103 | 43839 | 41261 | −2578 |
| 104 | 39411 | 33156 | −6255 |
| 105 | 60550 | 55032 | −5518 |
| **Σ** | **275282** | **267332** | **−7950** |

Wniosek: nawożenie samo w sobie jest wartościowe (duże zyski na seedach
100/101), ale detour do FERTILIZE kradnie ręce wieczornemu water-sweepowi
na innych seedach. Kolejna iteracja powinna bramkować nawożenie dopiero,
gdy wszystkie rośliny w strefie są podlane (np. za water-sweeepem h≥17)
lub ograniczyć zasięg/okno aplikacji (marchew d26-28; pszenica tylko gdy
roślina ma zapewnione podlewanie).

## Head-to-head vs agenci gałęzi arena/01a0712c-riemann — V12 NIE jest konkurencyjne

Ich równoległa sesja zaaudytowała V12 (`agents/variants/agent_farmosa_v12_087c0.py`
na 01a0712c) i zapisała wynik w `kaggriculture_meta_lab/results/
farmosa-v12-cross-branch-holdout-20260910.json` (commit 7f0918d):

| kontrolny agent (01a0712c) | mecze | W/L | win rate | średnia marża | v12 | opp |
|---|---:|---:|---:|---:|---:|---:|
| agent_v9_b21_s16 | 32 | 0/32 | 0% | −139 397 | 15 234 | 154 630 |
| agent_v10_subin_106845775 | 32 | 0/32 | 0% | −138 923 | 15 480 | 154 404 |
| agent_v11_subin_g4_29 | 32 | 0/32 | 0% | −122 614 | 14 540 | 137 154 |

Potwierdzenie własnym rerunem (seedy 100–103 × obie strony, 8 meczów):
v9_b21_s16 −143 759 (12 234 vs 158 096), v10_subin −135 814 (8 429 vs 144 243),
v11_g4_29 −125 020 (10 969 vs 135 989).

Wniosek: wyniki ~27–60k/mecz V12 to wyłącznie gra przeciw PASYWNYM
przeciwnikom (6 seedów; Σ 275 282 = suma, nie jeden mecz). W realnym
head-to-head z agentami elity V12 zarabia ~8–15k, a oni 135–158k — skala
ekonomii jest ~10× mniejsza (census TOP15: zwycięzcy realnych epizodów do
177 788, średnia ~97 700). Kaggle LB (~2900 pkt) to inna metryka rankingowa,
nie złoto. V12 NIE wysyłać na Kaggle.

Skala różnicy (census TOP15, DeeperNet): ~20k jednostek pszenicy sprzedanej,
16k mleka, 260 hire'ów w sezonie, 46 zakupów nawozu — vs moje ~kilkaset
jednostek i sprzedaż nawozu zamiast użycia. Luka ma charakter strukturalny
(architektura ekonomii), nie strojenia — poprawki typu v13 (nawożenie) dają
pojedyncze %, nie ~120k.

## Eksperymenty „większej skali” (v14–v16) — WSZYSTKIE przegrywają z v12; werdykt architektoniczny

Motywacja: census TOP15 (210 epizodów, 69 drużyn) — profil elity vs my:
elita: 2 krowy + 2 owce już d0–2 (owce! nie d10), 8 krów i 5–8 owiec do d12,
truskawki ~20–35, pszenica 20–32 w konwejerze cały sezon, marchew ~15–30 na
końcu, ~260 hire'ów/sezon, kupno ~46 nawozu + sprzedaż nadmiaru, pełna
likwidacja na d29 (nagroda = gotówka). Rewards elit do 177 788/mecz
(średnia ~97 700). Nasze v12 = ~46k/mecz vs pasywny.

Próby (wszystkie mierzone, seedy 100–105, vs pasywny):

| wariant | zmiana | Σ 6 seedów | vs v12 |
|---|---|---|---|
| **v12 (kanon)** | — | **275 282** | — |
| v14 | owce od d1, ręce +1–2, konwejer pszenicy 22–45, marchew 40, kapity sprzedaży, likwidacja d28 | 157 637 | −117 645 |
| v14b | jak v14, konserwatywniej | 75 558 | −199 724 |
| v14c | v14b + ochrona płynności (zakaz zwierząt <floor+300 do d9, sprzedaż całego nawozu <d10) | 209 439 | −65 843 |
| v15 | v12 + użycie nawozu h≥21 gdy NIC niepodlanego + keep fert 4 | 250 801 | −24 481 |
| v16 | v13 + użycie nawozu h≥10 gdy WŁASNA strefa podlana | 228 976 | −46 306 |

Mechanizmy porażki (zdiagnozowane trace'ami):
- **Kaskada płynności**: dodatkowe wczesne wydatki (owca d1 = 500) potrafią
  zepchnąć gotówkę poniżej progu floor (300), co blokuje **wszystkie** hire'e
  na 2–10 dni → melony niepodlane → WEED → spirala (s100 v14b: 535 zł).
- **Bariera podlewania**: przy 23:00 i tak ~10 roślin niepodlanych nawet przy
  25–35 roślinach (v12); każde zwiększenie areału bez zwiększenia przepustowości
  podlewania tylko mnoży WEED. v12 jest silnym lokalnym optimum swojej
  architektury.
- Nawóz: zysk tylko na seedach z nadmiarem rąk (100/101: +4–6k w v13), strata
  na pozostałych — aplikacja kradnie czas water-sweeepowi. Bramki (globalna
  h≥21 / lokalna strefa) nie naprawiają tego.

Wniosek strategiczny: różnica do „championów” z gałęzi 01a0712c
(137–158k w head-to-head, 0:32 w audycie krzyżowym) nie jest parametrami —
ci agenci kontrolni to **open-loop replaye** taśm TOP15 (blob b85, np.
`agent_v9_b21_s16.py`, 11 linii) działające wg stałego harmonogramu 720
kroków. Dogonienie ich wymaga zmiany architektury, nie strojenia:
(1) jednostkowy planer reaktywny z scoringiem akcji (ruch/wybór pola/siew/
woda/zbiór/nawóz/budowa/zwierzęta) wg planu z gałęzi głównej; (2) ekonomia
skali jak wyżej; (3) dopiero potem ew. mały model wybierający bezpieczne
akcje planera. To robota na kolejne sesje, nie na pojedyncze patche.

## Uruchamianie benchmarku

```bash
cd kaggriculture_meta_lab/seat_087c0
/tmp/kgvenv/bin/python -u - <<'EOF'
import importlib.util, sys
sys.path.insert(0, ".")
spec = importlib.util.spec_from_file_location("farmosa", "agents/farmosa_v1.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def passive(obs, config=None): return {"farmer":["PASS"],"hands":[],"market":[]}
from kaggle_environments import make
for s in (100,101,102,103,104,105):
    env = make("kaggriculture", configuration={"episodeSteps":720,"seed":s}, debug=False)
    env.run([m.act, passive])
    print("seed", s, "final:", env.state[0].reward)
EOF
```
