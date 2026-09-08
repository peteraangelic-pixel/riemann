# Audyt `arena/01a075fa-riemann` i ulepszony backend LAB-u

**2026-09-08. Wynik: zachować wspólny, zweryfikowany rdzeń Rust; przejąć ideę
integracji z LAB-em, ale utwardzić ją przed użyciem do selekcji agentów.**

## 1. Co faktycznie porównaliśmy

- Kod gałęzi źródłowej: `99c364e55fc88bd03954ab93e7b742fedac45101`.
- Sprawdzono też późniejszy HEAD `190989e605749a435b33e2075411e2ea330b152f`:
  dodaje dokument audytu i konfigurację sweepa, bez zmian rdzenia/backendu.
- Nasza sprawdzona implementacja: `7ec265adc078f7ad7fa4967ed2a152b4fc41bd3c`.
- [Porównanie obu implementacji](https://github.com/peteraangelic-pixel/riemann/actions/runs/34238504440).
- [Pełne CI naszego portu](https://github.com/peteraangelic-pixel/riemann/actions/runs/34238504426).

**Dziewięć plików `src/` oraz Cargo.toml i Cargo.lock są identyczne bajtowo.**
Obie kompilacje dały identyczny binarz SHA-256:
`be94f33974132f3825f74c8475d2112c40dd29588259ed49299d5974fd20aa84`.
Dokument `ważne.md` na badanej gałęzi wprost opisuje przejęcie nowszego rdzenia.
Nie ma więc podstaw, by ogłaszać jeden z tych rdzeni szybszym od drugiego.

Różnice warte audytu są **wokół silnika**: `rust_backend.py`, podpięcie sweepa,
generator strukturalnych wariantów i sposób przygotowywania danych.
Gałęzi źródłowej nie zmieniano ani nie przełączano naszego checkoutu.

## 2. Najcenniejsze rozwiązania — ledger

| Status | Rozwiązanie | Co z nim zrobiliśmy |
|---|---|---|
| **Przejęte i utwardzone** | Jedna paczka Rust dla statycznych polityk, Python dla reaktywnych | Nowe `tools/lab_backend.py` z zachowaniem sześciopolowych zadań LAB-u |
| **Przejęte i utwardzone** | Eksport taśmy raz zamiast procesu na seed | Snapshoty, cache po ścieżce/zawartości, nazwy bez kolizji, sprzątanie eksportów |
| **Rozszerzone** | Obsługa obecnych zamrożonych kontroli | B21, V7, V8 Aastik, V8 hybrid i szablon generatora, bez wykonywania kodu przy klasyfikacji |
| **Nowe** | Rozpoznanie faktycznie statycznej polityki | Audytowane AST funkcji i ograniczony evaluator danych; nie sama obecność `ACTIONS` |
| **Nowe** | Powtarzające się warianty / gry | Fingerprint operacji, normalizacja brakujących pól do ich domyślnych znaczeń, bezpieczne reużycie wyników statycznych gier |
| **Nowe** | Mieszane horyzonty i reguły rąk | Osobne buckety; przycinanie podąża za wejściowym agentem, nie miejscem |
| **Nowe** | Wiarygodny fallback | Przy braku binarza / nieobsługiwanej polityce, nie ukrywanie błędu już uruchomionej paczki |
| **Naprawione** | Użycie na Windows | Wybór `kg_sim.exe`; sam `Path.exists()` nie uwzględnia PATHEXT |
| **Warto zachować jako badania** | Generator zmian ciała taśmy i kontrola tożsamości | Wspieramy jego statyczny szablon; nie kopiujemy bez testów samych operatorów mutacji |
| **Wspólne, bez zmian** | Wspólny rynek, CPython RNG, tablice, brak alokacji podczas tur | Ten sam rdzeń; nie wymaga ponownego przepisywania |

Generowanie wariantu nie jest dowodem, że agent będzie wygrywał. Ten audyt
nie trenuje nowej strategii ani nie dokonuje submisji Kaggle.

## 3. Potwierdzone problemy w adapterze źródłowym

W każdym przypadku uruchomiono rzeczywisty binarz i porównano wynik z
niezmienionym frameworkiem Kaggle 1.32.7. Nowy adapter dał wynik referencyjny
we wszystkich pięciu grupach.

| Przypadek | Poprawny wynik / kolejność | Adapter z badanej gałęzi |
|---|---|---|
| Dwa różne pliki `one/agent.py`, `two/agent.py` | 2990 : 2960 | **2980 : 2960** — kolizja nazwy eksportu |
| W jednej paczce `steps=2` i `steps=3` | drugi mecz 2980 : 2920 | **2990 : 2960** — użyto pierwszego horyzontu |
| Reaktywny agent ma pomocnicze `ACTIONS`, lecz wybiera PASS | **3000 : 2960, wygrana** | **2010 : 2960, porażka** — zamrożono niewłaściwą politykę |
| Kandydat przycina ręce, przeciwnik jest surowy | **3017 : 2990** na obu miejscach | **3017 : 3017** — globalne przycinanie zmienia przeciwnika |
| Python kończy zadania w odwrotnej kolejności | seedy **11, 12, 13** | **13, 12, 11** — wynik `as_completed` sklejono pozycyjnie |

W ostatniej grupie same rekordy nadal mają własne seedy/tagi, ale kolejność
zwracanej listy nie odpowiada zadaniom. To błąd dla klienta parującego wejścia
z wynikami, nie twierdzenie, że każda agregacja po tagach jest przez to błędna.

Dodatkowe problemy potwierdzone sondami:

- Dla **8 zadań i jednego pliku** `_load_actions` jest wywoływane **17 razy**.
  Klasyfikacja ponownie importuje/dekoduje moduł per zadanie; eksport dodaje
  kolejne wywołanie. Nowy adapter czyta/kompiluje źródło **raz**.
- Zegar komunikatu `[rust] ...` startuje dopiero po klasyfikacji i eksporcie.
  Nie jest pomiarem całego wywołania backendu.
- V8 Aastik i V8 hybrid są statycznymi strumieniami, ale stare rozpoznawanie
  wymaga `len(ACTIONS)==2`, więc kieruje je do Pythona. Nowy kompilator
  uwzględnia ich pojedynczy strumień i statyczne podmienianie otwarcia.
- Przy wstrzykniętej awarii Rust stary `run_auto` najpierw wykonał jeden mecz
  Python, potem ponownie całą dwuelementową paczkę: wywołania fallbacku `[1,2]`.
  Nowy adapter przerwał jawnie, bez ponownego wykonania (`[]`). Awaria procesu
  nie jest automatycznie zamieniana w „udany, tylko wolniejszy” przebieg.
- Domyślne wykrywanie pliku `kg_sim` nie znajduje samego `kg_sim.exe`.
  Poprawka nazwy została przetestowana; **nie jest to pełny benchmark Windows**.
- `mkdtemp` bez kontekstu sprzątającego zostawia wyeksportowane pliki. Nasze
  testy sprawdzają usunięcie katalogów także przy błędzie.

## 4. Czy nowy kompilator nie zmienia agentów?

Nie importuje ich do rozpoznawania. Najpierw sprawdza **całe AST funkcji**,
łącznie z dekoratorami, argumentami i adnotacjami, a potem interpretuje tylko
literalne dane, zatwierdzone dekodowanie JSON/zlib/base85 oraz znane mutacje
otwarcia. Nieznane funkcje, efekty uboczne i nieudowodnione kształty danych
trafiają do Pythona, nie do fałszywej statycznej taśmy.

Dowody:

- **23 104 porównania akcji** z faktycznie wykonywanymi czterema zamrożonymi
  kontrolami: oba miejsca, każdy krok 0–719, kroki poza końcem taśmy oraz
  0/1/5/12 żywych pomocników.
- **16 pełnych gier na rzeczywistym frameworku**, porównanych z nowym backendem:
  B21 przeciw każdej kontroli, dwa seedy, oba miejsca.
- Szablon wygenerowanego wariantu strukturalnego został zdekodowany bez utraty
  danych; nie pominięto jego importowych nadpisań otwarcia.
- Dodatkowe testy odrzucają m.in. reaktywne `ACTIONS`, podmienione helpery,
  dekoratory, duplikaty funkcji, efekty uboczne oraz dane powodujące błąd
  Pythonowego wrappera zamiast emisji poprawnej akcji.

To kompilator **konserwatywny**, nie interpreter dowolnego Pythona. Nowy,
semantycznie równoważny styl kodu może zostać skierowany do Pythona. Cena
fałszywego odrzucenia to czas; cena fałszywej akceptacji to testowanie innej
polityki, niż użytkownik zamierzał.

## 5. Zmierzona poprawa czasu całego adaptera

Jeden runner: **AMD EPYC 7763, 4 logiczne CPU**, Rust 1.85.1. Ta sama para B21,
256 seedów/zadań, naprzemiennie oba miejsca, trzy powtórzenia.
Kolejność pomiaru stary/nowy adapter była zmieniana między powtórzeniami.
Wszystkie rekordy wynikowe były identyczne.

| Całe wywołanie adaptera | Mediana | Próbki |
|---|---:|---|
| `rust_backend.run_rust` z badanej gałęzi | **5,669221 s** | 5,440352 / 5,669221 / 5,694276 |
| Nowy `lab_backend.run_report` | **0,098613 s** | 0,099113 / 0,098613 / 0,097757 |

**5,669221 / 0,098613 = 57,49×** w tym workloadzie.

To rzeczywista poprawa **warstwy przygotowania i obsługi zadań**, nie nowy
szybszy silnik. Rdzeń i binarz są identyczne. Głównym źródłem różnicy jest
usunięcie setek powtórnych importów/dekodowań i wielokrotnego hashowania całej
taśmy. Mierzono pełne wywołanie, nie sam końcowy subprocess.

Nie wolno mnożyć 57,49× przez wcześniejsze 180–220× i reklamować wyniku jako
przyspieszenia całego LAB-u. To różne punkty odniesienia. Dla wielu unikalnych
polityk, dużego udziału fallbacku lub innego sprzętu wynik będzie inny.
W szczególności nie jest to pomiar całego screen/promote/finals ani uczenia
polityk reaktywnych.

## 6. Generator — co zachować, co sprawdzić przed użyciem

Przydatne są: mutacje ciała zamiast wyłącznie otwarcia, jawne parametry,
zamrożona kontrola i samodzielne pliki wariantów. Nasz adapter obsługuje jego
statyczny szablon i rozpoznaje powtarzające się efektywne taśmy.

Sondy ujawniły jednak:

- `liquidate_from=600` rozpoczyna pełną likwidację nadal w **718**, nie w 600.
- W porównaniu cutoff 600 i 700 surowy JSON różni się obecnością pustych pól,
  lecz **efektywne zlecenia są identyczne**. Nowe fingerprinty wykrywają tę
  tożsamość. Nie jest to dowód, że wszystkie semantyczne no-opy są rozpoznawane.
- `fert_scale=0` nadal kupuje **1** jednostkę zamiast zerowej ilości.
- `PRODUCT_KINDS` nie zawiera TOMATO.
- Skalowanie HIRE do 1,3 dało **50 tur z ponad 10 zleceniami**. Silnik ucina
  nadmiar, więc nominalna liczba HIRE w pliku nie opisuje liczby wykonywalnych
  zleceń i może wypchnąć inne zakupy.

Nie przepisano tych operatorów do produkcyjnego silnika ani nie promowano
wygenerowanego agenta. Warto dodać testy efektywnego wpływu parametru, limitów
zleceń i routingu, zanim przeznaczy się kolejne tysiące gier na taki grid.

## 7. Walidacja produkcyjna po zmianach

[Zielone CI](https://github.com/peteraangelic-pixel/riemann/actions/runs/34238504426):

- Rust **17/17 debug** i **17/17 release**;
- Python/CLI/backend **61/61**;
- **585 meczów / 87 seedów / 22 597 stanów**, bez różnic względem Pythona;
- **16** niezależnych prób realnego frameworka;
- 14 000 wyników zgodnych między 1/4/16 wątkami i trzema powtórzeniami;
- gorąca ścieżka nadal bez alokacji; hash natywnego binarza niezmieniony.

Nowy adapter nie naprawia sam błędów wewnątrz dostarczonego callbacku Python,
jeśli ten fałszywie raportuje sukces. Dla starego LAB-u nadal ważny jest
wcześniejszy `patches/lab-replay-correctness.patch` (seed replaya, indeks akcji,
wykrywanie awarii). Nie utożsamiamy porządnej walidacji wiersza z dowodem
poprawności całej obcej implementacji fallbacku.

## 8. Jak skorzystać — bez ruszania gałęzi źródłowej

Dokument API: [`../rust_port/LAB_BACKEND.md`](../rust_port/LAB_BACKEND.md).

```python
from kaggriculture_lab import tournament
from rust_port.tools.lab_backend import run_auto, run_report

rows = run_auto(jobs, workers=16, python_runner=tournament.run)
report = run_report(jobs, workers=16, python_runner=tournament.run)
print(report.metrics)
```

`sweep-integration.patch` pokazuje minimalną zmianę importu w sweepie.
**Najpierw trzeba dostarczyć nowe moduły `rust_port/tools/` do danego checkoutu**,
a dopiero potem zastosować patch i wykonać testy. Nie zastosowano go zdalnie
na `arena/01a075fa-riemann` ani na głównej gałęzi agentów.

Testy/benchmarki i źródłowy manifest są odtwarzalne:

```bash
python kaggriculture_meta_lab/branch_review/fetch_source.py --destination .cache/peer-port
python kaggriculture_meta_lab/branch_review/compare_branch.py --source .cache/peer-port --jobs 256 --repeats 3
```

Szczegółowe dane: [`review-results.json`](review-results.json).
Wyniki dotyczą przypiętej wersji, nie nieznanych przyszłych zmian tamtej gałęzi.
