# Audyt aktualnego LAB-u i kierunku poprawy agenta

**Data: 2026-09-07. Nic nie zostało wysłane do konkursu. Nie promowano nowego agenta.**

## 1. Jaką wersję sprawdziłem

- Główny projekt użytkownika: `arena/01a0712c-riemann`.
- Kod LAB-u: commit `f2c085f06df0e00997e640de66f3c0b882a1bbca`.
- Później odczytane wyniki testu miejsc i ledger:
  `3dd47f25fa6cd2a2523a427b0c612b171121ed44`.
- Źródła zostały pobrane tylko do izolowanej kopii; nie przełączałem ani nie
  nadpisywałem wskazanej gałęzi. Pełne taśmy B21 w aktualnym LAB-ie są takie
  same jak w dostarczonym przykładzie użytym do testów portu Rust.
- Przeczytałem m.in. aktualny README LAB-u, `CURRENT_20260907.md`,
  `V10_GOLDEN_FINDINGS.md`, `V10_B21_ROADMAP.md`, analizę odzyskiwania wygranych,
  wyniki finalistów i kod evaluatorów. Nie traktuję historycznego V8-fertilizer
  jako obecnego championa.

## 2. Rzeczywisty odczyt Kaggle

Odczyt z **7 września, 19:21:50 czasu polskiego (17:21:50 UTC)**:

| Pozycja | Wartość |
|---|---:|
| Zespół | Lauresowe 3D |
| Miejsce / liczba zespołów w pobranej tabeli | **804 / 8064** |
| Publiczny wynik zespołu | **2113,0** |
| B21/S16, submission `56071535` | **2113,0** |
| V8 Aastik, submission `56054137` | **2215,3** |
| V8 hybrid, submission `56054139` | **2095,0** |
| Lider w tej chwili: ymg_aq | **2925,9** |

To migawka, nie historyczne maksimum ani prognoza końcowego rankingu.
Oceny różnych submisji nie zastępują kontrolowanego testu na tych samych
przeciwnikach. Nie sprawdzałem ani nie zmieniałem wyboru aktywnych submisji.

Odczyt wykonał [read-only workflow](https://github.com/peteraangelic-pixel/riemann/actions/runs/34147276976),
korzystając z istniejącego sekretu repozytorium `KAGGLE_API_TOKEN`. Nie używał
API uploadu ani wyboru agentów. Tokenu podanego w rozmowie nie przepisano do
kodu, plików ani historii Gita; należy go unieważnić i zastąpić sekretem
ustawionym poza czatem.

## 3. Dlaczego 93–94% lokalnych wygranych nie przełożyło się na ranking

Aktualne wyniki samego projektu już pokazują pułapkę porównywania bliskich
klonów:

| Polityka | Wygrane TOP49 / 490 | Średnia przewaga gotówki |
|---|---:|---:|
| B21/S16 — kontrola | **184** | **+835** |
| B20/S15 | 184 | +628 |
| B19/S14 | 184 | −287 |
| B18/S13 — zwycięzca lustrzanego finału | **178** | **−1467** |

B18 dominował nad B21 i bliskimi wariantami, ale stracił sześć wygranych na
TOP49. Nie jest lepszym generalistą. Dodatkowo zakończony podczas tego audytu
test B20 tylko na P0 lub P1 **również nie zmienił ani jednego zwycięskiego
rekordu**: wszystkie wersje pozostały przy 184/490 i pogorszyły średnią.
Nie ma powodu ponawiać tego samego symetrycznego ani bezwarunkowego testu miejsc.

Drugi problem to aktualność populacji. **Po nazwach tylko 5 z aktualnego TOP10**
znajduje się w dotychczasowym wykazie TOP49: ymg_aq, Mengfei Li, get some fries,
mandgeee i Suliman Tadros. Nie znalazłem po nazwie 3정훈, SpaTaro, Atakan Aldemir,
THUNDER THUNDER i binghua. Zmiany nazw są możliwe — do rzetelnej identyfikacji
potrzebne są stabilne TeamId, nie sama nazwa. Nie można tworzyć „TOP10” przez
wzięcie pierwszych dziesięciu alfabetycznie posortowanych rekordów starego pliku.

## 4. Trzy potwierdzone problemy evaluatora LAB-u

### A. `corpus.score_episode` używał seeda 0 zamiast seeda nagrania

W oficjalnych replayach `configuration.seed` jest wyczyszczone do `null`.
Prawdziwy seed jest w `info.seed`. Kod LAB-u używał:

```python
seed = replay.get("configuration", {}).get("seed") or 0
```

To zmienia chwasty, losowania sklepów i ceny. Powtórzyłem osiem dołączonych
replayów samymi ich oryginalnymi akcjami:

- z `info.seed`: **8/8 dokładnych odtworzeń gotówki obu graczy**;
- z seedem 0: **8/8 innych wyników**.

Przykład `105788063`:

| Uruchomienie | Gotówka gracza 0 | Gotówka gracza 1 |
|---|---:|---:|
| Oryginalny zapis / poprawny seed | 26 308 | 98 306 |
| Te same akcje, błędny seed 0 | 27 326 | 21 386 |

W tym przykładzie błąd **odwraca zwycięzcę**. Takie dane nie są wiernym
odtworzeniem nagrania i nie mogą stanowić bramki regresji replayowej.

### B. Specyfikacja `tape:` opóźniała przeciwnika o turę

`agents._make_tape` zwracał `tape[step]`, choć replay zawiera na indeksie 0 stan
początkowy, a akcję kroku N na indeksie N+1. Osobna funkcja
`corpus.tape_agent` miała już poprawne `step + 1`; dwa loadery się rozjechały.
W dołączonym przykładzie `tape:` zwracał w pierwszej turze pusty rynek zamiast
czterech HIRE i zakupów nasion.

### C. Błędy agentów mogły przechodzić jako normalne wyniki

Silnik Kaggle potrafi zakończyć epizod statusem `DONE` również po wcześniejszym
`ERROR`. Dotychczasowy test wręcz wymagał `error is None` po wyjątku agenta.
Taki mecz może wejść do W/L/T zamiast do licznika błędów.

Samo sprawdzanie historii końcowych stanów nie wystarcza: **wyjątek w ostatniej
turze może zostać nadpisany na DONE jeszcze przed zapisaniem tego stanu**.
Potwierdziłem to na rzeczywistym frameworku. Poprawka obserwuje status wejściowy
przed wywołaniem niezmienionego interpretera, sprawdza historię i prawidłowość
końcowych wyników. Nie zmienia reguł gry ani RNG.

**Zakres:** osobny `kaggriculture/research/screen_top49_all.py` poprawnie używa
`info.seed` i akcji `step + 1`. Błędy A/B nie unieważniają jego tabel TOP49.
Natomiast przed testowaniem nowych polityk warto także w tym skrypcie stosować
pełną kontrolę awarii — obecnie on również sprowadza brak wyniku do zera.

## 5. Gotowa poprawka, bez nadpisywania równoległej pracy

Plik: [`../patches/lab-replay-correctness.patch`](../patches/lab-replay-correctness.patch).

Zawiera zmiany w `agents.py`, `corpus.py`, `engine.py`, `tournament.py`, poprawę
sprzecznego testu błędnego agenta oraz nowy zestaw regresji. Dodatkowo odrzuca
niepoprawny numer miejsca w `tape:` zamiast tworzyć cichego przeciwnika PASS.

**Weryfikacja: 26 testów przeszło.** Testowano rzeczywisty, przypięty core
Kaggle 1.32.7, w tym wyjątek dokładnie w ostatniej turze. Patch zastosowany do
świeżej kopii źródeł odtworzył wszystkie sześć sprawdzonych plików bajtowo.
Nie edytowano Pythonowych reguł symulatora.

Patch przygotowano względem `f2c085f...`. Przed użyciem na nowszym HEAD należy
sprawdzić kontekst, zwłaszcza jeśli inna sesja już zmieniała te pliki.
W checkout zawierającym aktualny LAB, po skopiowaniu patcha:

```bash
git apply --check kaggriculture_meta_lab/patches/lab-replay-correctness.patch
git apply kaggriculture_meta_lab/patches/lab-replay-correctness.patch
cd kaggriculture_meta_lab
python -m pytest tests/test_agents_corpus.py tests/test_engine_tournament.py tests/test_replay_regressions.py -q
```

## 6. Wykonany mały eksperyment końcówki — wynik negatywny

Sprawdziłem trzy najbliższe porażki B21: Kenneth Alonso `106178365`, Mengfei Li
`106180186`, elmo `106180027`. Oba miejsca. Kontrola dokładnie odtworzyła
wyniki zapisane w głównym TOP49 raporcie, zanim oceniono jakiekolwiek mutacje.

- Cztery warianty końcówki (pełniejsza sprzedaż, dodatkowe DROP, opróżnienie
  szopy turę wcześniej, powrót z odległości jednej kratki): **bez zmiany wyniku**.
- Trzy krótkie kontrolery zbioru i powrotu do szopy: **brak odzyskanych wygranych,
  niewielka regresja**.

| Przeciwnik | Kontrola: przewaga | Kontroler 4 tury | 6 tur | 8 tur |
|---|---:|---:|---:|---:|
| Kenneth Alonso | −81 | −82 | −117 | −119 |
| Mengfei Li | −280 | −283 | −299 | −304 |
| elmo | −412 | −415 | −454 | −453 |

To **48 meczów odkrywczych**, nie niezależny holdout ani ocena całej ligi.
Nie promuję żadnego wariantu. B21 już ma końcową sprzedaż w kroku 718;
samo „sprzedaj wszystko na końcu” nie rozwiązuje tych trzech porażek.
Nie dowodzi to, że wszystkie możliwe zmiany końcówki są bezwartościowe.

Kod badawczy: `terminal_salvage.py`; siedem testów logiki przeszło, ale nie jest
to dowód większej siły. Odtworzenie screeningu:

```bash
python kaggriculture_meta_lab/research/probe_terminal.py \
  --source-root /sciezka/do/glownego/checkout \
  --source-ref f2c085f06df0e00997e640de66f3c0b882a1bbca
```

Dokładne liczby, hashe replayów i ranking:
[`AGENT_AUDIT_20260907.json`](AGENT_AUDIT_20260907.json).

## 7. Sensowna kolejność dalszych prac

1. **Naprawić wiarygodność LAB-u** i potwierdzić odtwarzanie nagrań. Nie mieszać
   historycznych V7/fertilizer wyników z obecnymi bramkami B21.
2. **Zamrozić świeży manifest TOP10/20/30** według rankingu, TeamId, submisji,
   dat i identyfikatorów epizodów. Zachować kierunek C10 → C20 → C30 z aktualnego
   planu, bez dodawania treningu TOP31–49.
3. **Rozdzielić odkrywanie i walidację po graczach oraz epizodach.** Dwa rekordy
   uczestników tego samego meczu są legalnymi różnymi taśmami, ale nie dwiema
   niezależnymi obserwacjami do oceny pewności ani osobnymi stronami train/test.
4. **Wybrać jedną zmianę produkcji/routingu**, nie następną drabinkę lustrzanych
   otwarć. Na podstawie aktualnego ledgeru: dostępność pracy, realny koszt
   karmienia/CARE, zbiór przed końcem sezonu, obsługa premiów przy presji podaży
   konkurenta. Dodatkowe zwierzęta bez nowego planu obsługi nie są rozwiązaniem.
5. **Podłączać Rust z właściwym kontraktem.** Jego wcześniejsza zgodność została
   zmierzona (574 mecze / 84 seedy), ale nie jest jeszcze podłączony do tego LAB-u.
   B21 przycina listę pomocników, natomiast główny opponent-replay jej nie przycina.
   Globalne `--trim-hands` dla obu stron nie jest automatycznie równoważnym
   adapterem tego benchmarku. Potrzebna jest kontrola per agent i ponowny test
   zgodności. Polityki reaktywne nadal wymagają prawdziwego closed-loop, nie
   zamrożenia jednej taśmy na wszystkie mecze.
6. **Promować wyłącznie potwierdzony transfer**, z osobnym raportem nowych
   wygranych, utraconych wygranych, awarii i wyników na świeżych live replayach.
   Publikacja na Kaggle wymaga osobnego potwierdzenia użytkownika.

Na ten moment mamy lepiej zdiagnozowany problem i przetestowaną poprawkę
narzędzi, **nie nowego agenta z udowodnioną przewagą ponad 2300**.
