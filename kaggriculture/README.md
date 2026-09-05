# Kaggriculture — agent (wątek 2026)

Kaggriculture to turowa gra-farma Kaggle: 720 tur (30 dni × 24), dwóch
graczy, wygrywa ten z większą kasą na koniec sezonu. Więcej: strona
konkursu — https://www.kaggle.com/competitions/kaggriculture

Oficjalne pliki pobrane po dołączeniu do konkursu znajdują się w katalogu
głównym: [`AGENTS.md`](../AGENTS.md) (agent, submission i CLI) oraz
[`README.md`](../README.md) (pełne zasady i ekonomia). Ich specyfikacja jest
zgodna z lokalnie testowanym silnikiem `kaggle-environments 1.32.7`.

**Terminy:** wejście i merge drużyn 2026-09-23, finał submissji 2026-09-30,
dogrywka LB do ~2026-10-15. Pula $50k (10 × $5k). Dozwolone 5 submissji
dziennie; liczą się 2 ostatnie.

## Stan (2026-09-05)

- `agent.py` — **v2: pszeniczno-marchewkowy conveyor z melonem i rękami
  do pracy**. Deterministic, bez zależności poza silnikiem gry; bez pamięci
  między turami (czysta funkcja obserwacji).
- Silnik gry działa **offline** (`kaggle-environments`); pełny sezon 720 tur
  to ~2 s, więc iteracja jest tania.
- Uczestnictwo konta konkursowego i akceptacja regulaminu zostały potwierdzone;
  kandydat v2 jest gotowy do walidacji online i zbierania replayów potrzebnych
  do strojenia przeciw rzeczywistym rywalom.
- Wyniki lokalne (720 tur; średnia z 10 seedów):
  - vs `pass`: **~29.7k**, vs deterministyczny `random`: **~29.9k**,
    vs wbudowany `starter`: **~29.1k**, self-play: **~26.8k**
    (baseline v0 miało ~3.9k; po 10 seedów na wariant).

## Jak działa strategia (v2)

1. **Ręce do pracy.** Każdego dnia o godzinie 0 zatrudniamy farmerów pomocniczych
   (koszt fibonacciego 1,1,2,3,5,… resetuje się co dzień). Każda ręka dostaje
   „chunk" (spójny wycinek planu pól) i robi codzienny obchód: **podlewanie
   ma pierwszeństwo** (roślina niepodlana 2 dni → chwast, a świeżo posadzona
   musi być podlana tego samego dnia), przy okazji zbiera dojrzałe i od razu
   dosadza. Farmer to „overflow": zbiera/sadzi po całym planszu.
2. **Pszenica = stabilny fundament.** Jej krzywa ceny po stronie nadpodaży
   jest logarytmiczna, więc dwuosobowy rynek nie jest w stanie zepchnąć jej
   do ceny minimalnej (w przeciwieństwie do marchwi/melona/owoców/mleka).
   Zbiór w **wieku 3 dni** (3 sztuki zamiast 4 w wieku 4) — strata ~7%
   wydajności, ale zysk z harmonogramu: roślina czeka bez gnicia do wieku 5,
   więc spóźnione żniwa nie kosztują.
3. **Marchew = premia za deficyt.** Ma identyczny rytm jak pszenica (3 szt./4
   dni) przy bazowej cenie 35 vs 25, ale jej rynek da się przesycić. Dlatego
   areał marchwi dobieramy do **widocznego popytu miasteczka** (shopy są
   wspólne i jawne: PET_CAFE i FARMERS_MARKET kupują marchew) z mnożnikiem
   `CARROT_KAPPA=0.7` i limitem 40% planszu; sadzimy tylko gdy cena marchwi
   ≥ 1.15 × ceny pszenicy (samonaprawiający się zawór przy zalewie rynku).
4. **Melon = najwyższa marża.** Ratusz zawsze kupuje 1 melon dziennie (30 w
   sezonie), a 10-dniowa roślina daje 6 sztuk. Przy cenie rynkowej w okolicy
   bazy (250) 4 komórki melona (fragment NW) zarabiają więcej niż reszta pola
   — ale już 6 komórek przesyca rynek (krzywa sq) i psuje wynik, więc liczba
   jest stała (`MELON_CELLS`, sadzenie tylko do dnia 19).
5. **Ziemia: tylko NE ($1k) i SW ($2k).** SE ($4k) jest offline potwierdzona
   jako nieopłacalna — późno w sezonie nie zdąży się zwrócić (self-play z SE:
   ~21.8k vs ~26.8k bez SE).
6. **Sprzedaż.** Szopa (limit 100) jest opróżniana co turę przez SELL; koniec
   dnia sam zrzuca inventory do szopy, więc DROP/PICKUP są zbędne.

## Użycie

```bash
make setup       # venv + kaggle-environments (raz)
make test        # testy offline (kontrakt akcji, determinizm, przewaga nad idle)
make match       # lokalny mecz vs OPPONENT=pass|random|starter|self
make benchmark   # szybki przegląd vs pass, deterministyczny random i starter
```

Strojenie: `bench_tune.py` monkeypatchuje stałe modułu `agent.py` i mierzy
średnią z wielu seedów (self/pass/random) — to narzędzie deweloperskie,
nie wchodzi do paczki submissji.

## Architektura

- Sandbox (Arena) **nie ma** łączności z Kaggle; runner GitHub Actions ją ma.
  Dlatego: kod i testy rozwijamy offline, a walidację/submisję odpalamy na GH
  Actions (workflow `kaggriculture.yml`) z sekretami Kaggle.
- Sekrety **nigdy** nie są w repo. Lokalnie aktualny token zapisz jako
  `~/.kaggle/access_token` (tryb `600`) albo ustaw `KAGGLE_API_TOKEN`.
  Na GitHub preferowany jest secret `KAGGLE_API_TOKEN`; workflow zachowuje
  też kompatybilność ze starym duetem `KAGGLE_USERNAME` / `KAGGLE_KEY`.

## Submisja Kaggle

Silnik symulacyjny Kaggle ładuje `main.py` z funkcją `act(obs, config)`.

```bash
make pack         # buduje submission.tar.gz (main.py — kopia agent.py)
```

Właściwy upload robi workflow (ręczny dispatch z `submit=true` albo commit z
`[kaggr-submit]`), o ile w repo ustawiono sekrety Kaggle. Pierwsza submissja
przechodzi **Validation Episode** (agent gra sam ze sobą); logi błędów
pobierzesz przez `kaggle competitions logs <episode> 0`.

## Kierunki dalszej poprawy (kolejność)

1. Więcej upraw premiowych reaktywnie (truskawki/tomaty/zwierzęta) z
   doborem areału do popytu shopów — mechanizm jak przy marchwi, ale
   ongoing-crops mają inny rytm zbioru.
2. Fine-tuning liczby rąk / progów wykupu ziemi pod nowy miks upraw.
3. Ewentualny „endgame": przestać sadzić pod koniec sezonu (nasiona bez
   zwrotu) i zoptymalizować podział pracy między chunki.
