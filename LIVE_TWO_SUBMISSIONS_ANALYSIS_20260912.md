# Audyt dwóch zgłoszeń live i nowi kandydaci — 2026-09-12

## Dane

Pobrano przez oficjalny Kaggle CLI po 12 najnowszych kompletnych replayów zgłoszeń:

- V17 `56183278`, aktualny publicScore **2042.3**;
- V2 `56142365`, aktualny publicScore **2823.6**.

Każdy replay ma 720 stanów, status końcowy `DONE` i dodatnią nagrodę. Nie ma awarii agenta. Szczegóły są w `kaggriculture_meta_lab/results/live-v17-v2-replay-analysis-20260912.json`.

## Wyniki rzeczywistych meczów

| Zgłoszenie | W–L | Śr. nagroda | Mediana | Śr. marża |
|---|---:|---:|---:|---:|
| V17 | 6–6 | 82 649 | 76 366 | −2 487 |
| V2 | 6–6 | 92 248 | 91 134 | −5 220 |

Zbiory przeciwników i daty są różne, więc nie jest to bezpośredni head-to-head. V2 grał wcześniej z mocniejszym rankingowo koszykiem. Ratingu nie wolno wyjaśniać samym W–L.

## Najważniejsze mechanizmy

1. **Router V17 nie uruchomił się ani razu w 12 meczach.** Warunek otwarcia oparty na liczbie rąk i zapasie pszenicy nie występuje w aktualnym koszyku. V17 w praktyce był statycznym V16.
2. Oba agenty kończą każdy mecz z kompletnym stadem około **8 krów, 6 owiec i 3 gęsi**. Cykl budowa–rozmieszczenie–karmienie–opieka–nawóz działa; problem nie jest awarią zwierząt.
3. Akcje jednostek są niemal identyczne. Zasadnicza różnica dotyczy rynku:
   - V17: średnio **287 SELL/mecz**;
   - V2: średnio **465 SELL/mecz**.
   V17 wykonuje około 178 sprzedaży mniej i zarabia średnio o około 9,6 tys. mniej.
4. V17 ma bardzo wąskie zwycięstwa (średnio +2,0 tys.) i znacznie cięższe porażki (średnio −7,0 tys.; minimum −20,3 tys.). Brakuje przewagi ekonomicznej, nie legalności.
5. V2 ma większą średnią ekonomię, lecz także ciężkie porażki. Nadal jest najlepszym potwierdzonym zgłoszeniem live, ale nie jest rozwiązaniem poziomu 3000+.

## Nowi agenci

### V18

V2 z zachowaną pełną likwidacją oraz dziewięcioma późnymi zmianami WHEAT→CARROT z V16. Wynik na 24 dokładnych przeciwnikach live, obie strony:

- V18: 30–18, nagroda 93 943, marża +100;
- V2: **34–14**, nagroda **94 762**, marża **+939**.

V18 odrzucony.

### V19–V22

Cztery kompletne, niesklejane harmonogramy z najnowszego TOP12 (źródłowe ratingi 2997.6–3208.3). Counterfactual na dokładnych przeciwnikach live:

| Agent | W–L | Śr. nagroda | Śr. marża |
|---|---:|---:|---:|
| V19 | 4–44 | 88 981 | −10 621 |
| V20 | 15–33 | 86 396 | −11 796 |
| V21 | 22–26 | 95 231 | −2 408 |
| V22 | 8–40 | 77 163 | −21 593 |
| **V2** | **34–14** | 94 762 | **+939** |

Sam fakt, że replay pochodzi od źródła 3000+, nie czyni z niego przenośnego open-loop agenta. Wszystkie cztery odrzucono.

### V23 — duża populacja rynku

Przeszukano deterministycznie 256 mutacji V2: duplikowanie lub skalowanie sprzedaży według dni i produktów. Trening użył połowy dokładnych replayów live; holdout drugiej połowy oraz całego najnowszego TOP12.

Zwycięzca skaluje sprzedaż pszenicy w dniach 12, 14–16, 19, 22–23, 25–26 i 29.

| Panel holdout | V2 | V23 |
|---|---:|---:|
| aktualny TOP12 | 156 zwycięstw | **160** |
| live V2 cohort | 6 | 6 |
| live V17 cohort | 10 | 10 |

V23 zwiększa średnią nagrodę aktualnego TOP12 o 924 i marżę o 1106, ale nie zmienia żadnego wyniku na live holdout. Jest legalnym nowym kandydatem laboratoryjnym, lecz poprawa jest zbyt mała, by automatycznie zajmować slot Kaggle.

## Wniosek

Nie wysyłać V18–V22. V23 zachować jako punkt startowy, ale nie przedstawiać jako przełomu. Następna wersja musi zwiększyć skalę ekonomii lub dynamicznie zarządzać sprzedażą na podstawie rzeczywistego stanu magazynu/cen; kolejny statyczny crossover nie wystarczy.
