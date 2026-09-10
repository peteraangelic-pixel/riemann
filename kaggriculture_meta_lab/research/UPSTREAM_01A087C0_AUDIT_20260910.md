# Audit gałęzi `arena/01a087c0-riemann`

## Najważniejszy wynik

Ta gałąź nie pokazuje potwierdzonego nowego championa. Najnowszy audyt mówi
wprost, że `v12` przegrywa z silnymi agentami z gałęzi `arena/01a0712c`:

```text
v12 vs B21/S16: 0/32, margin około -139k
v12 vs static Subin: 0/32, margin około -139k
v12 vs G4-29: 0/32, margin około -123k
```

Wniosek z gałęzi: wysoki wynik V12 przeciw pasywnym przeciwnikom był złudny.
Przeciw silnym agentom elity agent zarabiał około 8–15k, a przeciwnicy
135–158k. To potwierdza, że główną luką jest architektura ekonomii, a nie
pojedynczy parametr.

## V20 — reaktywny eksperyment, ale słabszy

`farmosa_v20_b21plan.py` próbuje przejść w stronę planera reaktywnego, lecz
wynik jest niższy od V12:

```text
v20: 217523
v12: 275282
```

Zdiagnozowane problemy V20:

1. Ukryty crash `KeyError: max_yield_day`, który powodował stały fallback do
   PASS/empty market.
2. Zwierzęta kupione, ale nie rozstawiane — transport przegrywał priorytet z
   wodą i karmieniem.
3. Truskawki nie osiągały planowanej liczby z powodu gotówki/nasion.
4. Podlewanie co drugi dzień powodowało chwasty i straty.
5. Brakowało dedykowanych watererów oraz priorytetu porannego rozstawiania
   zwierząt.

## Najcenniejsze fakty z opisu FarmOS v20

Do niezależnego potwierdzenia w naszym silniku:

- market orders są wykonywane co godzinę;
- ręce są resetowane codziennie i wymagają ponownego HIRE;
- przekroczenie dostępnych nasion dla cropu może anulować wszystkie plant
  requests tego cropu w turze;
- pickup/drop działa przy czterech polach dostępu do shed;
- zwierzęta wymagają codziennego karmienia i uciekają po dwóch dniach bez feedu;
- fertilizer jest dostępny na rolloverach;
- shed ma wspólną pojemność dla produkcji i nieprzeniesionych zwierząt;
- overflow shed może wyrzucać zasoby;
- sklepy konsumują co cztery godziny według opisu tej gałęzi;
- wartość końcowa zależy od likwidacji gotówki pod koniec sezonu.

Te fakty są wartościowe, ale pochodzą z innej gałęzi i muszą być sprawdzone
w naszym aktualnym `engine.rs`/`engine.py`, zanim staną się kontraktem.

## Wniosek dla naszego projektu

Nie kopiować bezpośrednio V12/V20. Należy przejąć diagnostykę:

```text
poranny transport zwierząt
priorytet feed przed zwykłymi crop chores
dedykowani watererzy
budżet nasion przed batch PLANT
obsługa shed capacity/overflow
jawny crash sentinel zamiast cichego PASS
```

Najbliższy eksperyment powinien być ablacją jednego mechanizmu naraz na
prawdziwym `FarmerPlanner`, z wynikiem przeciwko G4 i B21 na tych samych
seedach. V20 nie jest nowym mistrzem; jest cennym źródłem failure modes.
