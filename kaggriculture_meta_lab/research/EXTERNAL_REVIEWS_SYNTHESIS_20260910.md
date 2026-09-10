# Synteza zewnętrznych przeglądów — priorytety badawcze

Data: 2026-09-10

Ten dokument zbiera cenne obserwacje z dwóch zewnętrznych przeglądów oraz z
raportu o gałęzi `arena/01a087c0-riemann`. Nie wszystkie twierdzenia zostały
jeszcze zweryfikowane w naszym checkoutcie. Status każdej obserwacji jest jawnie
oznaczony.

## 1. Najważniejsza nowa hipoteza: off-by-one w compilerze tape

Zewnętrzny raport twierdzi, że prawidłowe mapowanie replayu jest:

```text
akcja wykonana w kroku s jest zapisana w wierszu s+1
_ACTIONS = steps[1:]
agent zwraca _ACTIONS[min(step, N-1)]
```

Raport podaje dokładne odtworzenie trzech epizodów co do końcowej gotówki:

```text
SpaTaro:     144820 / 131575
Otter Vibe:  118379 / 130220
ultimatum:   177788 / 144720
```

### Status

To jest **zewnętrzny claim do niezależnej reprodukcji**, nie przyjmujemy go
jeszcze jako faktu dla wszystkich naszych narzędzi. W naszym `rust_backend.py`
raw replay path już używa `steps[1:]`, ale należy sprawdzić cały łańcuch:

```text
replay parser
→ tape compiler
→ candidate seat
→ simulator step
→ final reward
```

### Akcja

Dodać trzy golden replay fixtures i test dokładnego odtworzenia final rewards.
Żaden ranking tape nie powinien być interpretowany przed przejściem tego testu.

## 2. GermanJurado1 tape — interesujący, ale open-loop

Raport z innej gałęzi opisuje:

```text
champion_tape_germanjurado1_v1.py
```

oraz wyniki:

```text
vs static Subin: 64-0
vs B21:          68-4
vs Aastik:       28-4
```

na podanych zakresach seedów. Ma także podany round-robin finalistów i wynik
32-0 / 28-4 / 28-4 na nowych seedach.

### Status

To może być bardzo wartościowy **open-loop tape control**, ale nie jest
reaktywnym agentem i nie dowodzi przewagi w finale. Wynik wymaga:

1. odzyskania commitu/plików z `arena/01a087c0-riemann`;
2. sprawdzenia poprawności tape compiler;
3. odtworzenia wyników tym samym seedem i tym samym silnikiem;
4. testu przeciwko żywemu reaktywnemu przeciwnikowi;
5. testu fresh holdout.

Nie wolno nazywać go championem submission bez tych bramek.

## 3. G4 i G3 — problem odtwarzalności profili

Zewnętrzna recenzja zauważyła, że profile G3/G4 zawierają klucze takie jak:

```text
hands_per_quadrant
cow_target
sheep_target
goose_target
land_min_hands
wheat_seed_target
```

podczas gdy `MarketOverlay` Python/Rust akceptuje przede wszystkim:

```text
*_reserve
min_*_price
sell_fraction_bp
buy_stop_day
endgame_day
```

### Status

To jest poważny problem reprodukowalności. Profile G3/G4 nie są zwykłymi
market overlays. Najprawdopodobniej konfigurują szerszy `FarmerPlanner` albo
pochodzą z innego generatora niż ten obecnie widoczny w naszym launcherze.

### Akcja

Odtworzyć dokładny generator i runner G3/G4. Zapisać:

```text
source commit
source file
profile schema
base agent
runner command
seed range
seat mapping
```

Dopóki tego nie ma, `G4 = 29/83` traktujemy jako wynik raportowany, lecz nie
w pełni odtwarzalny benchmark.

## 4. R1–R4 — zewnętrzna krytyka jest trafna

Obecne moduły R1/R2/R3/R4 używają abstrakcyjnego schematu:

```python
observation["legal_actions"]
observation["inventory"]
observation["workers"]["actions"]
{"type": "SELL", ...}
```

Prawdziwy schemat Kaggriculture używany przez istniejący planner to między
innymi:

```python
obs["player"]
obs["farms"][player]["tiles"]
obs["private"]
```

a akcja ma postać:

```python
{
    "farmer": [...],
    "hands": [[...], [...]],
    "market": [...],
}
```

### Wniosek

R1–R4 nie są jeszcze częściowo zintegrowanym agentem. Są prototypem decyzyjnym
w innym schemacie. Nie należy budować drugiego równoległego planera od zera.
Lepsza droga:

```text
istniejący FarmerPlanner
+ public-state mode selector
+ bezpieczne ablations
+ poprawne pełne action rendering
```

To jest teraz priorytet integracyjny.

## 5. Możliwe błędy w G4 do sprawdzenia

### 5.1 TICKS_PER_DAY

W `agent_v10_reactive_subin.py` występują jednocześnie:

```text
TICKS_PER_DAY = 6.0
turns_per_day = 24
```

Jeżeli sklepy konsumują co godzinę, carrot demand może być zaniżony czterokrotnie.
Jeśli konsumują co 4 godziny, stała 6 może być poprawna.

**Nie jest to jeszcze potwierdzony bug.** Trzeba sprawdzić bezpośrednio kod
konsumpcji sklepów w silniku i napisać test jednej doby.

### 5.2 ANIMAL_CELLS kontra ACCESS

Recenzja wskazuje możliwą kolizję:

```text
market_overlay.ACCESS zawiera (4,4)
ANIMAL_CELLS zaczyna się od (4,4)
```

To może powodować konflikt między wejściem do szopy a budową/obsługą struktury
zwierzęcej.

**Status:** hipoteza do sprawdzenia w `engine.rs`/`data.rs`, nie potwierdzony bug.

### 5.3 B21/S16

Zewnętrzna analiza twierdzi, że nazwa B21/S16 jest myląca: kod zmienia tylko
początkowe akcje market w dwóch pierwszych krokach, a pozostałe 718 kroków
pozostaje replayem.

To należy zweryfikować i opisać jasno. Jeśli prawda, B21/S16 jest kontrolnym
bootstrap tape, a nie ciągłą polityką `kup 21 / sprzedaj 16`.

## 6. Rust/Python parity

Należy dodać golden vectors dla tych samych:

```text
state
action
profile
```

oraz porównać:

```text
quote
buy/sell gating
reserve handling
endgame handling
animal-structure detection
```

Samo przejście osobnych testów Python i Rust nie gwarantuje parytetu.

## 7. Crash/timeout safety

Reaktywny agent powinien mieć:

```text
try/except na act()
bezpieczny legalny fallback
czasowy budget
walidację liczby hands
walidację inventory
walidację market orders
```

Jeden brakujący klucz observation nie może kończyć całego tournamentu.

## 8. Lepszy plan eksperymentów

### Gen N — naprawcza

1. Zweryfikować off-by-one na trzech replayach.
2. Zweryfikować cykl konsumpcji sklepów.
3. Zweryfikować `ANIMAL_CELLS` i `ACCESS`.
4. Dodać asercje B21/S16.
5. Dodać golden vectors Python/Rust.
6. Odtworzyć generator G3/G4.

### Gen N+1 — benchmark

1. GermanJurado1 tape jako osobny open-loop control.
2. G4 z odtwarzalnym profilem.
3. B21/S16.
4. TOP15, stary TOP30, fresh holdout.
5. Paired seats z tymi samymi seedami.

### Gen N+2 — closed loop

1. Reuse istniejącego `FarmerPlanner`.
2. Dodać mode selector jako input, nie nowy abstrakcyjny action schema.
3. Włączyć/ablować `ADAPT_OPPONENT_MODE`.
4. Testować timed land vs AUTO.
5. Testować crop/animal/labor ablations.
6. Self-play candidate vs poprzednia generacja.

### Kill criteria

Kandydat odpada, jeśli:

```text
crash > 0
obie seaty nie są dodatnie
material margin <= 0 vs B21/S16
fresh holdout <= 0
transfer TOP30 załamuje się
przegrywa z poprzednią generacją self-play
```

## 9. Najważniejsze wspólne wnioski z recenzji

- Największym problemem nie jest brak LLM.
- Największym problemem jest brak odtwarzalnego closed-loop harnessu.
- Static tape i mirror score są diagnostyczne, nie promocyjne.
- GermanJurado1 może być cennym control/tape, ale nie gotowym adaptacyjnym
  championem.
- G4 może być silny, ale profil i runner muszą być reprodukowalne.
- R1–R4 trzeba podłączyć do realnego schema zamiast rozwijać fikcyjny adapter.
- Największą wartością małego modelu byłby wybór trybu planera, nie generowanie
  surowych akcji.
- TOP15 powinien być odświeżany bliżej deadline'u konkursu; obecny snapshot nie
  musi reprezentować finalnej meta.
- Trzeba dodać self-play między generacjami, bo statyczny przeciwnik nie umie
  skontrować kandydata.

## 10. Aktualna decyzja projektowa

Nie promować żadnego z poniższych wyłącznie na podstawie mirror scores:

```text
G2
G3
G4
GermanJurado1 tape
Static Subin
```

Najpierw uzyskać reprodukowalny closed-loop wynik oraz raport:

```text
candidate vs B21/S16
candidate vs G4
candidate vs previous generation
TOP15
old TOP30
fresh holdout
same seeds
both seats
zero crashes
material margins
```
