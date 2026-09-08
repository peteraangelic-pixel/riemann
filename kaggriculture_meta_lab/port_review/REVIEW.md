# Przegląd drugiego portu Rust i wyjaśnienie przyspieszenia

**2026-09-08. Wniosek: nie zastępować obecnego silnika tym ZIP-em. Zachować
przydatne pomysły, ale oddzielić je od nieukończonej walidacji implementacji.**

## Materiał i metoda

Oceniony plik użytkownika:
`kaggriculture_meta_lab/kaggriculture_rust_port_updated_20260908.zip`.
SHA-256: `d194d7197f0adcad4a6e6a1eedde6b6eb319e3748d55437f63da9a96c9b7b740`.
Archiwum pozostawiono bez zmian. Pracowano na izolowanych kopiach.

[Wykonany przegląd CI](https://github.com/peteraangelic-pixel/riemann/actions/runs/34210108491):
Rust 1.85.1, Python 3.12.14, Linux/glibc 2.35, **4 logiczne CPU**,
Intel Xeon Platinum 8370C. Oba porty i eksperyment LTO kompilowano i mierzono
na tym samym runnerze. Nie użyto żadnych kluczy Kaggle i nie wysyłano agentów.

Rozróżniamy trzy rzeczy:

1. **Oryginalny ZIP**, bez poprawek — wynik kompilacji.
2. **Kopia z poprawkami wyłącznie kompilacyjnymi** — wynik działania i pomiary.
3. **Nasza wersja produkcyjna** — bez zmian reguł i bez eksperymentalnego LTO.

Zielony status workflow przeglądowego oznacza, że audyt się wykonał, **nie że
alternatywny port zaliczył wszystkie testy zgodności**.

Pełne dane: [`review-results.json`](review-results.json).
Mechaniczna poprawka: [`compile-only.patch`](compile-only.patch).
Nie jest to patch naprawiający logikę drugiego symulatora!

## 1. Co jest dobre w drugim porcie

- Osobne typy `Crop`, `Animal`, `Product` oraz np. `Plant(Crop)` lepiej wyrażają
  domenę niż możliwość użycia dowolnego `Item` w wewnętrznym API. To wartościowy
  kierunek przy rozbudowie API Rust. Nasz parser JSON już odrzuca nielegalne
  kombinacje, więc nie wymieniałem teraz całego sprawdzonego modelu tylko dla
  tej zmiany typów.
- Wygodny format pojedynczego strumienia `[step]`, kopiowanego na oba miejsca.
  Przejąłem tę ideę **jako jawny eksport po stronie Pythona**, a nie automatyczne
  rozluźnienie walidacji binarza.
- Czytelna mapa funkcji Python → Rust. Dodałem analogiczny dokument
  [`../rust_port/SOURCE_MAPPING.md`](../rust_port/SOURCE_MAPPING.md).
- Wspólny rynek, jednoczesne wyceny przed commitami, zachowanie kolejności
  kluczy ekwipunku, sorted-shop RNG i podział Rayona po całych meczach są
  sensownie zaprojektowane. Te dobre rozwiązania są również w naszym porcie.
- Status ZIP-a uczciwie zaznaczał, że nie uruchomiono kompilatora. Po usunięciu
  blokad kompilacji **RNG i domyślne krzywe cen rzeczywiście przeszły próby**:
  120 000 słów MT19937, mieszane `random/choice`, 270 009 wycen.

## 2. Oryginalny ZIP nie kompiluje się

`cargo build --release` zakończył się kodem **101**. Rustc zgłosił osiem
komunikatów wynikających z czterech kategorii problemów:

- prywatny import `tape::Tape` używany poza modułem (`E0603`);
- niejednoznaczne `step as i32 < ...`, wymagające nawiasów wokół rzutowania;
- domyślna pojemność szopy `i32` przekazana do funkcji oczekującej `i64`;
- mieszanie `i64`, JSON `Value` i `Result` w obsłudze seeda zadania (`E0308`).

Do dalszej diagnozy powstała oddzielna kopia z poprawioną widocznością typów,
nawiasami i typami wyrażeń. **Nie poprawiano zamiany miejsc, konfiguracji,
RNG, ekonomii ani kolejności transakcji.**

## 3. Zgodność po samej naprawie kompilacji

| Grupa prób | ZIP po naprawie kompilacji | Nasz port |
|---|---:|---:|
| Pełne B21 self-play, bez reverse, seedy 0–63 | 64/64 | 64/64 |
| Pełne B21 z przycinaniem, również skrajne seedy | 8/8 | 8/8 |
| Pełne asymetryczne pary, bez reverse | 8/8 | 8/8 |
| Pełne asymetryczne pary z reverse | **0/8** | 8/8 |
| Pozostałe celowane przypadki | **1/14** | 14/14 |
| **Łącznie** | **81/102** | **102/102** |

To celowo zróżnicowane testy, **nie statystyczny szacunek procenta błędnych
meczów w normalnym ruchu**. Dodatkowo osobno sprawdzono poprawny CSV z
przecinkiem w nazwie pliku: nasz port go obsłużył, drugi nie.

### Najważniejsze wykryte rozbieżności

| Przypadek | Python / nasz port | ZIP po naprawie kompilacji |
|---|---|---|
| Prosta zamiana miejsc | `[2970, 2980]` | `[2980, 2970]` |
| Asymetryczny pełny mecz, seed 0, reverse | `[64231, 43868]` | `[36869, 54818]` |
| `episodeSteps=1`, zakup nasiona | `[2990, 3000]` | `[3000, 3000]` |
| Zakup 2 nasion, ilość `"2"` lub `2.9` | `[2980, 3000]` | `[3000, 3000]` |
| Ilość `2**31`, zakup do wyczerpania pieniędzy | `[0, 3000]` | `[3000, 3000]` |
| `PLACE COW 0` na pasującej strukturze, później sprzedaż nawozu | `[2700, 3000]` | `[2600, 3000]` |
| Zmienione początkowe `I0` pszenicy | `[2974, 3000]` | `[2983, 3000]` |
| Ułamkowa cena bazowa `25.5` | `[2973, 3000]` | `[2974, 3000]` |
| Nieznana funkcja ceny: fallback do liniowej | `[2975, 3000]` | `[2974, 3000]` |
| Pełna specyfikacja z `startingMoney.default=5000` | `[5000, 5000]` | `[3000, 3000]` |
| Granica pętli 100k, milion początkowej gotówki | `[10, 1000000]`, ostrzeżenie | `[0, 1000000]`, bez ostrzeżenia |

Główne przyczyny w kodzie archiwum:

- `src/main.rs:59–64` wybiera inne listy dla reverse, ale `sim::simulate`
  nadal przypisuje A do farmy 0, B do farmy 1, a następnie wynik jest odwracany.
  To **nie tylko błąd wyświetlania**: kolejność farm wpływa również na rynek i RNG.
- `src/tape.rs` wymaga ilości `i32`; nie realizuje konwersji `int(...)` dla
  ciągów, booli i ułamków, a większe poprawne ilości odrzuca zamiast ograniczyć
  ich wykonanie zasadami rynku.
- Parser PLACE odrzuca `n <= 0`, zanim silnik sprawdzi, czy chodzi o umieszczenie
  zwierzęcia. W oryginale na pasującej strukturze `n` jest ignorowane.
- `src/sim.rs:new_market` zawsze rozpoczyna przy 10 000; nadpisane I0 jest
  później używane do cen, ale nie do inicjalizacji zapasu.
- `load_config` nie rozpakowuje deskryptorów pełnej specyfikacji, niektóre
  ułamkowe parametry ignoruje, a nieznaną nazwę funkcji zastępuje funkcją
  domyślną produktu zamiast liniowym fallbackiem.
- Limit pętli pozwala wykonać 100 000 jednostek zamiast oryginalnych 99 999.
- `line.split(',')` nie jest parserem CSV i rozbija cytowane nazwy plików.

Dodatkowo `i64` dla gotówki różni się od Pythonowego `float` powyżej 2⁵³.
To rzadki, skrajny przypadek konfiguracji — **nie przyczyna typowych porażek** —
ale pokazuje, dlaczego „pieniądze całkowite” nie są automatycznie wierniejszym
portem istniejącego silnika.

W wielu powyższych przypadkach ZIP zwraca poprawnie wyglądający JSON
z `errors: []`, mimo innego wyniku. Dlatego sam brak crasha nie jest walidacją.

## 4. Alokacje i pokrycie testami

W testowej kopii dodano licznik alokatora, włączany **po stworzeniu stanu**.
Pomiar dał to samo w debug i release:

| Operacja | Alokacje/reallokacje ZIP-a |
|---|---:|
| DROP przy niepustym ekwipunku | **1** |
| Zmiana dnia bez pomocników | **1** |
| Pierwszy HIRE | **2** |

Powody: klonowanie `Inventory.keys`, dynamiczny wektor słów seeda RNG,
rozszerzanie wektorów pomocników i ekwipunków. Tablica planszy `[Tile;100]`
nie wystarcza do spełnienia wymogu braku alokacji w gorącej ścieżce.
Instrumentacja nie była włączona w binarzu używanym do benchmarków.

Dołączony `parity_check.py` generuje tylko ruch/PASS bez transakcji i drukuje
wyniki Rusta. **Nie uruchamia referencyjnego symulatora Python i nie porównuje
wyników.** Takie przypadki mają stale 3000/3000 i nie sprawdzają ekonomii.
W archiwum brakuje także gotowego eksportu pełnego stanu do porównań tur.

## 5. Uczciwy wspólny benchmark

Ponieważ część semantyki ZIP-a jest błędna, pomiar porównawczy obejmuje
**wyłącznie poprawnie odtwarzany wspólny workload**: ta sama taśma B21,
64 seedy, bez zamiany miejsc, 720 stanów / 719 tur. Trzy powtórzenia, mediana.
Binarz alternatywny ma wyłącznie poprawki kompilacyjne, nie poprawki gry.

Ten sam kod Python zapisuje CSV, uruchamia każdy binarz, czyta i sprawdza JSON.
W pomiarze są start procesu, ładowanie taśm, symulacja oraz I/O. Przygotowanie
samych danych testowych jest poza pomiarem dla obu portów.

| Wariant | Czas 64 meczów | Przyspieszenie vs szeregowy Python |
|---|---:|---:|
| Python, bezpośredni interpreter | **5,105620 s** | 1× |
| Nasz, proces na każdy mecz | 0,476345 s | **10,72×** |
| ZIP, proces na każdy mecz | 0,716315 s | 7,13× |
| Nasz, batch / 1 wątek | 0,053961 s | **94,62×** |
| ZIP, batch / 1 wątek | 0,075508 s | 67,62× |
| Nasz, batch / 4 wątki | **0,028071 s** | **181,88×** |
| ZIP, batch / 4 wątki | 0,035504 s | 143,80× |

Dodatkowo ten sam zweryfikowany workload powiększono do **2048 meczów**.
Wyniki obu portów były równe także dla całej tej paczki:

| Wariant, 4 wątki | Mediana | Mecze/s |
|---|---:|---:|
| Nasz, produkcyjne thin LTO | **0,581116 s** | **3524** |
| ZIP, po naprawie kompilacji | 0,833176 s | 2458 |
| Nasz kod, eksperymentalne fat LTO | 0,625282 s | 3275 |

W tym pomiarze nasz port był **1,26× szybszy od ZIP-a przy 64 grach**
i **1,43× przy 2048**. To nie jest gwarancja przewagi dla każdego możliwego
workloadu ani porównanie dwóch całkowicie poprawnych zamienników.

Samo przełączenie naszego kodu na `fat LTO` nie pomogło: w większej paczce
było około 7,6% wolniejsze. Nie traktuję trzech prób jako uniwersalnego prawa,
ale nie ma tu dowodu uzasadniającego zmianę ustawień produkcyjnych.
Pozostaje `thin LTO`.

## 6. Skąd wcześniejsze 130×, około 190×, a potem ponad 200×?

Wzór jest prosty:

```text
przyspieszenie = mediana czasu Python / mediana czasu Rust
```

Dla **najnowszej wersji po dodaniu usprawnień z przeglądu**, w
[zielonym CI #34211248146](https://github.com/peteraangelic-pixel/riemann/actions/runs/34211248146):

```text
Python, 64 gry:          5,258616317 s
Rust batch, 4 wątki:     0,028515361 s
5,258616317 / 0,028515361 = 184,41×
```

Osobny proces na mecz w tym samym przebiegu: 0,668028 s, czyli 7,87×.
Suma kontrolna binarza jest **identyczna z poprzednio wydaną wersją**
(`be94f339…aa84`): reguł ani natywnego kodu silnika nie zmieniano.
Przeszły testy Rust 17/17 w debug i release, Python 37/37, 585 meczów / 87 seedów,
22 597 porównań stanu, 16 prób rzeczywistego frameworka oraz duży batch 14k.

Dla poprzedniej walidacji tego samego silnika, w
[poprzednim zielonym CI](https://github.com/peteraangelic-pixel/riemann/actions/runs/34206326321):

```text
Python, 64 gry:          5,734315274 s
Rust batch, 4 wątki:     0,025866662 s
5,734315274 / 0,025866662 = 221,69×
```

Dla bieżącego wspólnego testu z ZIP-em:

```text
5,105619709 / 0,028071295 = 181,88×
```

To ten sam produkcyjny silnik, ale inny runner (poprzednio AMD EPYC 7763,
teraz Intel Xeon 8370C) i jawnie wspólny workload bez reverse. Wcześniejszy
wynik około 136× pochodził jeszcze z innego pomiaru/runnera oraz wcześniejszej
wersji obsługi I/O. Ostatnia walidacja po dodaniu eksportera odbyła się na AMD EPYC 9V74.
**Utrzymany jest rząd wielkości, nie stała 221,69 na każdym
sprzęcie.** Nie wnioskujemy o regresji kodu z porównania różnych maszyn.

Równie ważne zastrzeżenia:

- Python jako punkt odniesienia jest **szeregowy**. Nie twierdzimy, że Rust
  jest 182–222× szybszy od Pythona uruchomionego w 16 procesach.
- 182–222× dotyczy **batcha**. Osobny subprocess i ponowne parsowanie taśmy
  dla każdego meczu dawały około 10×, nie 200×.
- To nie jest samo skalowanie Rayona. W ostatnim wydanym pomiarze batch z jednym
  wątkiem był około 112,59× szybszy od Pythona, a przejście 1 → 4 wątki dało
  dodatkowo około 1,97×; iloczyn wynosi 221,69×.
- Pomiar obejmuje symulację taśm i jej I/O, **nie cały LAB**, generowanie nowych
  polityk, wywoływanie reaktywnych agentów, kompletne kopiowanie obserwacji
  przez framework ani statystyki turniejowe.
- 16 wątków na runnerze z 4 CPU nie jest testem 16 fizycznych rdzeni.
- Żaden współczynnik nie jest obietnicą, że cały trzygodzinny sweep potrwa
  kilkanaście sekund.

## 7. Co rzeczywiście przejęto

1. **Jawne normalizowanie pojedynczego strumienia** do dwóch miejsc:

   ```bash
   python tools/export_tape.py one_policy.json --single-stream -o work/opponent.json
   ```

   Walidacja binarza pozostaje ścisła. Błędne `[1,2]`, puste dane i tablice
   w tablicy nie zamienią się po cichu w słabych przeciwników PASS. Kopie obu
   miejsc są niezależne. Eksporter nie nadpisze pliku wejściowego.

2. **Mapa źródeł** Python → Rust ułatwiająca przyszły audyt zmian reguł.
3. **Nowe regresje** dla ignorowanego argumentu `PLACE COW 0/-3` i granicy pętli
   99 999 jednostek — jako zabezpieczenie naszego działającego kodu.

Nie przeniesiono błędnej logiki reverse, uproszczonego CSV, węższych typów
liczbowych, dynamicznych alokacji ani `fat LTO`. Nie zmieniono reguł naszego
silnika, agentów, submisji ani innych gałęzi.

Odtworzenie audytu (w środowisku z Rustem i dostępem do zależności):

```bash
python kaggriculture_meta_lab/port_review/compare_ports.py \
  --seeds 64 --repeats 3 --large-games 2048
```

Wyniki i kopie diagnostyczne trafiają do ignorowanego `.cache/port-review/`.
Oryginalny ZIP pozostaje nienaruszony.
