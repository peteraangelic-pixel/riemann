# Audyt aktualnych strategii 3000+ — 2026-09-13

## Dlaczego V3–V27 nie przebiły V2

Numer wersji oznacza kolejną hipotezę laboratoryjną, a nie monotoniczny wzrost
jakości. V2 jest kompletnym, silnie skoordynowanym planem pochodzącym z polityki,
która miała około 2976 punktów. Późniejsze wersje zwykle zmieniały jedną oś tego
planu (rynek, zwierzęta, crossover dni, router albo lokalne naprawy). Testy
wykazały, że jednostki, zakupy i sprzedaż są sprzężone: lokalnie rozsądna zmiana
często odbiera zasób potrzebny późniejszej akcji lub rozstraja trasę wielu
pracowników. Część wcześniejszych zwycięstw była dodatkowo dopasowana do starych
taśm i nie przeniosła się na live.

Najważniejszy błąd kierunku nie polegał na braku liczby eksperymentów, lecz na
próbie ulepszania statycznego harmonogramu fragmentami. Aktualni liderzy nie są
jedną lepszą taśmą. Ich pełne replaye pokazują polityki reagujące na stan.

## Aktualny korpus

Bezpośrednio przeanalizowano kompletne replaye z odświeżonego TOP12. Pięć
najlepszych aktywnych submissionów miało w chwili zebrania wyniki 3208.3, 3069.4,
3057.1, 3047.7 i 3013.2. Dla każdego użyto tylko replayów jego najlepszego
aktywnego submissionu.

## Co rzeczywiście robią liderzy

1. **Reagują niemal w każdej turze.** Dla lidera 3208.3 akcja różniła się między
   czterema replayami w 682 z 719 kroków. Dla strategii 3013.2 było to 717/719.
   To wyklucza wierne odtworzenie przez pojedynczą taśmę lub kilka progów rynku.
2. **Budują skalę wcześnie, ale nie identycznie.** Około dnia 10 mają zwykle
   11–13 pomocników, 2–3 ćwiartki, 49–59 upraw i 10–17 zwierząt. V2 później
   odtwarza podobne makro, lecz według niezmiennego zegara zamiast bieżącej
   dostępności pieniędzy, pól i produktów.
3. **Likwidują produkcję do końca.** W dniu 29 zostaje średnio tylko 2–10 upraw,
   a końcowy niesprzedany magazyn i ekwipunek są bliskie zera. Nie jest to jednak
   samo zwiększenie zleceń SELL — V24/V25 pokazały, że finansowanie całego cyklu
   zależy od wcześniejszego timingu.
4. **Najsilniejsze polityki utrzymują pełne sprzężenie produkcja–logistyka–rynek.**
   Lider 3208.3 kończy z 10 pomocnikami i trzema ćwiartkami, około dnia 10 ma
   średnio 54 uprawy i 16 zwierząt, a jego końcowe nagrody w czterech replayach
   wynoszą 90.7k–126.1k. Strategia 3069.4 stabilnie utrzymuje 12 pomocników,
   około 54 uprawy i 19–20 zwierząt w środku gry oraz zeruje przenoszony towar.
5. **Istnieją co najmniej dwie rodziny ekonomiczne.** Cztery pierwsze strategie
   opierają się głównie na produkcji, WHEAT/FERTILIZER i zwartej sprzedaży.
   Strategia 3013.2 wykonuje dodatkowo masowe zakupy CARROT, TOMATO, STRAWBERRY,
   MELON, EGG, MILK i WOOL, czyli stanowy handel/arbitraż pełnym koszykiem.

## Zmiana planu

Kolejny agent nie będzie kolejnym statycznym splice. V28 jest pierwszą próbą
rekonstrukcji funkcji polityki z wielu pełnych trajektorii lidera 3208.3:

- dla każdej tury zachowuje kilka demonstracji stanu i wynikającej akcji;
- porównuje na żywo pieniądze, skalę farmy, rynek, ceny, magazyn, nasiona,
  pozycje i lokalny stan każdej jednostki;
- wybiera akcję z najbliższego zaobserwowanego stanu tej samej tury;
- zachowuje neutralną nazwę i nie zawiera nazw graczy;
- jest testowany fail-closed przeciw exact-live, aktualnemu TOP12, G2 i V2.

## Wynik V28

Bramka 208 gier zakończyła się bez błędów wykonania, ale odrzuciła reprezentację
pełnej akcji przez najbliższy stan. V28 uzyskał 26–78 (25.0%), podczas gdy V2 na
identycznym panelu uzyskał 62–26–16 (67.3%). Średnia nagroda V28 była niższa o
13 212, a marża o 21 554. Rozbicie V28: TOP12 12/24, G2 4/16, exact-live V2
2/24, exact-live V17 4/24 i bezpośrednio z V2 4/16.

Wniosek jest konkretny: wybór całego wektora akcji z jednej demonstracji nadal
miesza role pracowników i zakupy zależne od innej historii, mimo dopasowania
stanu. Nie należy zwiększać liczby sąsiadów ani stroić wag tego modelu. Następna
rekonstrukcja musi rozdzielić: (1) zadanie każdej jednostki z legalnością lokalną,
(2) globalny docelowy skład farmy oraz (3) sekwencyjny budżet rynku. Demonstracje
3000+ pozostają etykietami dla tych trzech decyzji, a nie gotowymi pełnymi
akcjami do kopiowania.

## Wynik V29

Rozdzielenie demonstracji na legalizowane decyzje pojedynczych jednostek pogorszyło
wynik do 11–93 i średniej nagrody 60 985; V2 na tym samym panelu uzyskał
64–24–16. Przyczyną jest utrata wspólnego przydziału ról i konflikt lokalnie
wybranych ruchów z globalnym rynkiem. V29 został odrzucony bez zgłoszenia.

## V30 i pakiet awaryjny

Szerszy dziewięciotrajektoriowy V30 również nie przeszedł bramki: 25–79 wobec
64–24–16 V2, mimo dodatniego bezpośredniego średniego marginesu +346 przeciw V2.
Załamał się na aktualnym TOP12 (4/24) i G2 (2/16), więc nie wolno go zgłaszać.

Na wyraźną prośbę o artefakt gotowy technicznie do Kaggle przygotowano neutralny
ZIP `packages/stable_market_v23.zip` z `main.py` w katalogu głównym. Jest to
wcześniejszy V23: jedyny eksperymentalny wariant, który nie zmienił wyników exact-live
i miał małą dodatnią zmianę w pierwotnym TOP12. Nie jest to jednak potwierdzony
następca V2 ani kandydat z wiarygodną ścieżką 3000+; pakiet nie został automatycznie
wysłany i nie powinien zastępować aktywnego V2 bez świadomej decyzji użytkownika.

## Odświeżenie TOP50 z 4 października 2026

Nowy korpus zmienia próg strukturalny: aktualne wyniki najlepszych aktywnych
zgłoszeń mieszczą się między 3132.7 a 2827.8, a dwaj liderzy nadal przekraczają
3000. Około dnia 10 polityki z czołówki mają już zwykle 12 pomocników, wszystkie
cztery ćwiartki, 68–73 upraw i 20–22 zwierzęta. Najsilniejsze kończą na około
116–126 tys. nagrody. Trzy ćwiartki i około 54 upraw V2 odpowiadają obecnie raczej
dolnej granicy TOP12 niż architekturze lidera.

Dlatego następny ekran obejmuje wszystkie 108 nowych pełnych przebiegów jako
potencjalnych rodziców strukturalnych, ale sprawdza je na niezależnych seedach i
bramkuje przeciw całemu nowemu korpusowi, exact-live, G2 oraz V2. Szczegółowy,
wersjonowany plan i kryteria fail-closed zapisano w
`kaggriculture_meta_lab/docs/V31_REFRESHED_TOP12_PLAN_20261004.md`. Wynik tego
ekranu nie zostanie zgłoszony, jeżeli nie pokona jawnej kontroli V2; replay ma
wyznaczyć spójną architekturę, a nie wrócić do odrzuconego nearest-state imitation.

Ekrany V31–V33 potwierdziły ten warunek negatywnie. Żaden ze 108 rodziców nie
przeszedł bramki V31. V32 wykonał 101 920 gier nakładek rynku, a V33 76 368 gier
splice'ów pełnej akcji, jednostek i rynku; w obu przypadkach nie było żadnego
kwalifikującego się wariantu. Najlepsza statyczna taśma lokalna osiągnęła nawet
183–113, ale pochodziła ze submissionu o wyniku 2827.9 i traciła panel nowego
TOP12 120 do 132 wygranych V2. To lokalny kontrprzykład wobec selekcji samym
agregatem, nie kandydat 3000+. V31–V33 pozostają odrzucone bez zgłoszenia.
