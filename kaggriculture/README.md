# Kaggriculture — baseline agent (wątek 2026)

Kaggriculture to turowa gra-farma Kaggle: 720 tur (30 dni × 24), dwóch
graczy, wygrywa ten z większą kasą na koniec sezonu. Więcej: strona
konkursu — https://www.kaggle.com/competitions/kaggriculture

**Terminy:** wejście i merge drużyn 2026-09-23, finał submissji 2026-09-30,
dogrywka LB do ~2026-10-15. Pula $50k (10 × $5k). Dozwolone 5 submissji
dziennie; liczą się 2 ostatnie.

## Stan (2026-09-04)

- `agent.py` — **baseline v0 „wheat belt"**: jeden farmer, pszenica na
  NW-kwadrancie (sadź → podlewaj → zbierz w szczycie → zanieś do szopy →
  sprzedawaj co turę). Deterministic, bez zależności poza silnikiem gry.
- Lokalnie silnik gry działa **offline** (`kaggle-environments`); pełny
  sezon 720 tur to ~1–2 s, więc iteracja jest tania.
- Lokalny wynik v0: ~3 900 monet vs 3 000 (idle) / ~2 800 (random) — 3:0.
  To dopiero punkt startowy: ręce (farm hands), marchew, wykup ziemi i
  zwierzęta mają duży potencjał poprawy.

## Użycie

```bash
make setup       # venv + kaggle-environments (raz)
make test        # testy offline (kontrakt akcji, determinizm, przewaga nad idle)
make match       # lokalny mecz vs OPPONENT=pass|random|self
make benchmark   # szybki przegląd vs pass i random
```

## Architektura

- Sandbox (Arena) **nie ma** łączności z Kaggle; runner GitHub Actions ją ma.
  Dlatego: kod i testy rozwijamy offline, a walidację/submisję odpalamy na GH
  Actions (workflow `kaggriculture.yml`) z sekretami Kaggle.
- Sekrety **nigdy** nie są w repo. Lokalnie poświadczenia trzymaj w
  `kaggriculture/.kaggle/` (gitignored); na GitHub użyj secrets
  `KAGGLE_USERNAME` / `KAGGLE_KEY` (i opcjonalnie `KAGGLE_API_TOKEN` dla
  nowego formatu klucza `KGAT_...`).

## Submisja Kaggle

Silnik symulacyjny Kaggle ładuje `main.py` z funkcją `act(obs, config)`.

```bash
make pack         # buduje submission.tar.gz (main.py + agent.py) — offline
```

Właściwy upload robi workflow (ręczny dispatch z `submit=true` albo commit z
`[kaggr-submit]`), o ile w repo ustawiono sekrety Kaggle. Pierwsza submissja
przechodzi **Validation Episode** (agent gra sam ze sobą); logi błędów
pobierzesz przez `kaggle competitions logs <episode> 0`.

## Znane ograniczenia v0 (kolejność prac)

1. Jeden farmer bez rąk — ok. 8 roślin to max przy 1 akcji/turę; zatrudnianie
   rąk (koszt fib: 1,1,2,3,…/dzień) powinno znacząco podbić areał.
2. Tylko pszenica; marchew (lepszy przychód/tile) i melon (drogi, 1-tile) —
   następne.
3. Wykup ziemi ($1k/$2k/$4k) przy nadmiarze gotówki.
4. Handel: obecnie sprzedajemy od razu; przy dynamicznych cenach lepsze jest
   trzymanie towaru i sprzedaż w szczycie popytu (shopy odblokowują się co 3
   dni — patrz `town`).
5. Zwierzęta (gęsi/krowy/owce) — stały dochód, ale wymagają paszy (pszenica)
   i budynków; dopiero po stabilnym crop-loopie.
