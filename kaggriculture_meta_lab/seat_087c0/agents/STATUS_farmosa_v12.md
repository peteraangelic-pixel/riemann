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
