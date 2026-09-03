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

## Kryterium gotowości

Przed 30.09.2026 repozytorium ma zawierać odtwarzalny pipeline ARC-AGI-3,
instrukcję uruchomienia, testy smoke oraz udokumentowany wynik walidacyjny.
