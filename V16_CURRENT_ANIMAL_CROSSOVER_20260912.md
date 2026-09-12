# V16 — aktualny hybrydowy profil zwierzęcy (2026-09-12)

## Stan live

Ponowne odpytanie Kaggle po stabilizacji:

- V3, ref `56154098`: **2116.6**, COMPLETE;
- V7, ref `56159653`: **1994.2**, COMPLETE;
- wcześniejszy V2/V16, ref `56142365`: **2815.2**.

Wyniki V3/V7 potwierdzają, że wysoki wynik lokalny starych taśm nie przewiduje już dobrze aktualnego LB. Nie należy promować V8/V14 tylko dlatego, że wygrywają lokalny panel.

## Szeroki screen aktualnego TOP12

Przesiano wszystkie 108 wybranych taśm aktualnego TOP12 na dwóch wspólnych świeżych seedach: **46 656 gier**. Następnie 12 najlepszych przeszło niezależny holdout po 1728 gier. Najlepszym aktualnym rodzicem pod względem zwycięstw był neutralny `p097`; reprezentuje kompletną ekonomię zwierzęcą (budowa pastwisk, rozmieszczanie, karmienie, opieka i odbiór nawozu).

Proste zastąpienie starej polityki nie wystarczyło: lokalny V8 nadal wygrywał panel, choć jego bliski krewny V7 uzyskał tylko 1994.2 live. To kolejny dowód starzenia się panelu i konieczności korzystania z aktualnych rodziców.

## Odrzucone V14 i V15

- V14 przełączał V8 na aktualną politykę zwierzęcą dla rozpoznawalnego niskogotówkowego otwarcia. Na niezależnych seedach nie poprawił liczby zwycięstw, a obniżył własną nagrodę. **Odrzucony.**
- V15 dodawał reaktywne naprawy `FEED`, `CARE`, `COLLECT_FERTILIZER`, `BUILD_PASTURE` i `PLACE` w chwilach, gdy taśma planowała `PASS`. Liczba zwycięstw pozostała taka sama, lecz średnia nagroda i marża spadły. Dodatkowe czynności zabierały czas lepiej zaplanowanej pracy. **Odrzucony.**

## Konstrukcja V16

Rodzice `p091` i `p097` pochodzą z dwóch niezależnych epizodów tej samej aktualnej polityki o zarejestrowanym publicznym wyniku **2943.2**. Wykonano deterministyczny screen **128 pełnodniowych masek krzyżowania**:

- faza treningowa: **55 296 gier**;
- niezależny holdout: **29 376 gier**;
- przeciwnicy: wszystkie 108 taśm aktualnego TOP12;
- każdy kandydat grał w obu fizycznych miejscach.

Bezpieczny zwycięzca `45` używa:

- `p091` przez dni 0–22;
- `p097` przez dni 23–29.

Nie jest to drobna zmiana rynku, lecz pełny aktualny harmonogram upraw i zwierząt z alternatywną siedmiodniową końcówką.

### Holdout wyszukiwania

| Kandydat | W–L | Śr. nagroda | Śr. marża |
|---|---:|---:|---:|
| rodzic p097 | 1286–428 | 105586 | 13202 |
| **V16** | **1320–408** | 105181 | **13272** |

V16 zyskał 34 zwycięstwa, zmniejszył liczbę porażek o 20 i nie cofnął żadnej grupy rankingowej względem rodzica. Agresywniejszy crossover uzyskał 1349–379, ale cofnął grupę rank 12 o 20 zwycięstw, dlatego nie został wybrany.

## Niezależny gate promocyjny

### Aktualny TOP12, seedy 193000–193007, 1728 gier na kandydata

| Kandydat | W–L | Śr. nagroda | Śr. marża |
|---|---:|---:|---:|
| V8 | 1498–230 | 105695 | 22172 |
| V7 | 1480–248 | 105051 | 21611 |
| **V16** | **1456–272** | **105200** | **15629** |
| rodzic p097 | 1408–304 | 105314 | 15360 |
| G2 | 1324–404 | 103232 | 14321 |
| V2 | 1320–408 | 101761 | 11235 |

V16 poprawił rodzica o **48 zwycięstw**, G2 o **132**, a V2 o **136**. W dopasowaniu per-gra własna nagroda była wyższa od G2 o 1968 i od V2 o 3438.

### Poprzedni TOP7, seedy 194000–194003, 672 gry na kandydata

| Kandydat | W–L | Śr. nagroda | Śr. marża |
|---|---:|---:|---:|
| V8 | 611–60 | 111967 | 29731 |
| V2 | 610–62 | 107137 | 21678 |
| V7 | 607–65 | 111293 | 29070 |
| **V16** | **600–72** | **107182** | **21740** |
| rodzic p097 | 590–82 | 107711 | 21538 |
| G2 | 582–90 | 107716 | 21352 |

V16 zachował transfer: +10 zwycięstw nad rodzicem i +18 nad G2; względem V2 stracił 10 zwycięstw, ale miał nieco większą średnią nagrodę i marżę.

## Werdykt

V16 jest obecnie najmocniejszym **nowym, aktualnym i neutralnie nazwanym** kandydatem. Jest wyraźnie lepszy od G2 oraz obecnego rodzica w dwóch niezależnych panelach i bazuje na gospodarce, której źródłowy aktualny wynik wynosił 2943.2. Nadal jest częściowo open-loop, więc lokalne wyniki nie gwarantują przekroczenia 3000 live. Nie wysyłać automatycznie: obowiązuje ograniczenie dwóch aktywnych agentów i wspólna decyzja użytkownika.

## Dalszy V17 — selektywny router rynku

Agresywniejszy crossover (rodzic p097 przez dni 0–3, p091 od dnia 4) miał w holdoucie 1349–379, ale jego regresja skupiała się prawie wyłącznie na rank 12. Jednocześnie poprawiał charakterystyczną klasę rank 8 z 62 do 116 zwycięstw. Klasa ta wykonuje na początku duży obrót pszenicą `BUY 7, BUY 20, SELL 60`, który pozostawia publiczny stan rynku odmienny od małego arbitrażu rank 12.

V17 obserwuje po pierwszej turze liczbę rąk przeciwnika oraz globalny zapas pszenicy. Dla stanu bez zatrudnionych rąk i zapasu co najmniej 9986 wybiera agresywny crossover; w pozostałych przypadkach zachowuje bezpieczny V16.

Celowany prawdziwy test closed-loop (seed 195000, obie strony):

| Klasa | V16 | V17 | Nagroda V16 → V17 | Marża V16 → V17 |
|---|---:|---:|---:|---:|
| docelowy rank 8 | 0–18 | **2–16** | 139677 → **140395** | −2345 → **−1647** |
| sąsiednie rank 7/11/12 | 44–10 | **46–8** | 139390 → 139347 | 8255 → **8372** |

Router rzeczywiście przełączył politykę i zyskał cztery zwycięstwa bez regresji zbiorczej. Rozbicie: rank 7 +2 zwycięstwa, rank 8 +2, rank 11 i 12 bez zmian. W ośmioseedowym holdoucie statycznym klasy, które powinny aktywować router (rank 6/8/9 i część rank 7), agresywny wariant miał potencjał około +60 zwycięstw względem V16.

Drugi niezależny closed-loop seed 195001 rozszerzył klasę docelową na rank 6/7/8/9:

- V16 i V17 po 72–0, ale V17 zwiększył średnią nagrodę **87559 → 87745** i marżę **13947 → 14128**;
- kontrolne rank 11/12 pozostały dokładnie niezmienione: 28–8, nagroda 79096, marża 6424;
- w rozbiciu V17 zwiększył nagrodę rank 6 o 1076 i rank 9 o 522; spadek rank 7 o 850 nie pogorszył marży ani wyniku, rank 8 był praktycznie równy.

Po dwóch rzeczywistych seedach router ma łącznie +4 zwycięstwa, dodatnią zmianę marży w klasach aktywowanych i zero zmienionych wyników w chronionych rank 11/12. V17 jest obecnie najbardziej obiecującym wariantem, a V16 pozostaje prostszym wariantem bezpiecznym. Ze względu na bardzo dużą zmienność seedów V17 nadal nie powinien być wysyłany automatycznie.

Źródło V17: `kaggriculture_meta_lab/agents/candidates/agent_v17_state_router.py`; wyniki: `kaggriculture_meta_lab/results/v17-state-router-targeted-20260912.json` oraz `v17-state-router-second-seed-20260912.json`.

Źródła wyników:

- `kaggriculture_meta_lab/results/v13-top12-parent-screen-20260912.json`
- `kaggriculture_meta_lab/results/v13-parent-survivor-holdout-20260912.json`
- `kaggriculture_meta_lab/results/v16-current-animal-crossovers-20260912.json`
- `kaggriculture_meta_lab/results/v16-current-top12-promotion-20260912.json`
- `kaggriculture_meta_lab/results/v16-previous-top7-promotion-20260912.json`
- `kaggriculture_meta_lab/results/kaggle-v3-v7-stabilized-20260912.json`
