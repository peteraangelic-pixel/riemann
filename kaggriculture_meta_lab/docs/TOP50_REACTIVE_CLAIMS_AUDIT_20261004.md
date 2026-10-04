# Audyt tez o reaktywności nowego TOP12/TOP50

Źródło: `TOP50.7z`, kompletne replaye najlepszego aktywnego submissionu każdej
z 12 rang. Liczniki poniżej pochodzą bezpośrednio z akcji i stanów, nie z nazw
ani opisu agenta.

## Co potwierdzają replaye

Dla lidera 3132.7 cztery dostępne replaye najlepszego submissionu obejmują po
dwa występy na P0 i P1. Do końca dnia 10 lider ma zawsze 12 hands i cztery
ćwiartki, średnio 70.8 upraw oraz 21.5 zwierzęcia. Skład zwierząt nie jest stałym
`COW x4 / SHEEP x5`: przebiegi dnia 10 kończą m.in. jako 14/3/6, 14/3/5,
8/3/7 i 7/10/6 dla COW/SHEEP/GOOSE. To silny sygnał reakcji na rynek i
przeciwnika.

W czterech replayach lider wykonuje 1578 FEED, 1449 CARE, 1906
COLLECT_FERTILIZER i 967 FERTILIZE. Wystawia 363 zlecenia sprzedaży
FERTILIZER. Pełny cykl zwierzęcy i nawóz jako osobny strumień przychodu są więc
bezsporne.

Około dnia 10 lider ma średnio 31 STRAWBERRY, 12.8 MELON, 12 WHEAT i 1.8
TOMATO. Wszystkie pięć upraw występuje w akcjach sadzenia. TOMATO i STRAWBERRY
są ongoing według reguł silnika; top wykorzystuje ich kolejne zbiory bez
ponownego sadzenia po każdym zbiorze.

W czterech replayach lider nadal ma 40 operacji PLANT w dniach 27–28 łącznie,
ale zero w dniu 29. Prawidłowa teza brzmi zatem: sadzenie jest mocno wygaszane,
a dzień 29 jest likwidacyjny; nie jest prawdą, że absolutnie nie ma sadzenia od
dnia 27.

## Co nie zostało potwierdzone

Wszystkie replaye najlepszych submissionów zaczynają z dokładnie 3000 cash.
Korpus nie testuje różnych starting cash, więc twierdzenie, że otwarcie zależy
od starting cash, jest hipotezą, nie obserwacją. Polityka oczywiście reaguje na
cash pozostały po zakupach i sprzedaży.

Dla lidera sygnatura zleceń rynku pierwszego dnia jest identyczna we wszystkich
czterech replayach, mimo podziału 2/2 między P0 i P1. Dalsze trajektorie P0 i P1
są różne, lecz wynika to także z różnych stanów i przeciwników. Replaye dowodzą
state-awareness; nie dowodzą osobnej, twardo zakodowanej polityki otwarcia dla
każdego seat. Nowy agent powinien poprawnie obsługiwać oba seaty przez `player`
i własny stan, ale nie należy wymyślać seatowego rozgałęzienia bez wyniku
ablacji.

## Pokrycie przez nasze wersje

- V2/V16: mocny control, ale ta sama statyczna trajektoria na obu seatach;
  brak pełnej reaktywności i architektura mniejsza od liderów.
- V7: dobry historyczny control, lecz nie realizuje pełnej nowej gospodarki
  czteroćwiartkowej.
- V11 reactive: ma stanowy routing, FEED/CARE/COLLECT_FERTILIZER, sprzedaż
  nawozu i likwidację, ale domyślnie wyłącza SE, ma 14 zwierząt, zero
  strawberries i nie obsługuje tomato.
- V12–V15: zawierają części premium/animal repair, ale wcześniejsze bramki
  wykazały, że nie składają pełnego rentownego cyklu. V15 naprawia cykl tylko,
  gdy zaplanowana akcja jednostki jest PASS.
- V34: pierwszy jawny prototyp łączący cztery ćwiartki, tomato/strawberry,
  mieszane 18–20 zwierząt, pełny lifecycle, nawóz i stop sadzenia. Nie jest
  kandydatem do zgłoszenia: szeroki ekran 64 profili na seedzie 230100 dał
  0/128 zwycięstw przeciw V2. Najlepszy profil miał średnią nagrodę 61 400.5 i
  marżę -114 072. Wynik zapisano w
  `results/v34-reactive-population-seed230100-20261004.json`.

## Decyzja

Sugestia zewnętrzna trafnie wskazuje pełny cykl zwierząt, nawóz, uprawy ongoing
i likwidację, lecz myli lub nadmiernie upraszcza seat-awareness, starting cash
i docelowy skład stada. Samo włączenie tych cech w starym routerze V11 nie
wystarcza. Następna architektura musi przede wszystkim poprawić wspólny
przydział tras i kolejność finansowania; strojenie 32 liczb słabego routera nie
zbliża go do V2.
