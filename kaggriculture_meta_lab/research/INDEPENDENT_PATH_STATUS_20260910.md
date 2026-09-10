# Independent path status

The independent path is not a copied GermanJurado1/G2/G4 strategy. The first
implemented artifact is a safety wrapper around the real-schema V10 planner:
`agents/variants/agent_v10_reactive_safe.py`.

## First smoke result

Against B21/S16, seed 100, both seat swaps:

```text
0 wins / 2 losses / 0 ties
candidate mean: 37,278
B21 mean:       110,834
```

This is a diagnostic result, not a candidate promotion. It shows that adding
exception containment alone does not create a strong policy. The wrapper must
not be confused with a stronger agent.

## Independent strategy direction

The next real strategy work must alter the real-schema FarmerPlanner around
measurable bottlenecks, not tape actions:

1. prevent silent planner failure while preserving an error counter;
2. allocate workers by bottleneck: water, animal feed/placement, harvest,
   transport, fertilizer;
3. enforce seed and shed capacity budgets before batch actions;
4. test production modes against the two TOP7 families;
5. retain only changes that improve final bank and material margin on fresh
   seeds, not only mirror score.
