# Mistrz z taśm TOP15 — status 2026-09-10 (seat 087c0)

## Cel tej rundy

Użytkownik: „zrób wszystko, by stworzyć nowego mistrza" (TOP15 ~2900 score/mecz,
jego G2 max ~2400). Bramka mistrza: kandydat musi wygrać **≥50% gier przeciwko
b21 oraz v10sub** (najsilniejsze mierzalne taśmy, wiele seedów, obie strony).

**Wynik: bramka zaliczona z ogromnym zapasem.** Nowy kandydat na mistrza:
`agents/champion_tape_germanjurado1_v1.py`.

## Przełom metodologiczny: naprawa kompilacji taśm z replayów

Wcześniejsza runda skompilowała taśmy TOP15 ad-hoc i wszystkie przegrały z b21 —
**te wyniki były artefaktem błędu wyrównania wierszy i zostają unieważnione**.

Poprawne mapowanie (potwierdzone empirycznie, dokładna reprodukcja oryginalnych
meczów, co do złotówki):

- `steps` ma 720 wierszy; wiersz 0 to inicjalizacja, a akcja wykonana w kroku `s`
  jest zapisana w wierszu `s+1` → taśma `_ACTIONS = steps[1:]`, agent zwraca
  `_ACTIONS[min(step, N-1)]`;
- seat to nagrany seat drużyny z `info.TeamNames` (przy self-play: seat 0);
- bez trimowania hands (surowa taśma) — trim tylko jako opcja runtime.

Weryfikacja wierności (python engine, oba seaty z tego samego replaya, oryginalny seed):

| Epizod | Oryginał | Odtworzenie |
|---|---|---|
| SpaTaro 107210201 (seed 2059401071) | 144 820 / 131 575 | **144 820 / 131 575** |
| Otter Vibe 107217016 (seed 740417262) | 118 379 / 130 220 | **118 379 / 130 220** |
| ultimatum_game 107212126 | 177 788 / 144 720 | **177 788 / 144 720** |

## Screening 15 taśm TOP15 (best-listed submission, epizod o najwyższej nagrodzie)

Każda taśma vs v10sub: seedy 100–107 × obie strony (silnik deterministyczny
i symetryczny — obie strony dają identyczne wyniki, czyli 8 unikalnych seedów).

| Kandydat | W/L | margines/g | średnia kandydat / v10sub |
|---|---|---|---|
| terry_luo | 16-0 | **+72 413** | 130 011 / 57 598 |
| aaaabbs | 16-0 | **+73 213** | 130 450 / 57 238 |
| ultimatum_game | 16-0 | **+68 235** | 132 072 / 63 837 |
| kanno | 16-0 | +9 237 | 114 585 / 105 348 |
| germanjurado1 | 16-0 | +7 412 | 113 152 / 105 740 |
| pensukesan | 16-0 | +6 046 | 100 934 / 94 888 |
| dewangshu | 10-6 | +2 169 | 88 035 / 85 866 |
| cooked | 6-10 | −4 417 | 92 912 / 97 329 |
| mtmr_s1 | 4-12 | −5 766 | — |
| deepernet | 4-12 | −6 201 | — |
| himanshu_kumar | 2-14 | −5 526 | — |
| otter_vibe | 1-15 | −26 096 | 72 427 / 98 523 |
| binghua | 0-16 | −25 844 | — |
| spataro | 0-16 | −24 411 | — |
| mengfei_li | 0-16 | −28 798 | — |
| (kontrola) agent_b21 | 0-16 | −12 841 | 87 062 / 99 902 |

Uwaga: wielkie marginesy terry_luo/aaaabbs/ultimatum_game wynikają z załamania
statycznych przeciwników (ich wrapper gubi akcje przy dywergencji stanu), nie
tylko z siły taśmy.

## Pogłębienie (seedy 100–115 × obie strony = 32 gry na parę)

| Kandydat | vs v10sub | vs b21 |
|---|---|---|
| terry_luo | 32-0 (+68 189/g) | 24-8 (+3 258/g) |
| ultimatum_game | 32-0 (+69 989/g) | 29-3 (+10 243/g) |
| aaaabbs | 32-0 (+69 936/g) | 32-0 (+82 742/g) |
| germanjurado1 | 32-0 (+7 266/g) | 32-0 (+13 900/g) |
| kanno | 32-0 (+8 723/g) | 32-0 (+14 632/g) |
| pensukesan | 32-0 (+5 728/g) | 32-0 (+15 545/g) |
| dewangshu | 12-20 (−1 992/g) — odpada | 32-0 |

## Round-robin finalistów (seedy 100–111 × obie strony = 24 gry na parę)

- terry_luo–ultimatum_game: 12-12 (+488/g)
- terry_luo–aaaabbs: terry 24-0 (+1 825/g)
- ultimatum_game–aaaabbs: ulti 16-8 (+311/g)
- **germanjurado1**: 24-0 vs terry_luo, 24-0 vs ultimatum_game, 22-2 vs aaaabbs,
  24-0 vs kanno, 19-5 vs pensukesan — **wygrywa wszystko**
- kanno: 24-0 vs pensukesan, ale 0-24 vs germanjurado1 i 0-24 vs aaaabbs
- aaaabbs: 24-0 vs kanno, ale 2-22 vs germanjurado1

Nietransytywność (aaaabbs > kanno, kanno > terry, terry > aaaabbs) rozstrzyga na
korzyść **germanjurado1** — jedynej taśmy wygrywającej z każdym finalistą
i z obydwoma baseline'ami bez załamań przeciwnika.

## Walidacja końcowa mistrza (nowe seedy 116–131, poza treningiem selekcji)

`champion_tape_germanjurado1_v1.py` (wariant z runtime trim hands):

- vs v10sub: **32-0**, średnio 98 472 vs 92 473 (+5 999/g)
- vs b21: **28-4**, +8 393/g
- vs aastik: **28-4**, +7 487/g
- trim na seedach 100–103: 8-0 vs v10sub (+7 750/g), 8-0 vs b21 (+14 161/g)
- sanity vs reaktywny V12 (farmosa): brak błędów, 112k–170k vs 0.9k–21k
- pasywnie (seedy 100–105): **908 323** (dla kontekstu: V12 = 275 282)

Źródło taśmy: GermanJurado1 (TOP15 rank 10, public 2916.0, best-listed submission
56113029, epizod 107218640, seat 0, nagroda źródłowa 131 745). Artefakt: 719 akcji,
blob base85+zlib ~12,3 kB, plik samodzielny.

## Zastrzeżenia

- To **open-loop imitacja publicznego replaya**, nie oryginalna reaktywna polityka;
  na lidze przeciw reaktywnym rywalom przewaga będzie mniejsza niż lokalnie.
- Submisja na Kaggle: decyzja użytkownika; z tego seatu **zero** akcji Kaggle
  (brak submissionów, brak `[kaggr-submit]`, brak API key).
- Linia V12/V21 i jej bramka (275 282, seedy 100–105) pozostają bez zmian.

## Pliki

- `agents/champion_tape_germanjurado1_v1.py` — finalny kandydat na mistrza
- `scripts/compile_top15_master_tape.py` — poprawny kompilator taśm z replayów
- `scripts/h2h_tape_runner.py` — runner H2H (sekwencyjny, log per gra)
- `results/` — surowe wyniki: `screen_g{1,2,3}.json`, `deep_{1,2,3}.json`,
  `rr_{a,b,c}.json`, `final_new.json`, `final_trim.json`, `chosen.json`
- korpus TOP15: `TOP15.7z` w roocie repo (nie commitowany), rozpakowany do `/tmp`

## Dogrywka (ten sam dzień): G2/G4, szybki runner, konwergencja między gałęziami

- vs G2 (`agent_v10_subin_g2_83` z `arena/01a0712c`): **32-0**, +7 261/g, seedy
  100–115 × obie strony (`results/champ_vs_g2.json`); vs wariant G2-milk0: **32-0**,
  +6 837/g.
- vs G4 (`agent_v11_subin_g4_29` z `arena/01a0712c`): **32-0**, +14 526/g, seedy
  100–115 × obie strony (`results/champ_vs_g4.json`).
- Nowy `scripts/fast_h2h.py`: batch przez przypięty surowy symulator Python
  (`rust_port/tools/py_reference.py`, mechanika bajtowo identyczna z wheel 1.32.7),
  multiprocessing. Parzystość ze slow harness: 8/8 gier co do złotówki, w tym
  identyczne porażki z b21 (seedy 118, 127). Re-walidacja 100–131: vs subin **64-0**
  (+6 632/g), vs b21 **60-4** (+11 146/g) — 128 gier w ~9 s (~15 gier/s, ~90×
  szybciej niż 6 s/gra). Wyniki: `results/fast_valid_100_131.json`.
- **Erratum**: wcześniejsze „68-4 vs b21" podwójnie liczyło 8 gier wariantu trim
  (100–103); poprawny wynik głównego artefaktu na 100–131 to **60-4**.
- Niezależna konwergencja: gałąź `arena/01a0712c` zrekonstruowała tę samą taśmę
  (epizod 107218640) — akcje **identyczne w 719/719**, a ich świeże seedy
  (41000+, 42000+) dają łącznie 48-0 vs G2. Dwie niezależne rekonstrukcje, jeden artefakt.
- Zsynchronizowano `rust_port` (silnik + `overlay.rs`) z `arena/01a0712c`; kompilacja
  i testy walidowane w CI (`kaggriculture-rust.yml`). Lokalny Rust w tym sandboxie
  jest nieosiągalny (brak toolchaina, allowlista sieci blokujehosts Rust/artefakty),
  więc batch idzie szybką ścieżką Python — na każdej normalnej maszynie
  `cargo build --release` daje udokumentowane 100–180×.

## TOP7: detronizacja v1, nowy mistrz v2 (kanno)

Korpus `TOP7.7z` (gałąź `arena/01a0712c`, epizody z 2026-09-10 ~06:30):
SpaTaro 3055.3, Himanshu 3022.1, Otter 2988.5, binghua 2980.6,
デワンシュ 2978.8, kanno 2975.9 (sub 56133568), Yusuke Hayashi 2965.7.
Skompilowano 7 taśm (best-sub, epizod o max banku); wszystkie 7 reprodukują
źródłowe mecze co do złotówki (`results/top7_chosen.json`).

Kampania seeds 100–115 ×2 (49 par, ~1500 gier, `results/top7_campaign1.json`):
- v1 (GJ) vs TOP7: 32-0 SpaTaro (+33k, zapadnięcie), 23-9 Himanshu (+6.8k),
  30-2 Otter, 30-2 binghua, 32-0 dewangshu, **15-17 kanno (+497/g dla v1)**,
  32-0 Yusuke (+7.4k).
- Round-robin TOP7: kanno 184-8, Yusuke 144-48, Himanshu 114-78, dewangshu
  118-74, Otter 61-131, binghua 42-150, SpaTaro 9-183 (rank-1 live = czysta
  reaktywność, nie przenosi się do open-loop).
- kanno vs v1 to rodzeństwo: identyczny profil makro (259/260 hire, 2 landy d6,
  8 krów/6 owiec/3 gęsi, 163/33/31/12 seedów); różnice tylko mikro (58 kroków
  hands i 239 market, głównie dodatkowe CARE + inny mikrotiming rynku).

Walidacja świeże seedy 200-215/300-315/400-415 (`results/top7_deep_gj_kanno.json`):
v1 vs kanno **38-58**; kanno vs subin 96-0 (+8.3k vs +5.8k v1); kanno vs b21
85-11 (+11.0k vs 83-13/+10.5k v1). Vs G2 (slow, 100–115): kanno **32-0 +10.1k**
vs +7.3k v1 (`results/top7_kanno_vs_g2.json`). Łącznie kanno vs v1: **75-53**
(128 gier, dwa niezależne bloki seedów).

**Nowy mistrz: `agents/champion_tape_kanno_t7_v1.py`** (719 akcji, trim + fallback
PASS w try/except; weryfikacja: 8/8 remisów z taśmą źródłową).
Uwaga o kontrolach (sygnał live od użytkownika): G2 ~2300, G4 ~1300 — G4 jako
przeciwnik słaby (deprioritized); G2 pozostaje live-strong control. Lokalny
margines vs GJ uporządkował je poprawnie (G2 7.3k < G4 14.5k straty).

## Ablacja overlayów na v2: wszystko odrzucone (negatywny wynik)

Infrastruktura: `scripts/fast_overlay_h2h.py` (hook `overlay(action,obs,cfg)` na
surowym simie) + `scripts/bake_overlay_agent.py` + `scripts/overlay_lib/` (5
overlayów: wierne porty G2 i G4 oraz izolowane komponenty). Walidacja hooka:
fast(subin+g2exact) == slow(G2) na 6/6 gier co do złotówki.

Ablacja kanno+overlay vs nagi kanno, 100 świeżych gier (seedy 500–549 ×2):
- g2exact: 3-97, −163/g (całość szkody z milkcap; cashgate solo: 3-3-94, ±0)
- buystop(d29): 0-100, −3 963/g (zakupy dni 29–30 są load-bearing!)
- g4full: 0-100, −41 549/g (katastrofa; targety strojone pod Subina niszczą
  ekonomię kanno: 73k vs 114k)
Wniosek: overlaye walidowane na słabszych bazach nie transferują w górę; krawędź
mistrza tkwi dokładnie w mikro-decyzjach, które overlaye nadpisują. Brak
promocji do v2.1 (kryterium: udowodniony +margines na 100+ seedach).

Diagnoza porażek kanno vs v1 (18L/30W, swap0, świeże seedy): gry remisowe do
~dnia 24, rozstrzygnięcie w ostatnich ~5 dniach. Trop: miks sklepów —
porażki częściej przy YARN_STORE (1.39 vs 0.80/gra), wygrane przy
BRUNCH/ICE_CREAM (1.4 vs ~1.0/gra). Mała próba; do potwierdzenia na 200+
seedach przed projektowaniem interwencji.

## All-episode screen: v2 dethroned by its own sibling -> v3

Trop sklepowy UBITY: 200 świeżych gier kanno-vs-v1, korelacje miksu sklepów
z marginesem |r|<=0.19 (YARN -0.02, BRUNCH -0.07). Poprzedni wzorzec to był
szum z małej próby. (`results/shoptrace_800_899.json`, `scripts/trace_shops.py`)

Metodologia: identyczne taśmy dają 28 remisów + 2W/2L z idealną antysymetrią
swapów (efekt kolejności miejsc ~0.5-0.9k, znosi się dokładnie przy obu
swapach). Procedura obu-seatów pozostaje obowiązkowa.

Screening 34 taśm (WSZYSTKIE epizody best-sub TOP7, nie tylko max-bank) vs v2,
seedy 100–115: kanno_ep107381285 (bank źródłowy 59 494 — NAJNIŻSZY z 34!)
wygrywa **32-0 (+1.7k/g)**; następny najlepszy ma 8-24. Bank nie przewiduje
siły taśmy — potwierdzenie trzecie, najmocniejsze.

Walidacja fresh 200–231: vs v2 **63-1 (+1.5k/g)** (łącznie 95-1/96); vs v1
62-2; vs subin 64-0 (+7.9k); vs b21 48-16 (+8.0k, identyczne W/L co v2 na tych
samych seedach); vs yusuke 64-0; vs himanshu 63-1. Vs G2 (slow, 100–115):
**32-0 (+9.1k)**.

v2 vs v3: farmer+hands identyczne w 719/719, te same sumy (260 hire, 2 landy,
8/6/3 zwierzęta); różnica TYLKO mikrotiming rynku na 84 krokach (głównie dni
18–29, np. ten sam SELL przesunięty o kilka kroków). Cała przewaga rodzeństwa
to timing sprzedaży w endgame — zgodnie z diagnozą (decyzje w ost. ~5 dniach).

**Nowy mistrz: `agents/champion_tape_kanno_ep107381285_v1.py`** (v3).

## Przegląd LAB-a 0712c + V4 (day-crossover)

LAB rodzeństwa (Rust, ~10k gier w sekundy w CI): ich Python-fallback
(fast_static_tournament.py) to odpowiednik naszego fast_h2h — construkcja
szybkościowa już mamy. Prawdziwy łup to METODY: day-crossover search
(spójne dni 24-turowe kanno×GJ, populacja 256, holdout + regresje) oraz
sygnał live: **V16 (= nasz v2, 16/16 remisów) zdobył live 824.9**,
V15 (= v1) 1445.6, V14 milk0 1683.0 — wszystkie taśmy statyczne lądują
800–1700, daleko od G2 (~2300). Rodzeństwo unieważniło statyczny sygnał
promocji; live V2 (user submituje) to następny punkt danych.

Ich crossover-winner (maska GKK…K, +402/g nad V16) przegrywa z naszym v3
**0-16 (−1448/g)** — v3 > ich najlepszy artefakt. Ale metoda działa:
własny `scripts/search_day_crossover.py` (100 masek, S1→S2→S3, guard
hashujący taśmy w workerach), pary v3×v2 i v3×v1.

Para v3×v1: zwycięzca kid-17, maska B×9+A×21 (dni GJ 0–8 + v3 9–29),
plateau cięć 8/9/10. Holdout S3 (seedy 520–551): vs v3 **63-1 (+329)**,
vs v2 63-1 (+1639), vs b21 56-8 (tyle samo co baseline v3), vs subin 64-0.
Re-walidacja fresh 600–615: vs v3 **31-1 (+206)** → łącznie **94-2/96**.
Regresje: vs v1 16-0 (+1086), yusuke 16-0 (+9174), himanshu 16-0 (+8811).
Bramka slow vs reaktywne G2: **16-0 (+8295)**. Parity fast/slow 4/4.
Para v3×v2 odrzucona (najlepszy 27-1-36, +4/g — szum).

**Nowy mistrz: `agents/champion_tape_daycrossover_v4.py`** (v4).
Sanity pliku repo vs emisja LAB: 4/4 remisów.

## Rust LAB w Actions (bring-up OK)

Trigger push-kolejką (`lab_queue.json` + `[kg-lab]` w message), bo token
sandboxa nie ma rights do dispatch API (403). Wzorzec: build kg_sim
(cargo --release, cache Swatinem) → `run_lab_queue.py` → `rust_h2h.py`
(Rayom batche, trim per-tape) → wyniki commitowane z powrotem na gałąź.
Bring-up `bringup-v4` (run 34470368169): SUCCESS, ~1350 g/s (55x lokalnie),
parity Rust-vs-Python 8/8 na każdej parze, 0 błędów.
V4 na świeżych seedach 1000–1015: vs v3 32-0 (+303), vs v2 32-0 (+1769),
vs v1 32-0 (+1386), vs b21 26-6 (+10770), vs subin 32-0 (+5769) — zgodnie
z lokalnymi wynikami. Corpus zamrożony w repo (9 taśm).
Uwaga live: V16 (bliźniak v2) po ~20 min miał 824.9, po ~40 min już ~1500
i rośnie — unieważnienie statyków przez rodzeństwo było przedwczesne;
wyniki live dryfują w górę z liczbą gier. Czekamy na live V2.

## V4 mega-walidacja w LAB (3584 gry, seedy 2000–2255, ~3500 g/s)

vs v3 473-39 (+903/g, 92.4%); vs v2 504-8 (+2424); vs v1 498-14 (+1283);
vs b21 426-86 (+9699, 83.2%); vs subin 512-0 (+7062); vs yusuke 510-2;
vs himanshu 501-11. Łącznie 3424-160 (95.5%). V4 utrzymany — uwaga, że
win-rate vs v3 spada z ~98% (96 gier) do ~92% (512 gier): duże N ma sens
i teraz jest tanie (cały batch ~3 s + cache'owany build).

## Zwiad 0712c (head d969c683) + ewolucja V5

Rodzeństwo zaudytowało naszą gałąź i znalazło MECHANIZM v3: różnice v2→v3
to 84 kroki market, MILK/WOOL/EGG/STRAWBERRY przesunięte z fazy step%4==3
do step%4==1 — town konsumuje co 4 tury, faza 1 to sprzedaż tuż po szoku
popytowym (realizacja ceny). Sygnał town-cycle do użycia w przyszłości.

Ich broń: (1) `v3_market_genetic_holdout_winner` — ewolucja 120 bloków
rynku (8 dawców kanno, 768×5, 452k gier), 484-28 vs V3; (2) hybryda
(market-parent × NASZ V4): jednostki GJ dni 0–4 + kanno od 5, rynek
70/39/11 — niezależna bramka 10240 gier: **481-31 (+350/g) vs nasz V4**.
Weryfikacja lokalna: hybryda vs V4 13-3 (+416); market-parent vs V4
4-12 (sam nie bije V4 — opening jest load-bearing); ich rekonstrukcja
V4 = 719/719 (2-2-4, margines 0). V16 live skorygowany: wczesne 824.9 to
nie był wynik stabilny (user: 1100+, 100% win) — statyki zrehabilitowane.

Odpowiedź: własna ewolucja `search_rust_evolve.py` (Rust, kolejka Actions):
genom cut + 120 bloków, 11 dawców rynku (8 kanno z TOP7.7z + V4 + hybryda
+ market-parent), 10 kontroli, podłogi regresji vs klon V4, klony V4/hyb/V3
wstrzykiwane co generację, holdout + ostra elekcja. Pliki peer w
corpus/peer/ (verbatim + PROVENANCE.md).
