# ARC-AGI-3 — plan do 30.09.2026

**Status:** aktywny

**Horyzont:** 3–30 września 2026

**Priorytet projektu:** ARC-AGI-3 / ARC Prize 2026

## Decyzja kierunkowa

Do **30.09.2026** cała dostępna moc obliczeniowa GitHub Actions oraz czas
projektowy są przeznaczone na ARC-AGI-3. Wątek Hall / census / gadget jest
**wstrzymany**: nie uruchamiamy kolejnych skanów ani harmonogramu cyklicznego.
Istniejące wyniki pozostają jedynie archiwum.

## Cel

Przygotować powtarzalny, mierzalny pipeline agenta ARC-AGI-3, gotowy do
iteracji i zgłoszenia przed kamieniem milowym 30 września 2026 r.

## Plan działania

1. **Dostęp i dane (natychmiast)**
   - zachować lokalną konfigurację Kaggle poza Git;
   - potwierdzić dostęp do właściwych danych i regulaminu konkursu;
   - zapisać deterministyczny sposób pobrania danych oraz wersje zależności.

2. **Szkielet rozwiązania**
   - utworzyć izolowany moduł ARC (loader, reprezentacja stanu gry, executor
     akcji, logowanie trajektorii);
   - dodać mały zestaw smoke-testów na publicznych przykładach;
   - mierzyć wynik per gra, per poziom i koszt/limit wywołań modelu.

3. **Pętla agenta**
   - zbudować bazowy agent: obserwacja → hipoteza → akcja → weryfikacja;
   - zapisywać pełne trajektorie, błędy i seed, aby eksperyment był
     odtwarzalny;
   - priorytetowo usuwać błędy wykonania i błędy interakcji przed strojem
     strategii.

4. **Eksperymenty i selekcja**
   - prowadzić krótkie, ograniczone budżetowo eksperymenty w GitHub Actions;
   - porównywać warianty na stałym publicznym zestawie walidacyjnym;
   - promować tylko warianty z mierzalną poprawą i odtwarzalnym wynikiem.

5. **Finalizacja do 30.09**
   - zamrozić najlepszą konfigurację, zależności i instrukcję uruchomienia;
   - wykonać end-to-end dry run w środowisku zbliżonym do zgłoszenia;
   - sprawdzić wymagania regulaminowe, format zgłoszenia i limity kosztów;
   - zapisać wynik końcowy oraz listę ryzyk/usprawnień po terminie.

## Zasady wykorzystania GitHub Actions

- Brak automatycznego crona dla wcześniejszych obliczeń matematycznych.
- Do czasu dodania workflow ARC nie uruchamiać ręcznie zadań Hall, census ani
  gadget.
- Nowe runy Actions mają mieć nazwę, budżet czasu i artefakty odnoszące się do
  ARC-AGI-3.
- Sekrety i pliki poświadczeń pozostają lokalne lub w GitHub Secrets — nigdy w
  commicie, logach ani artefaktach.

## Stan implementacji — 03.09.2026

- Dodano katalog `arc_agi3/` z deterministycznym baseline'em
  `novelty-explorer-v1`: legalne akcje, analiza zmian ramek, ranking kliknięć
  według komponentów i mały graf stanów zamiast losowych akcji.
- Dodano offline'owe testy regresji oraz generator notebooka Kaggle z
  wyłączonym internetem. Domyślnie wybiera CPU; GPU jest świadomą opcją.
- Dodano ręcznie uruchamiany workflow GitHub Actions do testów ARC. Nie ma on
  crona, nie zawiera poświadczeń i nie wykonuje zgłoszenia Kaggle.
- Lokalny sandbox nie łączy się obecnie TLS z ARC/Kaggle, dlatego rzeczywisty
  smoke test publicznych gier jest przeznaczony do ręcznego runu GitHub Actions
  lub środowiska z dostępem do ARC. Nie wykonano zgłoszenia konkursowego.

## Najbliższe bramki

1. Potwierdzić, że konto Kaggle dołączyło do konkursu i zaakceptowało regulamin.
2. Uruchomić publiczny smoke test na `ls20` i `vc33`, obejrzeć recordingi i
   ustalić pierwsze powtarzalne mechaniki.
3. Uzyskać lokalny `ARC_API_KEY` (poza Git) dla pełnego zestawu publicznych
   środowisk oraz zbudować stały zestaw walidacyjny.
4. Dopiero po walidacji pushować notebook do Kaggle; oficjalne zgłoszenie
   leaderboardowe pozostaje osobną, świadomą decyzją (limit: jedno dziennie).

## Kryterium gotowości

Przed 30.09.2026 repozytorium ma zawierać odtwarzalny pipeline ARC-AGI-3,
instrukcję uruchomienia, testy smoke oraz udokumentowany wynik walidacyjny.
