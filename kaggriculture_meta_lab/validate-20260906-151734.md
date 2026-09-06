# Validation: agent_v8_fert.py vs agent_v7.py
workers=24  closed-loop seeds=500 (x2 seats)  corpus=corpus/sample

[1/2] Closed loop: 1000 games ...

  733W 267L 0T  score 73.3%  95% Wilson 70.5-75.9
  mean margin +649 (median +538, p10 -661)  errors 0
  seat0 361-139 margin +646 | seat1 372-128 margin +653
  GATE: PASS — PASS: 733W/267L/0T, score 73.3% (CI 70.5-75.9), margin +649

[2/2] Open-loop corpus: C:\Users\Vizua\Desktop\Projekty CC\kaggriculture\LAB z areny\corpus\sample
  8W 0L 0T over 8 episodes (errors 0)
  candidate mean cash 84,914 (median 78,835)
  recorded  mean cash 26,948  delta +57,966

elapsed 289s
