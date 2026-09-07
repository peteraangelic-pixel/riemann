# Kaggriculture — Rust + Rayon

Port **wyłącznie symulatora** `kaggle-environments==1.32.7`. Sweep, dobór agentów,
statystyki i Wilson zostają w Pythonie. Rust dostaje już rozpakowane taśmy JSON;
nie wykonuje Pythona ani polityk reaktywnych.

## Co zostało porównane

Pliki z `arena/01a06bce-riemann`, commit
`a310ca103efcbb95376b03f32bb901c9d8b05791`, są zachowane w `reference/`.
**Symulator i konfiguracja są identyczne bajtowo z oficjalnym wheel 1.32.7.**
Nie ma dodatkowej mechaniki do łączenia ani „lepszej” wersji jednej z tych reguł.
SHA-256 i pochodzenie: [`reference/provenance.json`](reference/provenance.json).
Pełny pierwotny kontrakt: [`reference/HANDOFF_FOR_FABLE.md`](reference/HANDOFF_FOR_FABLE.md).

## Szybki start

Wymagania: Rust **1.85+**, Python **3.10+** do eksportu/testów. Sam binarz nie
wymaga Pythona, NumPy ani `kaggle-environments`.

```bash
cd kaggriculture_meta_lab/rust_port
cargo build --release --locked

# Działa także ze źródłem przemianowanym na .txt. Bez wykonywania kodu agenta.
python tools/export_tape.py -o work/example.json

./target/release/kg_sim \
  --tape-a work/example.json --tape-b work/example.json \
  --seed 0 --steps 720 --trim-hands
```

Wynik: jedna linia na stdout, wyłącznie JSON:

```json
{"rewards":[60225.0,60976.0],"errors":[]}
```

### Dwa ważne szczegóły zgodności

1. **`--steps` domyślnie oznacza Kaggle `episodeSteps`.** Stan początkowy jest
   już pierwszym rekordem. Dlatego `--steps 720` wykonuje **719 tur akcji**
   (indeksy 0–718), dokładnie jak oryginalny interpreter i framework Kaggle.
   Aby wykonać dosłownie 720 akcji wraz z ostatnim odświeżeniem dnia:

   ```bash
   ./target/release/kg_sim --tape-a work/example.json --tape-b work/example.json \
     --seed 0 --steps 720 --step-mode turns --trim-hands
   ```

   `--step-mode turns --steps 0` zwraca stan początkowy. W trybie Kaggle minimum
   to 1, a `episodeSteps=1` również wykonuje jedną turę, zgodnie z frameworkiem.

2. **Domyślne taśmy to dosłowne akcje interpretera.** `--trim-hands` dodatkowo
   odtwarza przycinanie `hands[:len(live_hands)]` z dostarczonego agenta,
   **przed** atomową walidacją PLANT. Bez tej flagi nawet polecenia PLANT dla
   nieistniejących pomocników liczą się do zapotrzebowania na nasiona — tak
   działa oryginalny interpreter. Eksporter uwzględnia również nadpisanie
   początkowych zleceń `BUY_WHEAT=21` / `SELL_WHEAT=16`; samych danych z bloba
   nie należy traktować jako całego wrappera agenta.

Nie poprawiamy ukradkiem tych zachowań. Do porównania z własną pętlą Pythonową
należy wybrać ten sam horyzont i tę samą regułę przycinania.

## Taśmy i zamiana miejsc

Format pliku (rozszerzenie dowolne, zawartość JSON):

```json
[
  [{"farmer":["PASS"],"hands":[],"market":[["BUY_SEED","WHEAT",2]]}],
  [{"farmer":["PASS"],"hands":[],"market":[]}]
]
```

- Dokładnie dwie niepuste listy: `[seat][step]`. Po końcu listy powtarzana jest
  ostatnia akcja, analogicznie do `min(step,719)` z przykładu. Aby po krótkiej
  taśmie nic nie robić, dopisz na końcu `{}`.
- Bez `--reverse-seats`: seat 0 = A[0], seat 1 = B[1].
- Z `--reverse-seats`: seat 0 = B[0], seat 1 = A[1].
- **`rewards` zawsze jest w kolejności wejściowej A, B**, nie fizycznych miejsc.
- Nieznane/nielegalne operacje są no-opami; wadliwe sloty zleceń nie są usuwane,
  żeby nie zmieniać ich parowania na wspólnym rynku.

## Wiele meczów — tu używamy Rayona

`work/jobs.csv`, bez nagłówka (nagłówek `seed,tape_a,tape_b,reverse` też działa):

```csv
0,example.json,example.json,0
1,example.json,example.json,1
2,example.json,example.json,false
```

Ścieżki taśm są względne **do katalogu CSV**, nie do bieżącego katalogu procesu.
CSV obsługuje cudzysłowy, spacje i przecinki w nazwach plików.

```bash
./target/release/kg_sim --jobs work/jobs.csv --steps 720 --threads 16 --trim-hands
# albo RAYON_NUM_THREADS=16 zamiast --threads
```

Każda linia wyniku odpowiada linii zadania, **w kolejności wejściowej**, niezależnie
od kolejności zakończenia wątków. Każda unikalna taśma jest parsowana i przygotowana
raz, następnie współdzielona niemutowalnie przez `Arc`. Każdy mecz ma własny RNG,
dwie farmy i **jeden wspólny rynek**. Nie ma blokady globalnego rynku ani RNG.

Wadliwy rekord daje `{"rewards":null,"errors":["..."]}` na swojej pozycji;
poprawne mecze nadal są liczone. Proces kończy się kodem 1, jeśli wystąpił błąd
lub zadziałał oryginalny limit pętli rynku. Nie licz takiego rekordu jako remisu!
Błędy użycia opcji CLI zgłasza Clap na stderr, z niezerowym kodem wyjścia.

### Cienki klient Python

```python
from pathlib import Path
from tools.rust_client import Job, replay_many

p = Path("work/example.json")
jobs = [Job(seed, p, p, reverse=bool(seed % 2)) for seed in range(1000)]
results = replay_many(jobs, threads=16, steps=720, trim_hands=True)
for job, result in zip(jobs, results):
    cash_a, cash_b = result["rewards"]
    # Tutaj dotychczasowy sweep / statystyki / Wilson, bez zmian.
```

Klient nie używa shella, zapisuje prawidłowy CSV, sprawdza liczbę odpowiedzi i
**domyślnie odrzuca błędy**, żeby nie zatruć statystyk. `allow_errors=True` pozwala
obsłużyć je samodzielnie. Do sweepów używaj jednego `--jobs`, nie subprocessu na
każdy seed: start procesu i ponowne parsowanie JSON mogą dominować czas symulacji.

## Konfiguracja

`--config` przyjmuje pełny dostarczony `kaggriculture_config.json` albo płaskie
nadpisania, np.:

```json
{
  "startingMoney": 3000,
  "shedCapacity": 100,
  "weedSpawnChance": 0.005,
  "marketParams": {"WHEAT": {"above_target": 0.25}}
}
```

Obsługiwane: kasa, koszty pomocników, pojemność szopy, długość dnia, limit zleceń,
wszystkie interwały miasta, chwasty i rzadkie nadpisania krzywych cen
(`linear`, `sq`, `sqrt`, `log`, `log10`, `hinge`). Nieznana nazwa funkcji ceny ma
liniowy fallback jak w Pythonie. Nasiona nie zajmują szopy.

Świadome ograniczenia v1:

- **Wyłącznie plansza 10×10**; inny rozmiar jest odrzucany, nie symulowany błędnie.
- Seed CLI/CSV: signed 64-bit. Dzienne mieszanie `(seed*1000003)^day` jest w
  `i128`, bez przepełnienia 32/64-bitowego. To obsługuje także ujemne seedy.
- Horyzont/interwały do `i32::MAX`; pieniądze i ceny używają `f64`, jak Pythonowe
  pieniądze. Testowana jest konfiguracja konkursowa i opisane testy nadpisań,
  nie dowolne ekstremalne liczby powodujące przepełnienia.
- Kontrakt obejmuje poprawnie kodowane akcje. Nie odwzorowujemy wyjątków
  Pythona dla patologicznych obiektów/niekonwertowalnych ilości w akcjach
  jednostek; takie operacje są no-opami. Błędy JSON i konfiguracji są jawne.
- Brak rendererów, agentów reaktywnych, timeoutów agentów, logiki submissji,
  protokołu całego środowiska Kaggle ani warstwy turniejowej.

## Dlaczego szybko i dlaczego zgodnie

- Plansze `[Tile; 100]`, produkty/nasiona w tablicach, enumy zamiast stringów.
- Małe ekwipunki zachowują **kolejność wstawiania słownika Pythona**, łącznie
  z usunięciem i ponownym dodaniem klucza. To istotne przy przepełnieniu szopy.
- Pamięć pomocników jest rezerwowana **przed grą** z liczby możliwych HIRE w
  taśmie. Działa również darmowe zatrudnianie; nie ma arbitralnego limitu 12 rąk.
- Gorąca ścieżka nie alokuje, także przy zatrudnianiu, DROP i zmianie dnia.
  Test z licznikowym alokatorem sprawdza to bez polegania na deklaracji autora.
- MT19937 odtwarza integer seed CPythona, 53-bitowe `random()` i odrzucanie
  losowań w `choice`. Chwasty obu farm i losowanie sklepu używają tego samego
  dziennego strumienia; pobieramy losowania tylko na pustych polach.
- Cena za jednostkę jest zaokrąglana **ties-to-even**. `log(1+x)` nie zostało
  zastąpione przez `log1p`, nie używamy FMA/fast-math.
- Zlecenia są przetwarzane jednostka po jednostce: wycena obu graczy, dopiero
  potem oba commity. BUY_PRODUCT wycenia zapas po kupnie. Sprzedaż za $1 nie
  zwiększa podaży. Popyt miasta działa także w turze 0.
- Ceny widoczne w obserwacji wyliczamy dopiero dla opcjonalnego trace. Taśmy
  ich nie czytają, więc odświeżanie dziewięciu nieużywanych cen po każdym
  slocie zleceń jest zbędne. Ceny transakcji nadal liczymy dokładnie.

## Weryfikacja i diagnostyka

```bash
cargo fmt --all -- --check
cargo clippy --all-targets --locked -- -D warnings
cargo test --locked
cargo build --release --locked
python -m unittest discover -s tests -v
python tools/check.py --check --seeds 64 --threads 4
python tools/benchmark.py --games 64 --threads 4 --repeats 3
```

`check.py` sprawdza SHA źródeł, gotówkę **bitowo jako binary64**, pełne stany tur,
ujemne/duże seedy, obie orientacje, nadpisania konfiguracji i losowe taśmy. Wyniki
Rayona dla 1 i wielu wątków muszą być identyczne również jako bajty JSONL.
Rustowe wektory kontrolne obejmują 120 000 wyjść MT19937, mieszane wywołania
`random/choice` oraz **270 009 wycen** z oryginalnego Pythona.

Opcjonalna niezależna kontrola używa **rzeczywistego `Environment.run` Kaggle**
i funkcji `agent` z przykładu, nie tylko lekkiego adaptera. Pobiera przypięty
wheel (~60 MB), sprawdza SHA-256 i nie instaluje zależności innych gier:

```bash
# W osobnym venv, jeżeli potrzebujesz tej dodatkowej kontroli:
python -m pip install -r requirements-framework.txt
python tools/check_framework.py --download
# Offline, jeżeli wheel już jest na dysku:
python tools/check_framework.py --wheel /sciezka/kaggle_environments-1.32.7-py3-none-any.whl
```

Wyniki wykonanej weryfikacji i pomiarów: [`VALIDATION.md`](VALIDATION.md).

Szczegółowy trace nie jest częścią szybkiej ścieżki:

```bash
./target/release/kg_sim --tape-a work/example.json --tape-b work/example.json \
  --seed 17 --steps 720 --trace work/rust-trace.jsonl --trim-hands
python tools/py_reference.py --tape-a work/example.json --tape-b work/example.json \
  --seed 17 --steps 720 --trace work/python-trace.jsonl --trim-hands
```

Trace zawiera stan początkowy i każdy stan po turze, w **fizycznej kolejności
miejsc**. Przy błędzie checker zgłasza pierwszy różniący się klucz/pole, a nie
jedynie „wynik się nie zgadza”. Biblioteka Rust udostępnia także `Replay::advance`
i `Game::snapshot` do własnych testów.

Raporty powstają w ignorowanym `work/`; binaria w `target/`. Workflow
`Kaggriculture Rust simulator` kompiluje i wykonuje testy w GitHub Actions.
Testowane wartości przyspieszenia należy brać z raportu benchmarku, nie z
założenia 8–20×. Benchmark obejmuje start binarza i I/O, ale **nie jest pomiarem
całego Twojego 14k-game sweepa ani maszyny z 16 fizycznymi rdzeniami**.

## Układ plików

- `src/engine.rs` — mechanika farm, jednostek, rynku i dnia.
- `src/rng.rs`, `src/market.rs`, `src/data.rs` — zgodne RNG, krzywe i tabele.
- `src/tape.rs`, `src/config.rs` — parsowanie poza gorącą ścieżką.
- `src/main.rs` — CLI, CSV, cache taśm, Rayon, kolejność wyników.
- `src/snapshot.rs` — opcjonalna, alokująca diagnostyka.
- `tools/` — eksport, cienki klient, oryginał Python, checker i benchmark.
- `tests/` — regresje, pełne CLI, odciski RNG/cen i licznik alokacji.
- `reference/` — zachowane wejście i dowód pochodzenia. Nie edytuj symulatora,
  żeby „naprawić” niezgodność z Rustem.

Licencja silnika i portu: Apache-2.0; zob. `LICENSE` i `NOTICE.md`.
