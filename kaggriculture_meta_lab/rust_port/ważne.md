# Ważne: porównanie portu Rusta

Data porównania: 2026-09-08.

Ten katalog zawiera port używany przez `kaggriculture_meta_lab`. Został
porównany z aktualizowanym portem z gałęzi
`arena/01a07c52-riemann` (stan `307c916`). Nie kopiujemy całej tamtej gałęzi,
ponieważ ten port jest już połączony z naszym backendem sweepa, fallbackiem
Python i generatorem taśm.

## Co przejęliśmy z nowszego portu

Do bieżącej wersji włączono następujące poprawki:

- cache załadowanych taśm w trybie batch (`TapeCache`), dzięki czemu powtarzane
  ścieżki nie są ponownie kanonizowane i odczytywane z dysku;
- niezależne reguły przycinania rąk dla taśmy A i B:
  `--trim-hands-a` oraz `--trim-hands-b`;
- poprawne przenoszenie tych reguł razem z wejściowymi taśmami przy
  `--reverse-seats`;
- API `Replay::new_with_hand_trimming`, zachowujące wsteczną kompatybilność
  starego konstruktora;
- testy mixed replay, klienta Python, CLI, konfiguracji oraz hand trimming.

To jest ważne dla naszego użycia: kandydat strukturalny bywa generowany jako
wrapper/tape, a przeciwnik może być surową taśmą historyczną. Nie wolno
stosować reguły hand trimming automatycznie do obu wejść.

## Zalety względem pierwotnej wersji tego portu

Pierwotna wersja, którą wcześniej podłączyliśmy do backendu, miała wspólną
flagę `trim_hands` dla obu agentów i nie miała cache ścieżek w batchu. Obecna
wersja jest więc lepsza w trzech praktycznych obszarach:

1. **Poprawność** — replay kandydata przeciwko surowemu przeciwnikowi może
   używać różnych zasad przygotowania rąk.
2. **Odporność przy odwróceniu seatów** — wynik nadal jest zwracany w kolejności
   kandydat, przeciwnik, a reguły podążają za taśmami, nie za fizycznym seatem.
3. **Wydajność sweepa** — taśmy używane przez wiele jobów są ładowane tylko
   raz w procesie batchowym. To szczególnie pomaga przy screen/promote/finals,
   gdzie te same warianty powtarzają się na wielu seedach.

Zachowaliśmy dodatkowo nasze własne elementy, których tamta gałąź nie
zastępuje: `rust_backend.py`, automatyczny fallback Rust/Python, integrację
`--backend` w `scripts/sweep.py`, generator `structural_gen.py`, kontrakt
`for_python_port` i pakiet handoff dla ChatGPT/Fable.

## Co oznaczają benchmarki

W zaktualizowanym raporcie tamtej gałęzi zmierzono na runnerze z 4 logicznymi
CPU dla 14 000 gier:

| Rayon | Czas | Gry/s |
|---:|---:|---:|
| 1 wątek | 9,022 s | 1552 |
| 4 wątki | 3,580 s | 3911 |
| 16 wątków | 3,518 s | 3980 |

Dla 64 gier raport podaje mediany:

| Wariant | Czas | Przyspieszenie względem Pythona |
|---|---:|---:|
| Python | 5,73432 s | 1x |
| Rust, osobny proces na mecz | 0,59006 s | 9,72x |
| Rust, batch, 1 wątek | 0,05093 s | 112,55x |
| Rust, batch, 4 wątki | 0,02587 s | 221,69x |

Wcześniejszy pomiar tego portu wynosił 80,87x dla batcha 1-wątkowego i
136,31x dla batcha 4-wątkowego. Liczb 221,69x i 80,87x nie należy jednak
porównywać jako czystego przyspieszenia kodu: użyto innych runnerów i innych
czasów bazowego interpretera Python. Uczciwy wniosek z samego czasu batcha to
niewielka poprawa, natomiast cache daje większą korzyść w rzeczywistym
workloadzie z powtarzanymi taśmami.

Żaden z tych benchmarków nie jest pełnym pomiarem całego lejka. Pełny sweep
obejmuje także budowę jobów, eksport taśm, JSONL, rating i ewentualne agentów
reaktywnych. Dlatego wynik produkcyjny należy mierzyć osobno na docelowym
Ryzen 9 5950X.

## Walidacja i ograniczenia

Port pozostaje portem wyłącznie symulatora. Nie wykonuje sam polityk
reaktywnych i nie wysyła submission do Kaggle. Przed użyciem w sweepie należy
uruchomić testy oraz sprawdzić, że Rust i Python zwracają identyczne nagrody
binary64 dla kontrolnego zestawu seedów.

Pełny launcher Windows naszego eksperymentu to:

```bat
set BUILD=1
run_structural_sweep.bat
```

Po pierwszym buildzie można uruchamiać sweep bez `BUILD=1`. Jeśli binarka nie
istnieje, `backend=auto` bezpiecznie wraca do silnika Python.
