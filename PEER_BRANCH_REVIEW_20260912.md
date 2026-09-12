# Przegląd gałęzi 01a08fb2 — 2026-09-12

Stan zdalny: `84aebbc`.

## Fakty

1. Commit `ea4d2fc` zastąpił `kaggriculture/main.py` 823-liniowym reaktywnym FarmOS v16 (`farmosa_v16_fert_zonegate`). Kod zawiera pełną obsługę zakupu, budowy, rozmieszczania, karmienia, opieki, zbierania nawozu, stref pracowników, podlewania i likwidacji.
2. Action `34679674275` zakończył się sukcesem, ale workflow kompiluje i uruchamia `agent.py`, nie `main.py`. `agent.py` nadal jest starym reaktywnym V2. Artefakt workflow również powstaje przez skopiowanie `agent.py` do `main.py`.
3. Job wysyłający do Kaggle został `skipped`: commit nie miał wymaganego `[kaggr-submit]` i nie uruchomiono ręcznego `workflow_dispatch` z `submit=true`. Zatem nowy FarmOS z `main.py` nie został tym Action ani przetestowany, ani spakowany, ani wysłany.
4. Jest to wariant rodziny, której wcześniejsze własne pomiary gałęzi wykazały regresję względem FarmOS v12 i całkowitą niekonkurencyjność wobec elitarnych taśm. Sam sukces Action nie stanowi nowego dowodu jakości.
5. Commit `84aebbc` aktualizuje `TOP12.7z`; manifest wygenerowano `2026-09-12T07:13:21Z`. Aktualna czołówka zawiera wynik 3208.3, a pozycje 2–4 przekraczają 3047.

Najnowszy TOP12 został przeniesiony do naszej gałęzi w `39d30af` i przesiany w Action `34691296463` (46 656 gier). Wynik ponownie pokazuje bardzo słabą korelację open-loop z publicznym LB: lokalny zwycięzca pochodzi z taśmy oznaczonej wynikiem 2576.4, podczas gdy taśmy źródłowe 3208.3 mają wyniki lokalne od 63 do 220 zwycięstw. Nie należy wybierać kolejnego zgłoszenia wyłącznie po tym screenie.
