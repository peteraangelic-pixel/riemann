# Weryfikacja portu Rust

## 2026-09-08 — po przeglądzie alternatywnego ZIP-a (najnowszy stan)

Zielone [CI #34211248146](https://github.com/peteraangelic-pixel/riemann/actions/runs/34211248146),
commit kodu `b34ed45a9dff030155bead96c84eed434b51a347`.
Dodano jawne `export_tape.py --single-stream`, ochronę źródła przed nadpisaniem,
mapę funkcji oryginału oraz kolejne testy graniczne. **Natywny kod silnika i
ustawienia kompilacji nie zostały zmienione**; SHA-256 binarza nadal wynosi
`be94f33974132f3825f74c8475d2112c40dd29588259ed49299d5974fd20aa84`.

- Rust debug/release: **17/17 w każdym trybie**; Python/CLI: **37/37**.
- Python parity: **585 meczów / 87 seedów / 22 597 pełnych stanów**, bez różnic.
- Rzeczywisty framework: **16/16**, bez różnic.
- Batch 14 000: **9,054 s / 3,712 s / 3,580 s** dla 1 / 4 / 16 wątków,
  mediana 3 prób na runnerze z 4 logicznymi CPU (AMD EPYC 9V74).
- Skrót uporządkowanych wyników batcha pozostał taki sam:
  `15d95560c01fb498aff3ae6cb07a9604604aa8733daa6df9440df4128965f304`.
- Mały pomiar 64 gier: Python **5,258616 s**, Rust proces/mecz **0,668028 s**,
  Rust batch 1 wątek **0,053312 s**, batch 4 wątki **0,028515 s**.
  Przyspieszenia względem szeregowego Pythona: **7,87× / 98,64× / 184,41×**.

Zmiana 221,69× → 184,41× między przebiegami nie jest dowodem regresji silnika:
zmienił się runner i warunki pomiaru, a binarz pozostał identyczny.
To nadal pomiar taśm, nie całego LAB-u ani Pythona w 16 procesach.

[Porównanie obu portów, błędy ZIP-a i pełna metodologia](../port_review/REVIEW.md).
Archiwum użytkownika pozostawiono bez zmian; kopia kompilacyjna drugiego portu
nie jest używana jako produkcyjny symulator.

## 2026-09-08 — zakończenie poprawki portu (wcześniejszy pomiar)

**Wszystkie bramki zielone:** [GitHub Actions #34206326321](https://github.com/peteraangelic-pixel/riemann/actions/runs/34206326321).
Sprawdzony commit kodu: `20f7a9d5e99c846ec7d59f37253995d947895b25`. Późniejszy commit
uzupełnia tylko ten raport, bez zmian kodu.

### Co domknięto

- Naprawiono interpretację płaskich nadpisań `marketParams`: nieznany produkt
  `default` nie usuwa prawdziwych nadpisań. Sprawdzone również na rzeczywistym
  frameworku, nie jedynie we wspólnym adapterze Python/Rust.
- Całkowite liczby JSON zapisane jako np. `24.0` działają zgodnie z typem
  `integer` JSON Schema; liczby ułamkowe i poza zakresem nie są obcinane.
- Dodano `--trim-hands-a` / `--trim-hands-b`, niezależnie od siebie. Opcje
  podążają za wejściowym agentem A/B również przy odwracaniu miejsc.
  `--trim-hands` i stare konstruktory biblioteki nadal zachowują stare działanie.
- Klient Python sprawdza schemat odpowiedzi, kompletność i skończoność wyników,
  sygnały/błędne kody wyjścia oraz opcjonalny `timeout`. `allow_errors=True`
  pozwala odebrać jawne błędy gier, nie ukrywa uszkodzonego protokołu.
- Klient rozwiązuje każdą ścieżkę taśmy raz na batch; binarz pomija ponowne
  odpytywanie systemu plików dla kanonicznej ścieżki obecnej już w cache.

### Testy

| Kontrola | Wynik |
|---|---:|
| rustfmt + Clippy `-D warnings` | OK |
| Rust debug | **17/17** |
| Rust release | **17/17** |
| Python: eksport, klient, CLI i konfiguracja | **32/32**, bez pominięć w CI |
| Mecze porównane bitowo z Pythonem | **585**, 87 różnych seedów |
| Pełne stany porównane bez tolerancji | **22,597**, zero różnic |
| Niezależny rzeczywisty framework Kaggle | **16/16** |
| Batch: 14 000 wyników × 3 liczby wątków × 3 powtórzenia | **wszystkie zgodne** |
| Dodatkowa próbka z całej paczki 14k sprawdzona w Pythonie | **64/64** |

Test alokatora obejmuje wszystkie cztery kombinacje przycinania rąk i obie
orientacje, po 720 tur: **0 alokacji/reallokacji w gorącej ścieżce**, zarówno
w debug, jak i release. Start gry, parsing, start Rayona i trace są poza tą
ścieżką. Nadal przechodzą odciski 120 000 słów MT19937 i 270 009 cen.

Mieszane reguły zweryfikowano na przypadkach, w których wpływają na prawdziwą
gotówkę: agent przycinany kończy z 3017, a surowy przeciwnik z 2990. Po
odwróceniu miejsc wynik pozostaje w kolejności A/B, nie fizycznych miejsc.

### Zmierzony duży batch

Workload: dostarczona taśma B21 przeciw sobie, seedy 0–13 999, naprzemiennie
odwracane miejsca, `episodeSteps=720` = 719 akcji. Mediana trzech prób.
Czas obejmuje wywołanie klienta Python, zapis CSV, uruchomienie binarza,
parsowanie taśm, symulację oraz odczyt i walidację wszystkich odpowiedzi.

| Wątki Rayon | Czas 14 000 meczów | Mecze/s | Przyspieszenie vs Rust 1 wątek |
|---|---:|---:|---:|
| 1 | 9.022 s | 1552 | 1.00× |
| 4 | 3.580 s | 3911 | 2.52× |
| 16 | 3.518 s | 3980 | 2.56× |

Runner miał **4 logiczne CPU** (AMD EPYC 7763 64-Core Processor).
16 wątków na tej maszynie nie oznacza pomiaru 16 fizycznych rdzeni.
Wszystkie próby miały ten sam SHA-256 uporządkowanych bajtów binary64 wyników:
`15d95560c01fb498aff3ae6cb07a9604604aa8733daa6df9440df4128965f304`.

To **126 000 wykonanych gier Rust** w powtórzeniach benchmarku, ale nie 126 000
niezależnych sprawdzeń z Pythonem: Python sprawdził 64 rozłożone po całej paczce
zadania, a pełne paczki porównywano między liczbami wątków i powtórzeniami.
Nie wykonano ani nie ekstrapolowano 14 000 gier Python na potrzeby tej tabeli.

### Mały benchmark porównawczy

Ta sama maszyna, 64 mecze, trzy powtórzenia, mediana:

| Wariant | Czas 64 meczów |
|---|---:|
| Python — bezpośredni interpreter | 5.73432 s |
| Rust — proces na mecz | 0.59006 s |
| Rust — batch / 1 wątek | 0.05093 s |
| Rust — batch / 4 wątki | 0.02587 s |

W tym pomiarze to 9.72× dla osobnych procesów i
221.69× dla batcha / 4 wątków względem bezpośredniego interpretera.
Nie porównujemy tych liczb przyczynowo z poprzednim runnerem o innym CPU.
**Żaden z benchmarków nie jest pomiarem całego sweepa, generowania polityk,
pracy agenta reaktywnego ani statystyk turniejowych.**

### Użycie i artefakt

```bash
make test
make check SEEDS=64 THREADS=4
make benchmark-batch BATCH_GAMES=14000 BATCH_THREADS=1,4,16
# Kandydat A przycinany, zapisane akcje przeciwnika B pozostają surowe:
./target/release/kg_sim --jobs work/jobs.csv --steps 720 --threads 16 --trim-hands-a
```

Biblioteka: `Replay::new_with_hand_trimming(..., reverse, [trim_a, trim_b])`;
klient Python: `replay_many(jobs, trim_hands_a=True, threads=16, timeout=300)`.
Nie podmieniano agenta, nie wysyłano submisji do Kaggle i nie zmieniano
`arena/01a0712c-riemann`. Port dostarcza poprawny kontrakt dla mixed replay,
nie wykonuje sam polityk reaktywnych ani automatycznie nie podłącza się do LAB-u.

Binarz Linux x86_64 i cztery raporty JSON są w artefakcie powyższego CI:
`kg-sim-20f7a9d5e99c846ec7d59f37253995d947895b25` (retencja 7 dni).
SHA-256 binarza: `be94f33974132f3825f74c8475d2112c40dd29588259ed49299d5974fd20aa84`.
Rust kompilowano i uruchamiano **w GitHub Actions**; sandbox nie ma lokalnego
toolchaina. Lokalne testy modułów Python były uzupełnieniem, nie są przedstawiane
jako lokalny pomiar binarza.

---

## Archiwum: pierwsza weryfikacja — 2026-09-07

### Status: wszystkie bramki przeszły

Zielony przebieg: [GitHub Actions #34139300389](https://github.com/peteraangelic-pixel/riemann/actions/runs/34139300389).
Sprawdzony commit kodu: `0e26017cf79c16b085195355b501bc19fe440122`.
Późniejszy commit dodaje wyłącznie ten raport, bez zmian kodu.

| Kontrola | Wynik |
|---|---|
| `cargo fmt` / brak zmian po formatowaniu | OK |
| `cargo clippy --all-targets --locked -- -D warnings` | OK |
| Rust: 8 testów jednostkowych + 2 konformancji + 1 alokacji | **11/11** |
| Python: eksporter, CLI, CSV, klient, błędy | **12/12**, bez pominięć |
| `cargo build --release --locked` | OK |
| Porównanie Rust–Python: gotówka jako bajty IEEE-754 binary64 | **574 mecze, zero różnic** |
| Porównanie pełnego stanu po każdej turze wybranych meczów | **14 674 stany, zero różnic** |
| Rzeczywisty framework `Environment.run` + dostarczony agent | **9/9 przypadków**, Rust i adapter zgodne |

#### Zakres testów różnicowych

- Batch: **68 seedów** — 0–63, −1, 2³², −2⁶³, 2⁶³−1.
- **84 różne seedy łącznie**, po uwzględnieniu scenariuszy dodatkowych.
- 544 mecze batch: self-play, przeciwnik pasywny, zamiana miejsc, asymetryczne
  taśmy; każdy wariant z dosłownymi oraz przyciętymi listami pomocników.
- Dodatkowe 30 scenariuszy: krótkie/długie horyzonty, dokładnie 720 tur akcji,
  różne długości dnia i interwały sklepów, mała szopa, darmowi pomocnicy,
  chwasty z prawdopodobieństwem 0 i 1, rzadkie nadpisania krzywych,
  12 deterministycznie wygenerowanych taśm losowych.
- Wyniki batch są identyczne **bajtowo i w kolejności wejściowej** między
  1 a 4 wątkami. Oddzielny test CLI sprawdza również 16 wątków i
  `RAYON_NUM_THREADS`, w tym cytowanie przecinków/spacji w nazwach plików.
- Odciski konformancji: **120 000 słów MT19937**, mieszane wywołania
  `random()/choice()` i **270 009 cen** z referencyjnego Pythona.
- Licznik alokatora: **0 alokacji/reallokacji w 720 turach**, także przy
  darmowym HIRE, zmianie dnia, przepełnieniu szopy i reużyciu pamięci rąk.
  Parsowanie, rezerwowanie stanu, start Rayona i opcjonalny trace są poza
  gorącą ścieżką.

To testy dokładnej równości, nie tolerancja „± dolar” ani porównanie średnich.
Nie stanowią dowodu formalnego dla wszystkich możliwych wejść; zakres
obsługiwanych konfiguracji i patologicznych akcji opisuje README.

### Porównanie źródeł przed i po porcie

Użyto plików z gałęzi `arena/01a06bce-riemann`, commit
`a310ca103efcbb95376b03f32bb901c9d8b05791`. Ponowne pobranie przypiętego wheel
w końcowym CI potwierdziło:

- `kaggriculture_sim.py` jest **identyczny bajtowo** z oficjalnym symulatorem 1.32.7.
- `kaggriculture_config.json` jest **identyczny bajtowo** z oficjalną specyfikacją.
- Nie scalano dwóch wariantów zasad i nie zmieniano Pythonowej referencji
  w celu dopasowania testów do Rusta.

Hashe źródeł: [`reference/provenance.json`](reference/provenance.json).
SHA-256 wheel:
`2a1bb862ad2d6463080f80f6a766f46d94b53fd57168cfeddb9857fc3dbc4c8f`.

Rzeczywisty framework potwierdził też pułapkę numeracji:
`episodeSteps=720` → 720 zapisanych stanów → **719 akcji**.
`episodeSteps=721` → **720 akcji**. Dla `episodeSteps=1` framework nadal
wykonuje jedną akcję. Port ma osobny `--step-mode turns` do dosłownej liczby tur.

Przykład self-play, seed 0, dostarczony wrapper agenta:
`{"rewards":[60225.0,60976.0],"errors":[]}`.

### Zmierzona wydajność

Końcowy zielony CI: Linux x86_64, glibc 2.35, Rust 1.85.1, Python 3.12.14.
Runner otrzymał **4 logiczne CPU** na hoście AMD EPYC 9V74; nie jest to test
80 rdzeni mimo nazwy procesora, ani test 16 fizycznych rdzeni.

64 pełne mecze na próbkę, 3 powtórzenia, mediana; `--steps 720`, raw hands.
We wszystkich wariantach sprawdzono również zgodność gotówki.

| Wariant | Czas na 64 mecze | Przyspieszenie vs Python |
|---|---:|---:|
| Bezpośredni interpreter Python | 3,9023 s | 1× |
| Rust, osobny proces na mecz | 0,4966 s | **7,86×** |
| Rust, jeden batch / 1 wątek | 0,04825 s | **80,87×** |
| Rust, jeden batch / Rayon 4 wątki | 0,02863 s | **136,31×** |

Czas Rusta obejmuje uruchamianie procesów, zapis/odczyt CSV i taśm JSON oraz
odczyt wyników. Pythonowy punkt odniesienia jest konserwatywny: bez kosztów
całego frameworka Kaggle, kopiowania obserwacji i `deepcopy` polityki.
**Używaj batcha** — osobne procesy tracą czas na wielokrotne parsowanie tych
samych danych. Dla tej małej paczki skalowanie 4 wątków względem 1 wyniosło
1,69×, bo część czasu jest stałym kosztem uruchomienia i I/O.

W poprzednim pomiarze tej samej binarki na innym runnerze było 9,78× / 160,68×
(oddzielne procesy / batch 4). Nie wybieramy lepszego wyniku jako gwarancji:
tabela powyżej pochodzi z końcowego zielonego przebiegu.

**Nie zmierzono całego Twojego trzygodzinnego sweepa.** Generowanie taśm,
zmiany polityk, statystyki i Pythonowe sterowanie pozostają poza tym pomiarem.
Nie obiecujemy więc konkretnego czasu 14k-game pipeline bez uruchomienia go
na jego rzeczywistych danych i docelowym sprzęcie.

### Artefakt i odtwarzalność

Binarz Linux x86_64 i raporty JSON są w artefakcie końcowego CI:
`kg-sim-0e26017cf79c16b085195355b501bc19fe440122` (retencja 7 dni).
SHA-256 binarza:
`a00be6ebe42b5c35a35554e3f97f525909fa49cf3975c0715756b2a91670389e`.

Rust był kompilowany i uruchamiany **w GitHub Actions**, nie w lokalnym
sandboxie Arena: ten sandbox nie ma toolchaina i nie pozwalał pobrać go ani
artefaktów z serwerów dystrybucyjnych. Lokalnie sprawdzono dodatkowo adapter
Python względem rzeczywistego core Kaggle. Raporty z końcowego CI odczytano
przez GitHub Checks API; brak lokalnego binarza nie jest przedstawiany jako
lokalnie wykonany benchmark.

Do ponowienia offline (po standardowej instalacji Rust i pobraniu zależności):

```bash
make test
make check SEEDS=64 THREADS=4
make benchmark GAMES=64 THREADS=4
```

Opcjonalna kontrola rzeczywistego frameworka:

```bash
python -m pip install -r requirements-framework.txt
make framework-check
```

Duże taśmy, wheel, trace i binaria pozostają poza Gitem w `work/` / `target/`.
Zamrożone małe odciski testowe można odtworzyć przez `tools/generate_vectors.py`.
