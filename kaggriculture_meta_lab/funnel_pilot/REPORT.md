# Następny krok: test całego lejka przed zmianą strategii

**2026-09-08. Test integracji zakończony. Nie promowano prawdziwego agenta i nie
wykonano żadnej submisji Kaggle.**

## Dlaczego ten krok

Główna gałąź `arena/01a0712c-riemann` zdążyła już podłączyć zweryfikowany adapter
Rust. Nie wykonywałem ponownie tej pracy ani jej bieżącego baseline'u TOP30.
Sprawdziłem brakujący poziom: **całe screen → promote → finals**, w tym
zachowanie wariantów, tożsamość par i decyzje rankingu.

Źródło: `290d360e3ba380eec9846597b57d6d57c4f57681` (kod sweepa taki sam jak w
wcześniej odczytanym `db7f09b...`). Tylko mały snapshot źródeł został pobrany
na naszą gałąź roboczą; nie przełączano ani nie nadpisywano gałęzi głównej.

## Znalezione i poprawione problemy

### 1. Gotowe warianty znikały przy deduplikacji

Klucz deduplikacji używał tylko `base` i `params`, pomijając `path`.
Trzy różne gotowe pliki z `params={}` zamieniały się w **jeden wariant**.
Poprawka uwzględnia ścieżkę, toleruje brak opcjonalnego `params` i odrzuca
niejednoznaczne, powtórzone nazwy różnych wariantów.

### 2. Finały identyfikowały przeciwnika po basename

Mapowanie `Path(opponent).stem` scalało różne pliki `.../main.py`.
W kontrolowanym teście agent `keeper` wygrywał z każdym, lecz ranking źródłowego
skryptu wskazywał **`buyer` jako zwycięzcę** i gubił część komórek macierzy.

Poprawka nadaje każdej parze osobny tag korelacyjny, niezależny od nazwy i nawet
od ścieżki pliku. Działa również wtedy, gdy dwie różne etykiety świadomie
wskazują tę samą zamrożoną politykę. Wynik finału zawiera teraz pełną strukturę
`pairwise`, nie tylko tekstową tabelę i ranking.

### 3. Brakowało kontroli kompletności etapów

Samo odrzucenie `error` nie dowodzi, że wszystkie gry dotarły dokładnie raz.
Dodano weryfikację liczby i multizbioru tożsamości wyników (tag, seed, seat,
przeciwnik), skończoności wartości oraz spójności margin/outcome.
Brakujący, zdublowany lub obcy rekord nie może przejść do rankingu.

### 4. Ścieżka baseline'u zależała od katalogu uruchomienia

Do etapów przekazywany był surowy względny wpis konfiguracji, mimo że już
wyliczono jego ścieżkę względem LAB-u. Poprawka przekazuje rozwiązaną ścieżkę.
Pilot celowo uruchamiał CLI z katalogu repozytorium, a nie z folderu LAB-u.

## Co uruchomiono

[Zielony przebieg CI #34281049065](https://github.com/peteraangelic-pixel/riemann/actions/runs/34281049065),
commit narzędzi `dddeb6959eb05ce8757e72a015feb81fbf254ff9`.

Nie zmieniano progów promocji, algorytmu Bradley–Terry ani reguł gry.

| Część | Python | Rust |
|---|---:|---:|
| Screen: 3 warianty × 2 seedy × 2 miejsca | 12 | 12 |
| Promote: 3 warianty × 10 seedów × 2 miejsca | 60 | 60 |
| Finals: 4 finalistów, 6 par × 2 seedy × 2 miejsca | 24 | 24 |
| B21 przeciw V7/Aastik/hybrid: po 2 seedy i oba miejsca | 12 | 12 |
| **Łącznie** | **108** | **108** |

**216 wykonanych gier**, limit pilota 128 na backend; limit samego lejka 100.
Próba z limitem 95 została odrzucona przed wykonaniem jakiejkolwiek gry
(projekcja wynosiła 96). Osiem dodatkowych testów regresyjnych przeszło.

Wyniki:

- gotówka i margin każdego meczu porównane jako bajty binary64;
- identyczna lista wszystkich wariantów, ranking screeningu i lista promocji;
- identyczne wartości Bradley–Terry, ranking i kompletna macierz finałów;
- identyczne wyniki dodatkowych gier z trzema realnymi kontrolami;
- zero przyjętych brakujących, obcych lub zduplikowanych wyników.

### To nie jest odkrycie nowego silnego agenta

Trzy polityki finału są **syntetycznymi kontrolami integracyjnymi**. Wydają
różne małe kwoty, żeby znana kolejność wymusiła wykonanie wszystkich etapów.
Nie są propozycjami do konkursu. Nazwa `INTEGRATION_ONLY_DO_NOT_PROMOTE` i
pole `agent_promoted=false` są celowe.

Czasy 96-gier smoke testu (Python 71,351 s, Rust 0,105 s) zapisano w JSON jako
diagnostykę. **Nie reklamuję ich ilorazu jako wydajności prawdziwego sweepa**:
syntetyczne polityki praktycznie nie prowadzą farmy, a test wymusza konkretne
przejście przez bramki. Właściwe benchmarki silnika są w `rust_port/VALIDATION.md`.

## Gotowy patch i odtwarzalność

- [Patch sweepa](funnel-identity-and-completeness.patch)
- [Wszystkie wyniki etapów i tożsamości gier](report.json)
- `source_manifest.json` — przypięte pliki i hashe źródeł
- `guard_tests.py` — przypadki regresyjne
- `pilot.py` — pełne, ograniczone uruchomienie CLI

Patch został sprawdzony na izolowanej kopii. **Nie zastosowano go automatycznie
na `arena/01a0712c-riemann`.** Przed aplikacją na nowszym HEAD:

```bash
git apply --check kaggriculture_meta_lab/funnel_pilot/funnel-identity-and-completeness.patch
git apply kaggriculture_meta_lab/funnel_pilot/funnel-identity-and-completeness.patch
```

Odtworzenie kompletnego testu w środowisku z Rustem:

```bash
python kaggriculture_meta_lab/branch_review/fetch_source.py \
  --manifest kaggriculture_meta_lab/funnel_pilot/source_manifest.json \
  --destination .cache/pilot-source
cargo build --release --locked --manifest-path kaggriculture_meta_lab/rust_port/Cargo.toml
python -m pip install -r kaggriculture_meta_lab/rust_port/requirements-framework.txt
python kaggriculture_meta_lab/funnel_pilot/pilot.py --source .cache/pilot-source --workers 4
```

## Co proponuję dalej — już praca nad siłą gry

Nie powtarzać symetrycznej drabinki zakupów pszenicy ani starego eksperymentu
V8-fertilizer. Nie zwiększać od razu skali do tysięcy mutacji.

Na głównej gałęzi jest już ukończony
[baseline świeżego TOP30](https://github.com/peteraangelic-pixel/riemann/actions/runs/34280083082).
Odczyt istniejącego raportu (bez ponownego uruchamiania):

| Pula | Wygrane B21 |
|---|---:|
| TOP1–10, wszystkie wybrane świeże rekordy | **23/100** |
| TOP11–20 | **16/100** |
| TOP21–30 | **36/100** |
| Łącznie TOP30 | **75/300** |

To **open-loop replay stress**, nie odtworzenie rankingu live. Tylko 72/150
slotów korpusu pochodzi z najlepszej wskazanej aktywnej submisji danego zespołu;
reszta reprezentuje inne świeże submisje. Trzeba zachować obie perspektywy,
a wspólnego epizodu nie rozdzielać między trening i holdout.

Najbliższy sensowny plan:

1. Zastosować poprawkę lejka, zachowując B21 i trzy kontrole bez zmian.
2. Wybrać kilka **jawnie oznaczonych przypadków odkrywczych TOP10 z podzbioru
   najlepszych submisji**, nie mieszać ich z późniejszym holdoutem.
3. Dla nich policzyć przyczyny strat: produkcję i sprzedaż według produktu,
   utracone zbiory, koszt i wykorzystanie pracy oraz wpływ presji rynku.
   Sama końcowa gotówka nie pozwala jeszcze wskazać przyczyny. Dobry pierwszy
   zestaw odkrywczy to poniższe **wysokodochodowe porażki** z najlepszych
   wskazanych submisji TOP10 (średnie z obu miejsc):

   | Przeciwnik | Epizod | Gotówka B21 | Przewaga B21 |
   |---|---:|---:|---:|
   | Ad Space Available | 106841276 | 115 356 | −2593 |
   | Tarang222 | 106846940 | 121 716 | −7524 |
   | Matthew Huang | 106841278 | 143 132 | −8557 |

   Epizod 106841278 występuje też po stronie innego uczestnika: **żadna jego
   kopia nie może być późniejszym niezależnym holdoutem**. To propozycja wyboru
   przypadków, nie diagnoza przyczyny ani rozpoczęty trening.
4. Dopiero po tej diagnozie przetestować **jedną** zmianę (np. wykorzystanie już
   opłaconych tur pomocników lub istniejącego nawozu bez nowych objazdów).
   Najpierw sprawdzić, czy w danych w ogóle występują takie okazje; jeśli nie,
   nie generować bezwartościowego gridu.
5. Na pierwszą rodzinę zmian ustalić **limit 200 gier**, z kontrolą B21 i
   osobnym wykazem utraconych wygranych. Tylko finalista przechodzi na
   niewidziane zespoły/epizody TOP11–20; ten test nie służy do kolejnego
   dostrajania tego samego C10. Dopiero potem osobny klon C20 i analogicznie C30.

Nie ma jeszcze nowego agenta z udowodnioną przewagą ligową. Jest natomiast
sprawdzony lejek, który nie zgubi wariantu ani nie wybierze zwycięzcy przez
przypadkową nazwę pliku — to właściwy fundament kolejnego eksperymentu.
