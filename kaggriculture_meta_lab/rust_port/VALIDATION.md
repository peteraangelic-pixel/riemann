# Weryfikacja portu — 2026-09-07

## Status: wszystkie bramki przeszły

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

### Zakres testów różnicowych

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

## Porównanie źródeł przed i po porcie

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

## Zmierzona wydajność

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

## Artefakt i odtwarzalność

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
