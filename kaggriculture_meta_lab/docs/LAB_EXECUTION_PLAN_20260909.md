# LAB execution plan — v12 + Subin evolution

## Aktualny stan wiedzy

- B21/S16 pozostaje zamrożonym baseline’em, ale na aktualnym TOP30 ma 75/300
  zwycięstw, 25,0% score rate i średni margin -3862.
- Najmocniejszy open-loop lead to trzy niezależne replaye rodziny Subin:
  46,7%, margin -282 do -481 po wykluczeniu source episode. To lead, nie
  kandydat submissionowy.
- TOP30 best-listed action census wskazuje około 10,4 rąk, 3 kwadranty,
  14,8 pastwisk, 6,5 owiec, 6,4 krów, 1,7 gęsi, około 336 sprzedaży i 79
  zakupów nasion pszenicy. Nie kopiujemy średnich bezwarunkowo.
- Static replay matchup jest diagnostyką open-loop. Promocja wymaga closed-loop
  lub świeżego holdoutu.

## Tor A — strukturalny v12

`v12_timing_endgame.json` obejmuje 27 wariantów:

- `hire_deadline`: 500/600/720;
- `fert_deadline`: 500/600/720;
- `liquidate_from`: disabled/700/710.

Kolejność:

1. screen: 20 seedów, oba seaty;
2. promote: 120 seedów, baseline B21 zawsze obecny;
3. finals: 175 seedów, baseline i finalistów;
4. TOP30 gate, świeży holdout 250–500 seedów.

## Tor B — Subin reactive genetics

Bazą jest `agents/variants/agent_v10_reactive_subin.py`. Generator
`generate_reactive_population.py`:

- zmienia tylko 22 jawnie ograniczone geny;
- nie importuje ani nie wykonuje kodu bazowego podczas generacji;
- tworzy pierwszy osobnik jako baseline;
- jest deterministyczny po seedzie;
- wspiera późniejsze mutate/crossover przez `reactive_genetics.py`;
- renderuje poprawny Python i zapisuje manifest SHA-256.

Etapowanie:

1. wygenerować 1000 genomów, nie 1000 ręcznie pisanych agentów;
2. screen TOP10: V7, Aastik, hybrid oraz reprezentant TOP10;
3. odrzucić crash/error i niestabilne osobniki;
4. zachować top 10, zawsze z kontrolą baseline;
5. mutate/crossover do kolejnej generacji;
6. rozszerzyć najlepszych do TOP20;
7. rozszerzyć do TOP30;
8. holdout 250–500 seedów, oba seaty;
9. dopiero wtedy Bayes/CMA-ES.

Dla 10 000 genomów używać manifestu/genotype-first i renderować tylko
screenowane top-K. Nie zapisywać 10 000 pełnych kopii źródła, jeśli nie są
potrzebne do uruchomienia.

## Budżet obliczeń

Kalkulator:

```bash
python scripts/compute_lab_plan.py --population 1000 \
  --output reports/lab-plan-1000.json
```

Domyślny plan przy 4000 Rust games/s:

| Etap | Gry |
|---|---:|
| v12 screen | 1080 |
| v12 promote | 2400 |
| v12 finals | 3850 |
| reactive population screen, 1000 | 64 000 |
| reactive promote | 2400 |
| TOP20 gate | 1000 |
| TOP30 gate | 1500 |
| holdout top-K | 5000 |
| **razem** | **81 230** |

To jest plan z kontrolami i oboma seatami, a nie obietnica czasu. Przy zmierzonej
przepustowości 4000 gier/s daje około 20,3 s czystego replayu; rzeczywisty czas
będzie większy przez eksport taśm, procesy, parsowanie, rating i reaktywnych
agentów Python. Dlatego najpierw kalibrujemy throughput na 5950X, a potem
wpisujemy pomiar do kalkulatora.

## Kryterium promocji

Kandydat musi mieć:

- zero crashów;
- dodatni materialny margin względem B21 i zróżnicowanych kontroli;
- poprawę W/L na TOP30, nie tylko mirror;
- stabilność obu seatów;
- brak spadku na V7/Aastik/hybrid;
- pozytywny świeży holdout 250–500 seedów.

Near-tie, wynik z jednego seeda albo poprawa wyłącznie na source replay nie
wystarcza.

## Podział sprzętu

GitHub Actions: compile, parity, małe bounded screens i niezależne regresje.

Ryzen 9 5950X/64 GB: pełny v12, populacje 1000–10000, generacje, trace
analysis, TOP20/TOP30 i holdout. Rust pozwala użyć 16 workerów; nie usuwa
potrzeby LAB-u, tylko zwiększa rozmiar eksperymentu, który możemy wykonać.
