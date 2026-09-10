# Audyt opinii zewnętrznych i plan działań — 2026-09-10

Ten dokument utrwala użyteczne punkty z przekazanych raportów: analizy innej gałęzi (GermanJurado1), audytu Groka i audytu Claude'a. Rozdziela fakty zweryfikowane od hipotez i zapobiega ponownemu promowaniu kandydatów na podstawie jednego wąskiego testu.

## Najważniejsze doprecyzowanie wersji

Żadna wysłana wersja nie zawiera nowego stosu `reactive_state.py` + `reactive_candidates.py`.

- V13 (`agent_v13_b21_recovery.py`) to taśma B21 z kompaktową warstwą recovery.
- V14 (`agent_v14_subin_g2_milk0.py`) to G2 z jedną zmianą: rezerwa mleka 1 → 0.
- Estymator i generator kandydatów były dotąd samodzielną infrastrukturą laboratoryjną. `reactive_selector.py` domyka teraz ścieżkę estymator → kandydaci → selektor → obiekt akcji, lecz nadal nie jest samodzielnym, spakowanym agentem ani wersją V.

## Punkty zweryfikowane

1. **Offset replayu.** Wiersz 0 replayu jest inicjalizacją; akcja kroku środowiska `s` znajduje się w wierszu `s+1`. Python używa `step+1`, a Rust `steps[1:]`. Regresje znajdują się w `tests/test_replay_regressions.py`.
2. **Seed.** Pierwszym źródłem jest `replay.info.seed`; zerowy fallback nie jest normalnym wynikiem. Brak seeda/błąd agenta musi być błędem próbki.
3. **Awarie agentów.** Runner sprawdza ERROR/INVALID/TIMEOUT również w historii, ponieważ interpreter może nadpisać status końcowy na DONE. Takiej gry nie wolno zaliczać jako remisu 0–0.
4. **Częstotliwość sklepów.** `turnsPerDay=24`, a `townShopSellInterval=4`, więc sklepy konsumują sześć razy dziennie. Stała modelująca sześć zdarzeń na dzień nie ma podejrzewanego błędu ×4.
5. **Pole (4,4).** Dostęp do szopy jest sprawdzany pozycyjnie. Struktura/zwierzę na tym polu nie wyłącza dostępu; zarzut kolizji semantycznej nie został potwierdzony przez silnik.
6. **Parzystość Rust/Python.** Istnieją testy różnicowe i porównanie 64 gier. Rust jest właściwy dla statycznych taśm i wspieranych overlayów; polityki reaktywne bez równoważnego overlayu muszą iść przez audytowany silnik Python.
7. **Rekonstrukcja GermanJurado1.** Niezależnie od niedostępnego commita `44526e5`, odtworzono seat 0 epizodu `107218640` z `TOP15.7z`. Seed `726872323`, 720 wierszy, wynik replayu `[131745, 126919]`. Uruchomienie obu poprawnie przesuniętych taśm odtworzyło dokładnie `[131745.0, 126919.0]`, statusy DONE/DONE. Kandydat: `agents/candidates/champion_tape_germanjurado1.py`; ma 719 akcji i nie otrzymał numeru V.

## Wartościowe zalecenia przyjęte

- Mierzyć w zamkniętej pętli, parami na tych samych seedach i obu miejscach; raportować win rate, margines, wariancję i awarie.
- Obowiązkowe kontrole obejmują G2 (praktycznie silny live), G4/B21 oraz aktualnych kandydatów. Dominacja tylko nad G4/B21 nie wystarcza.
- Oddzielać: poprawność jednostkową modułu, open-loop na replayach, closed-loop i dowód live. Te kategorie nie są zamienne.
- TOP15 jest głównym, ale szybko starzejącym się korpusem. Zachować świeży holdout i odświeżać replaye silnych graczy.
- Stosować sekwencyjne księgowanie rynku: sprzedaże, wpływy, zakupy, rezerwa gotówki, rezerwa paszy i limity ilości. `reactive_selector.py` realizuje pierwszą bezpieczną wersję.
- Kandydaci jednostek muszą być ograniczeni, deterministyczni, z kontrolą kolizji i legalnym PASS-em.
- Hodowla, towary premium, popyt sklepów i schyłek gry pozostają ważnymi elementami funkcji wartości.
- Rust + Rayon należy preferować dla dużych zgodnych batchy, ograniczając minuty Actions. Brak parytetu ma kończyć batch błędem, nie cichym fallbackiem.
- Otwarta taśma elitarnego gracza to wartościowy prior/teacher, lecz nie dowód reaktywności ani transferu na live.

## Punkty częściowo trafne lub wymagające kontekstu

- **G3/G4 i dodatkowe pola.** Ryzyko niezgodności schematu jest ogólnie słuszne. Jednak dodatkowe cechy profili strukturalnych są wejściem generatora/overlayu Rust, a nie polami wysyłanymi do środowiska przez `market_overlay.py`. Każdą nową ścieżkę nadal trzeba testować na realnym schemacie.
- **Try/except w agencie.** W paczce submission bezpieczny PASS po wyjątku może ograniczyć katastrofę. W laboratorium blanket `try/except` jest niewskazany, bo ukrywa defekt; evaluator ma oznaczać grę jako błąd. Wrapper submission i audyt awarii to dwa odrębne wymagania.
- **Nazwa B21.** To zamrożona polityka referencyjna, nie deklaracja, że jest obecnie najlepsza. Dokumentacja i raporty powinny używać nazw „frozen reference/control”, a nie sugerować bieżącego mistrza.

## Punkty odrzucone albo niepotwierdzone

- Podejrzenie, że sześć ticków popytu na dzień jest błędem ×4 — odrzucone po inspekcji konfiguracji/silnika.
- Podejrzenie, że struktura na (4,4) blokuje dostęp do szopy — niepotwierdzone i sprzeczne z aktualną kontrolą dostępu.
- Wyniki 64–0 i 68–4 z commita `44526e5` — nadal niezależnie niepotwierdzone, bo commit nie istnieje w osiągalnej historii. Kandydat został zrekonstruowany z replayu i musi przejść nowe testy.
- Pogląd, że wysłane V13/V14 zawierają nową reaktywną architekturę — fałsz.

## Wnioski z porażki V13/V14

- V13: 0–24 przeciw G2 i około 689.5 w pierwszej obserwacji publicznej mimo przewagi nad G4 offline.
- V14: 29–3 przeciw niemal identycznemu G2, ale mały średni zysk materiałowy (+217.6) i słabe zachowanie live według użytkownika.
- Wstrzymujemy promocje z wąskich testów rodzinnych. Kandydat musi pokonać live-strong control, przejść paired seats/seeds, świeży holdout i test zero-crash. Mała modyfikacja rodzica wymaga ponadto istotnego marginesu, nie tylko wysokiego win rate.

## Kolejność dalszych działań

1. Przetestować zrekonstruowaną taśmę GermanJurado1 closed-loop przeciw G2, G4/B21 i w obu seat/tych samych seedach.
2. Uruchomić jej open-loop na pozostałym TOP15 z wyłączeniem źródłowego epizodu; oznaczyć przeciek danych.
3. Walidować pełny adapter reaktywny na prawdziwych obserwacjach i dodać testy sekwencyjnego rynku/kolizji.
4. Dopiero po wyniku wyraźnie lepszym od G4 i konkurencyjnym wobec G2 budować samodzielną kompaktową paczkę oraz nadawać numer V.
5. Rozszerzać scoring o planowanie wielodniowe, zwierzęta i popyt premium; mały model wyboru rozważać dopiero po stabilnym baseline heurystycznym.

## Wyniki niezależnej rekonstrukcji (pierwszy pełny screen)

Closed-loop, wspólne seedy i oba seaty, zero błędów:

- przeciw G2: 16–0 (seedy 41000–41007, średni margines +6472.2) oraz 32–0 (42000–42015, +5530.7), łącznie **48–0**;
- przeciw właściwemu G4 (`agent_v11_subin_g4_29.py`): **16–0**, średni margines **+23946.1**;
- przeciw frozen B21: **16–0**, średni margines **+9954.9**.

Open-loop na sześciu pozostałych replayach GermanJurado1 w TOP15, bez epizodu źródłowego: **5–1**, łączny margines +22555, zero błędów. Jedyna porażka to -5517 przeciw taśmie Mengfei Li. To jest mocny kandydat wyraźnie lepszy od G4 offline i pierwszy, który jednocześnie dominuje G2 w szerzej rozdzielonych seedach. Nadal zachowujemy etykietę „candidate”, ponieważ replaye pochodzą z tej samej rodziny/submission i open-loop nie jest niezależnym dowodem live.

Maszynowe wyniki: `kaggriculture_meta_lab/results/germanjurado-reconstruction-screen-20260910.json` oraz `germanjurado-top15-open-loop-holdout-20260910.json`.

Adapter reaktywny został ponadto uruchomiony na wszystkich **1440 obserwacjach graczy** z epizodu 107218640: zachował dokładny kluczowy schemat akcji oraz liczbę akcji `hands`, bez wyjątku. To test integracji schematu, nie test siły tej polityki.

## Audyt gałęzi `arena/01a087c0-riemann` i dogrywka

Sprawdzono osiągalne commity `8511d13`, `7affdba` i `aa215c5`. „Nowy mistrz” tej gałęzi nie jest inną polityką: po dekodowaniu jego **719/719 akcji jest identyczne** z naszym `champion_tape_germanjurado1.py`. Różni się formatem pakowania (pojedynczy strumień ignorujący seat kontra dwa identyczne strumienie), nie zachowaniem. Niezależne uruchomienie seedów 100–115 przeciw G2 odtworzyło **dokładnie wszystkie 32 wiersze**, wynik 32–0, średnie 103863.46875 / 96602.46875, margines +7261.0.

CI run `34455457302` zakończył się sukcesem po synchronizacji Rust porta z naszą gałęzią. Potwierdza simulator/benchmark, nie wynik mistrza. Nie należy cherry-pickować wcześniejszego stanu CI z `8511d13`: usuwał overlay i parytet LAB oraz robił kosztowny batch 14k bezwarunkowo. Przyjęto natomiast pomysł szybkiego fallbacku `py_reference`: `scripts/fast_static_tournament.py` osiąga około 20 gier/s lokalnie i przez konserwatywny `_source` **odrzuca G2/G4**, zamiast błędnie traktować je jak gołe taśmy. Reaktywne overlaye nadal wymagają pełnego runnera.

Przeskanowano wszystkie siedem epizodów GermanJurado1. Alternatywa z epizodu `107212592` jest ciekawym specjalistą:

- dokładna reprodukcja źródła `[71058, 69945]` na seedzie `1067427524`;
- G2, świeże seedy 44000–44007: 16–0, +10824 wobec +8877 lidera;
- G2, 45000–45015: 32–0, +7814 wobec +6068 lidera;
- paired delta na 48 grach: średnio **+1813.4**, dodatnia w 45/48;
- G4 44000–44007: 16–0, +24942 wobec +23604 lidera;
- wspólny open-loop holdout po wyłączeniu obu epizodów źródłowych: 4–1 i +24048 wobec 4–1 i +20120 lidera.

Nie zastępuje jednak lidera ogólnego:

- świeże 128 seedów × oba seaty przeciw B21: lider 216–40 (+10313), alternatywa 212–44 (+9998.5);
- syntetyczny fresh TOP15 static, 15 rywali × 8 seedów × oba seaty: lider 179–51–10, alternatywa 173–67–0;
- alternatywa przegrywa bezpośrednio z liderem w tym panelu.

Decyzja: zachować `107218640` jako lidera ogólnego, a `107212592` jako specjalistę G2/G4 oraz materiał do przyszłego selektora/ensemble. Proste recovery na PASS przegrało 0–16 z rodzicem (-4772), a G2-style market guard 1–15 (-212); oba eksperymenty odrzucono i nie są promowane. Akcje PASS i rynek tej taśmy są silnie skoordynowane, więc lokalne „oczywiste poprawki” niszczą plan.
