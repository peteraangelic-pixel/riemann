# V31: odświeżony TOP12 i poszukiwanie rodzica strukturalnego

## Źródło

Korpus `TOP50.7z` (SHA-256 `161f53d7d26c76a4a66511f0e73edf08ea6548097d998524c4f0d6eb4f414ec6`)
zawiera 12 zespołów i po dziewięć kompletnych replayów. Wyniki najlepszych
aktywnych zgłoszeń to: 3132.7, 3103.5, 2987.2, 2950.4, 2944.7, 2916.7, 2907.9,
2866.2, 2855.5, 2849.9, 2843.1 i 2827.8.

## Nowy próg architektury

Bezpośredni odczyt stanów z kompletnych replayów wykazał konwergencję znacznie
większą niż w poprzednim korpusie. Około dnia 10 najlepsi mają 12 pomocników,
wszystkie cztery ćwiartki, około 68–73 upraw i 20–22 zwierzęta. Około dnia 15
mają 24–29 tys. gotówki, a najmocniejsze przebiegi kończą na 116–126 tys.
Wariant pozostający przy trzech ćwiartkach zajmuje ostatnie miejsce zestawu z
wynikiem 2827.8, bardzo zbliżonym do poziomu V2.

Wniosek: dostrojenie rynku V2 nie wystarczy. Następca potrzebuje spójnej,
legalnej obsługi czwartej ćwiartki, około 12 pracowników oraz produktywnej skali
około 70 upraw i 20–23 zwierząt. Replaye służą do ustalenia kamieni milowych i
rodzica strukturalnego, nie do kopiowania akcji przez najbliższego sąsiada.

## Eksperyment V31

`search_v31_new_top12_structural.py` wykonuje fail-closed dwuetapowy ekran w
porcie Rust:

1. każdy ze 108 pełnych przebiegów jest kandydatem na rodzica strukturalnego;
2. etap treningowy mierzy transfer na niezależnych seedach przeciw najlepszym
   aktywnym źródłom wszystkich 12 rang;
3. 12 finalistów jest ocenianych na całym nowym korpusie z oryginalnymi seedami,
   exact-live 56142365 i 56183278 oraz przeciw V2 i G2;
4. V2 jest jawnie dodaną kontrolą i staje się wynikiem domyślnym, jeżeli żaden
   rodzic nie przejdzie bramki;
5. kandydat musi pokonać V2 globalnie, nie pogorszyć exact-live, poprawić panel
   nowego TOP12 o co najmniej cztery wygrane i nie załamać się przeciw G2.

To jest ekran diagnostyczny i selekcja materiału do spójnego planera. Sam fakt,
że statyczny przebieg ma farmę 3000+, nie będzie podstawą zgłoszenia do Kaggle.
Jeżeli bramka nie znajdzie transferowalnego rodzica, następnym krokiem pozostaje
stanowy joint planner realizujący powyższe kamienie milowe na bazie bezpiecznego
conveyora V2.

## Wyniki V31–V33

V31 wykonał 5 184 gry treningowe i 4 144 gry holdout. Żaden ze 108 przebiegów
nie przeszedł bramki; kontrola V2 wygrała selekcję z bilansem 177–109–10. Oznacza
to, że nawet replay pochodzący z architektury czteroćwiartkowej nie jest sam w
sobie transferowalną polityką.

Najbliższy statyczny przebieg (indeks 37) osiągał zależnie od odświeżenia panelu
181–115 lub 183–113 i średnio około 104,8–105,0 tys. nagrody, ale tylko 120
wygranych w nowym panelu rang wobec 132 dla V2. Co ważne, pochodził z aktywnego
submissionu o wyniku publicznym 2827.9, a nie z wersji 3000+. Nie jest więc
kandydatem do zgłoszenia mimo dobrego agregatu na panelu lokalnym.

V32 sprawdził 2 000 połączeń czterech najlepszych rodziców ze stanowymi
nakładkami rynku (96 000 gier treningowych i 5 920 holdout). Każdy zwycięzca
lokalnego treningu przegrał z niezmienioną akcją rynku; modyfikacje załamywały
finansowanie i synchronizację taśmy. V33 sprawdził 258 pełnych, rynkowych i
jednostkowych splice'ów z V2 w 76 368 grach. Wszystkie splice'y były znacznie
gorsze od rodziców, a bramka ponownie wybrała V2.

Decyzja fail-closed: V31, V32 i V33 nie będą zgłaszane ani przedstawiane jako
następcy V2. Wyniki zawężają dalszą pracę do jednej drogi: własnego planera
zamkniętej pętli, który wspólnie przydziela pracowników, finansuje czwartą
ćwiartkę i pilnuje celów około 70 upraw oraz 20–23 zwierząt. Nie należy ponawiać
statycznych splice'ów, nearest-state ani samych nakładek rynku na replay.
