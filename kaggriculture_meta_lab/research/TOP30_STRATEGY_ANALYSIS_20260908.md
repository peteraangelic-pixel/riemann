# TOP30 — pierwsza analiza strategii

Źródło: `TOP30.7z` z gałęzi `arena/01a0712c-riemann`, commit `1ebeefd`.
Archiwum zawiera 30 zespołów, po 5 replayów na zespół oraz 180 gotowych
plików analitycznych w `per_replay/` (30 manifestów + 150 replayów).
Surowe replaye nie zostały dodane do repozytorium.

## Ranking źródłowy

| Pozycja | Zespół | Public score |
|---:|---|---:|
| 1 | SpaTaro | 2933.2 |
| 2 | Otter Vibe | 2922.5 |
| 3 | binghua | 2881.9 |
| 4 | Mengfei Li | 2878.7 |
| 5 | Matthew Huang | 2871.3 |
| 6 | Ad Space Available | 2856.3 |
| 7 | Tarang222 | 2834.9 |
| 8 | Suliman Tadros | 2831.6 |
| 9 | carbonapi | 2830.3 |
| 10 | Subin An | 2827.5 |

## Pierwsze sygnały strategiczne

Analiza `per_replay` jest agregatem tolerancyjnym i nie zawsze odzyskuje
ilości/produty z natywnego formatu, dlatego poniższe wartości są hipotezami,
a nie jeszcze gotowymi parametrami agenta.

### 1. TOP30 nie jest jedną rodziną

Najwyżej sklasyfikowane zespoły dzielą się przynajmniej na różne profile:

- **SpaTaro** — bardzo wysoki turnover: średnio około 523 buy i 308 sell na
  gracza; pierwsza sprzedaż około t11.
- **Otter Vibe** — niski buy, wyraźnie późniejsza pierwsza sprzedaż około t37;
  profil delayed-sale / oszczędzania kapitału.
- **binghua** — pośredni turnover i pierwsza sprzedaż około t32.
- **Tarang222** i **carbonapi** — również pierwsza sprzedaż około t31.
- **THUNDER THUNDER** — pierwsza sprzedaż około t28.
- **Mengfei Li**, **Matthew Huang**, **Ad Space Available** i wiele dalszych
  zespołów sprzedaje już około t1–t2, ale różnią się obrotem i liczbą zakupów.

To potwierdza, że nie należy stroić tylko jednej osi `fert_scale` albo
kopiować jednej taśmy. W TOP30 współistnieją co najmniej strategie
high-turnover oraz delayed-sale.

### 2. Opóźniona sprzedaż jest realnym sygnałem w aktualnym TOP30

Wśród wysokich pozycji występuje kilka niezależnych profili z pierwszą
sprzedażą w okolicach t28–t37. To wzmacnia hipotezę z wcześniejszego TOP49,
ale nie dowodzi, że sama zamiana B21 na opóźnioną sprzedaż będzie lepsza.

Wnioski dla eksperymentu:

- nie ruszać całej taśmy naraz;
- zachować B21 jako fallback;
- testować opóźnienie sprzedaży jako warunkową gałąź kroku 1;
- porównać je z wariantem wysokiego turnoveru, a nie tylko z B21.

### 3. Wysoki score nie oznacza jednego poziomu aktywności

SpaTaro ma skrajnie wysoki buy count, ale drugi w rankingu Otter Vibe ma
znacznie mniej zakupów i dużo późniejszą sprzedaż. Zatem prosty cel typu
„więcej buy”, „więcej nawozu” albo „więcej hire” jest niewłaściwy.

Potrzebujemy parametrów warunkowych:

- kiedy sprzedawać po pierwszym ruchu rynku;
- kiedy utrzymywać gotówkę;
- kiedy wejść w wysoką rotację;
- kiedy przełączyć się z opóźnionej sprzedaży na produkcję.

### 4. Warto analizować mechanizm, nie nazwę

Nazwy z TOP30 nie powinny pojawiać się w kodzie agenta ani w regułach
promocji. W następnym kroku grupujemy replaye po fingerprintach:

- first sell bucket: t1–2, t10–15, t25–32, t33+;
- buy/sell ratio;
- action turnover;
- timing HIRE i fertilizer;
- końcowa aktywność sprzedażowa.

Dopiero reprezentant klastra może stać się kandydatem do rekonstrukcji.

## Zmiana planu eksperymentalnego

`v12_timing_endgame` pozostaje właściwy jako pierwszy test struktury B21.
Po nim należy dodać osobny tor `v13_top30_policy_families`:

1. B21 jako exact fallback;
2. wariant delayed-sale około t28–37;
3. wariant high-turnover inspirowany profilem SpaTaro;
4. wariant pośredni około t31–32;
5. warunkowy krok 1 oparty o cenę/zapas po pierwszym ruchu;
6. każdy wariant testowany na obu seatów i świeżym holdoucie.

Nie należy kopiować surowych trajektorii open-loop. TOP30 służy do odkrycia
rodzin strategii; przewagę potwierdzamy dopiero w closed-loop i na nowych
seedach.

## Ograniczenie obecnej analizy

W gotowych plikach `per_replay` część pól ilościowych jest oznaczona jako
`UNKNOWN`, mimo że parser poprawnie odzyskuje liczbę akcji i timing. Dlatego
obecny raport jest dobry do wyboru rodzin i timingów, ale nie do ustalenia
konkretnych ilości nawozu/zwierząt. Do tego potrzebny będzie izolowany parser
natywnego replay body dla wybranych replayów TOP30.
