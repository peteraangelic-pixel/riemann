# Postęp z `arena/01a0712c-riemann` — decyzja A/B

Sprawdzony tip: `5521d11`.

## Najważniejsza nowość

Ta gałąź ma aktualny benchmark TOP30:

- B21 all recent selected: 75/300 wins, 25.0%, mean margin -3 862;
- B21 player 0: 24.0%; player 1: 26.0%; brak istotnego seat artefact;
- best-listed TOP30 ma około 10.4 rąk, 3 odblokowane kwadranty, 14.8 pastwisk,
  6.5 owiec, 6.4 krów i 1.7 gęsi;
- best-listed records średnio: około 336 sprzedaży, 79 zakupów nasion pszenicy
  i 95 sprzedaży nawozu;
- średnia zarejestrowana gotówka tego podzbioru to około 101.9k.

To jest lepsza referencja strategiczna niż stary TOP49. Nie przenosimy jednak
samych średnich jako parametrów — polityki są reaktywne, a korpus miesza różne
submissiony.

## Najmocniejszy obecny lead

Bounded TOP10 exemplar micro-screen z 640 gier znalazł spójną rodzinę **Subin**:

| Exemplar | non-source score | margin |
|---|---:|---:|
| Subin 106845775 | 46.7% | -282 |
| Subin 106846791 | 46.7% | -346 |
| Subin 106844933 | 46.7% | -481 |
| Subin 106847573 | 33.3% | -3 623 |
| B21/S16 | 25.0% | -7 116 |

To jest silny lead open-loop, nie dowód closed-loop. Trzy niezależne epizody
mają podobne otwarcie i cadence, a różnią się sprzedażą zależnie od stanu.
Najlepszy exemplar ma w przybliżeniu 413–415 sprzedaży, 260 HIRE, 189 zakupów
nasion, 65 zakupów produktów, 12 zakupów zwierząt i 2 zakupy ziemi.

Przejęto go lokalnie jako:

```text
agents/variants/agent_v10_subin_106845775.py
```

Jest to tylko immutable research lead, nie nowy champion. B21 pozostaje
kontrolą A/B, ale nie submission candidate.

## Co robimy inaczej niż upstream

Upstream rozwija obecnie fail-closed reactive genetics kernel i natywne overlaye
rynkowe. Nie kopiujemy ich całego podejścia ani nie mieszamy go z naszym
structural grid. Nasz rozdzielony plan:

1. v12 timing/endgame na B21 jako kontrolowany eksperyment;
2. Subin exemplar jako osobny anchor porównawczy;
3. odczyt cech pełnego replayu i rekonstrukcja małej polityki reaktywnej;
4. benchmark TOP10 → TOP20 → TOP30, oba seaty, source-episode exclusion;
5. świeży holdout 250–500 seedów;
6. dopiero potem Bayesian/CMA-ES.

Nie promujemy static Subin na podstawie 46.7%: nadal jest poniżej 50%, a jego
wynik może zawierać korelację z konkretnym korpusem.
