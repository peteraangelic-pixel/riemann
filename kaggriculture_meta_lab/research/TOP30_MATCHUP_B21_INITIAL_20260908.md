# B21/S16 kontra TOP30 — prawidłowy replay benchmark

Data: 2026-09-08. Kandydat: `agents/current/agent_v9_b21_s16.py`.
Źródło: `TOP30.7z` z gałęzi `arena/01a0712c-riemann`, commit `1ebeefd`.

## Korekta metodologiczna

Pierwszy lokalny prototyp sprawdził kandydata tylko w oryginalnym seatcie drużyny
TOP30, a nie w obu fizycznych seatów. Jego wynik 150-0 był więc niewłaściwą
metryką porównawczą i nie jest używany.

Prawidłowy benchmark powinien:

- używać zapisanej taśmy **nazwanej drużyny TOP30** jako przeciwnika;
- zastępować tę drużynę kandydatem;
- uruchamiać kandydata w obu fizycznych seatów;
- zachowywać oryginalny seed;
- traktować wynik jako open-loop replay stress, nie closed-loop leaderboard.

Audyt tej procedury z gałęzi `arena/01a0712c-riemann` wykonał 300 gier na 150
rekordach. Wynik B21:

| Korpus | Gry | W | L | Score rate | Średni margin |
|---|---:|---:|---:|---:|---:|
| TOP10, selected recent | 100 | 23 | 77 | 23,0% | -2 301 |
| TOP20, selected recent | 200 | 39 | 161 | 19,5% | -5 744 |
| TOP30, selected recent | 300 | 75 | 225 | 25,0% | -3 862 |

To jest istotny wynik: **B21 nie jest obecnie wystarczającą referencją przeciwko
aktualnemu TOP30**. TOP49 nie może już służyć jako główna bramka.

## Co z tego wynika

Nie kopiujemy bezpośrednio sztywnych replayów. Skoro B21 przegrywa z nagraną
polityką nawet w poprawnym open-loop stress, potrzebujemy znaleźć przyczynę:

1. rozdzielić porażki według pierwszego materialnego rozjazdu;
2. porównać cash, inventory, market i produkcję co 10–24 kroki;
3. odróżnić przegraną wysokiego turnoveru od delayed-sale;
4. sprawdzić osobno best-listed-submission i wszystkie recent selected;
5. budować closed-loop reprezentantów rodzin, nie kopiować nazw graczy.

Najważniejszy nowy sygnał z upstream audytu: wybór TOP30 to najnowsze epizody
aktywnych submissionów, a nie zawsze pięć gier z najlepszego submissionu danego
zespołu. Dlatego raporty muszą rozróżniać oba podzbiory.

## Narzędzie

`scripts/top30_matchup.py` zostało poprawione tak, aby kandydat był testowany w
obu seatów przeciwko taśmie nazwanej drużyny. Reprodukcja:

```bash
PYTHONPATH=. python scripts/top30_matchup.py /path/to/extracted/TOP30 \
  --team SpaTaro --team "Otter Vibe" --team binghua
```

## Następny krok

Najpierw używamy poprawnego benchmarku 300 gier jako baseline dla v12. Potem
wybieramy profile z największym wkładem do porażek i rekonstruujemy ich rodziny
closed-loop. Każdy nowy agent musi poprawić B21 na TOP30, zachować wynik wobec
V7/Aastik/hybrid i przejść świeży holdout 250–500 seedów.
