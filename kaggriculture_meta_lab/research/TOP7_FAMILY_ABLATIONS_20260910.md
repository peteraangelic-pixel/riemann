# TOP7 family ablations

The latest TOP7 census supports two separate mechanisms. They must not be
mixed into one random profile population.

## F1 — SpaTaro fast expansion / turnover

Observed:

```text
first sell ≈ step 9
first land ≈ step 69
buy ≈ 507
sell ≈ 306
fertilizer ≈ 42
```

Hypothesis: early expansion and high purchase turnover create an industrial
opening. The first ablation varies land timing and cash reserve while keeping
fertilizer modest.

## F2 — active fertilizer industrial

Observed across Himanshu/Yusuke/kanno/dewan슈:

```text
first sell = step 1
first land ≈ step 151
sell = 407–555
fertilizer = 120–128
animals ≈ 12
```

Hypothesis: immediate cash conversion plus sustained fertilizer-intensive
production is the key mechanism. This ablation varies fertilizer gating and
waterer count while keeping the opening active.

## Required comparison

Every rendered family variant must be compared with:

```text
B21/S16
exact G2
corrected GermanJurado1 tape
G4 negative control
```

on:

```text
TOP15
TOP7
old TOP30
fresh seeds
```

The first pass is an ablation, not a promotion. We will report first-sale,
land timing, HIRE, fertilizer, animal placement, final bank, material margin,
crashes and timeouts. A family is retained only if it beats its matched base
mechanism without a fresh TOP7 regression.
