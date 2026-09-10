# TOP7 — audyt, strategie i próba poprawy lidera (2026-09-10)

## Korpus

Źródło: `TOP7.7z`, SHA i pełna lista plików w `results/top7-audit-20260910.json`.

- 7 drużyn, po 12 slotów, 84 kompletne pliki replay;
- 78 unikalnych epizodów i seedów, 6 slotów będących kopiami tego samego meczu;
- 14 submissionów; 168 statusów DONE; brak seeda zero i brak awarii;
- wszystkie 84 pary surowych taśm odtworzyły oryginalne wyniki co do jednostki pieniędzy.

Tabela w chwili zebrania: SpaTaro 3055.3, Himanshu Kumar 3022.1, Otter Vibe 2988.5, binghua 2980.6, デワンシュ 2978.8, kanno 2972.3, Yusuke Hayashi 2965.7.

`audit_top15.py` został uogólniony o jawne `--expected-teams` i `--expected-episodes`; nadal jest fail-closed i zachowuje domyślne 15×7 dla TOP15.

## Jak wypada wysłany lider

GermanJurado `107218640` zastępował gracza TOP7 w jego oryginalnym seacie i seedzie, przeciw oryginalnej taśmie drugiej strony:

- **65–19**, średni margines **+5243.4**, zero błędów;
- SpaTaro 10–2, Himanshu 7–5, Otter 11–1, Yusuke 9–3, binghua 6–6, kanno 11–1, デワンシュ 11–1.

To open-loop z realistyczną presją rynku, ale przeciwnik nie reaguje na zmienioną grę. Największą wykrytą słabością jest grupa epizodów folderu binghua. German-specialist `107212592` uzyskał 61–23 (+5375.7), więc nie zastępuje lidera.

## Co robią gracze 3000+

Wnioski dotyczą obserwowanych akcji, nie kodu źródłowego agentów:

1. **SpaTaro (3055)** używa wyraźnie innej gospodarki: agresywnie kupuje nie tylko wheat/fertilizer, ale również carrot, melon, milk, tomato, egg, wool i strawberry. Utrzymuje około 8–9 pomocników oraz trzy ćwiartki. Wskazuje to na reaktywny handel/arbitraż i wykorzystanie popytu premium, nie tylko produkcję farmy.
2. **Himanshu (3022)** kończy zwykle z 11 pomocnikami i trzema ćwiartkami. Łączy duże stado (cow/sheep/goose), kupowanie wheat/fertilizer, intensywne nawożenie oraz wielokrotne zlecenia sprzedaży wszystkich produktów.
3. **Kanno, Yusuke i Himanshu** mają bardzo podobne sygnatury makro: 11 pomocników, trzy ćwiartki, te same klasy zwierząt i upraw oraz rozbudowaną likwidację rynku. Nie są jednak kopiami: w 84 strumieniach znaleziono 83 unikalne sekwencje, co wskazuje na reakcję na stan.
4. **Otter Vibe** zatrudnia najwięcej jednostek (zwykle 12–13), intensywnie nawozi i obsługuje zwierzęta. Jego pojedyncze taśmy słabo transferują do syntetycznych seedów, więc przewaga live prawdopodobnie pochodzi z reaktywności.
5. **Binghua** ma dwa bardzo różne submissiony. Lepszy leaderboardowo wariant jest bardziej zwarty; nowszy, słabszy live mocniej rozbudowuje uprawy i zwierzęta.
6. Wspólny motyw TOP7 to trzy ćwiartki, rozbudowa pracowników, livestock, fertilizer i sprzedaż pełnego koszyka. Samo kopiowanie jednej taśmy zwykle nie przenosi wysokiego wyniku live — ważne są timing oraz reakcja rynku.

Surowe liczniki per team/submission są w `results/top7-strategy-signatures-20260910.json`.

## Screening wszystkich taśm

Najpierw wybrano po jednej taśmie o największej nagrodzie źródłowej dla każdego z 14 submissionów i przetestowano ją na seedach 70000–70015 przeciw liderowi, B21 i surowemu Subinowi. Następnie wszystkie 84 taśmy przeszły screen przeciw liderowi na seedach 71000–71003.

Większość taśm SpaTaro/Otter/Binghua załamuje się po zmianie seeda pomimo wysokich nagród źródłowych. To kolejny dowód, że open-loop nie odtwarza ich reaktywnej przewagi.

Najlepszym challengerem okazała się taśma Kanno z epizodu `107377838`, submission `56137264`:

- fresh direct vs German lider, 128 seedów × oba seaty: **247–9**, +1043.6;
- vs German-specialist: **209–47**, +9721.5;
- vs B21: **198–58**, ale tylko +346.1;
- pełny closed-loop vs G2: **16–0**, +8422;
- pełny closed-loop vs G4: **16–0**, +39840;
- TOP7 open-loop: 63–21, +5612.7 (lider: 65–19, +5243.4).

Challenger jest zachowany jako `agents/candidates/top7_kanno_ep107377838.py`, bez numeru V. Ważne zastrzeżenie: submission źródłowy miał tylko 2787.6 public score; leaderboard Kanno 2972+ pochodził z innego submissionu. Taśma jest znakomita w lockstep i przeciw G2/G4, ale ma mniejszy margines bezpieczeństwa przeciw B21 i o dwie porażki więcej na TOP7 open-loop. Nie zastępuje jeszcze V15 bez większego closed-loop i dowodu live.

## Dekompozycja German ↔ Kanno

Te dwie taśmy są zaskakująco bliskie: 444/719 całych kroków identycznych; różni się 4 farmer actions, 58 list hands i 243 market actions. Próby faktoryzacji ujawniły silną koordynację:

- German units + Kanno market wygrywał z Germanem 98–30, ale załamał się przeciw B21 do 15–241;
- Kanno units + German market zachował B21 215–41, ale przegrał z Germanem 35–89–4.

Nie wolno promować hybryd. Wynik tłumaczy też wcześniejsze porażki prostych market/recovery overlayów: lokalna poprawa jednej osi niszczy interakcję jednostek z rynkiem.

## Decyzja i dalszy kierunek

- V15 pozostaje wysłanym, bezpieczniejszym liderem ogólnym.
- Kanno `107377838` jest najsilniejszym challengerem i teacherem do kolejnej rundy.
- Najbardziej obiecujące ulepszenie nie polega na podmianie market tape, lecz na reaktywnym selektorze całych planów: rozpoznać po pierwszych obserwowanych krokach rodzinę presji przeciwnika i wybrać spójny plan German albo Kanno.
- Drugim kierunkiem jest przeniesienie idei SpaTaro: ograniczony, stanowy handel premium z pełnym sekwencyjnym księgowaniem, testowany jako kompletna polityka, nie luźny overlay.
- Każdy następny kandydat musi przejść G2, G4, B21, TOP7 open-loop, fresh paired seeds i zero-crash. Wyniku V15 live nie należy zastępować samą przewagą lockstep.

## Aktualizacja po audycie `arena/01a087c0-riemann` — Kanno best-sub v2

Gałąź doszła do ważniejszego kandydata niż nasz wcześniejszy Kanno `107377838`: wybrała **best-listed submission 56133568 (public 2975.9), epizod 107384200**. Jej commit `4614aab` raportuje 75–53 przeciw Germanowi w dwóch blokach, 96–0 przeciw raw Subinowi, 85–11 przeciw B21, 32–0 (+10063) przeciw pełnemu G2 oraz 184–8 w round-robin TOP7.

Niezależna weryfikacja:

- lokalna rekonstrukcja i artefakt gałęzi mają **719/719 identycznych akcji**;
- dokładnie odtworzono źródło na seedzie 522182097: `[84925, 78077]`;
- fresh seedy 76000–76127 × oba seaty: **212–44** przeciw V15 (+602.4), **145–111** przeciw Kanno z niżej notowanego submissionu oraz **213–43** przeciw B21 (+9745.1), zero błędów;
- pełny G2, fresh seedy 77000–77007: **16–0, +9623**; V15 na identycznych seedach **16–0, +5347**. Paired delta +4276.4, kandydat lepszy w 14/16 gier.

To zmienia ocenę: `top7_kanno_bestsub_ep107384200.py` jest obecnie kandydatem jakości submission, mocniejszym niż V15 na bezpośrednim fresh H2H, G2 i porównywalnym B21. Nie podmieniono po cichu już wysłanego V15; kolejna promocja/submission powinna być jawną decyzją i dostać osobny numer.

## V16 LAB: day-level crossover

Po autoryzacji V16 uruchomiono GitHub Actions LAB `34466271319`. Rust przeliczył 256 spójnych planów dziennych German/Kanno: 16384 gier treningowych i 4352 holdout w 47 sekund całego joba. Zwycięzca trening/holdout używał dni German 0, 17 i 23, a w pozostałych dniach Kanno. Na holdout podniósł średni score rate z 0.7383 do 0.9023 i został wyemitowany jako `v16_day_crossover_holdout_winner.py`.

Obowiązkowa niezależna dogrywka ujawniła regresję:

- fresh direct vs V16 parent: 245–11 (+401.8), więc crossover faktycznie zmienia matchup;
- fresh B21: crossover **204–52, +6774.9**; czysty V16 na identycznych seedach **214–42, +10337.4**.

Crossover zostaje odrzucony mimo zwycięstwa selekcyjnego. Żaden z 16 finalistów holdout nie poprawił Germana, zachowując jednocześnie zarówno score rate, jak i margines B21 rodzica. To mocny sygnał, że czysty Kanno jest na aktualnym froncie Pareto statycznych mieszanek, a dalsza poprawa wymaga reaktywnego wyboru/rynku zamiast kolejnego splice taśm.

## Korekta oceny LAB i rozszerzona kampania

Uwaga użytkownika była trafna: pierwszy job nie był „zaawansowanym LAB-em permutacji V16”, tylko **pilotem 256 jednopokoleniowych masek pełnych dni dwóch taśm**. Liczba 20k gier brzmiała szeroko, ale przestrzeń polityk była wąska, panel nie zawierał pełnego G2, a kryterium premiowało bezpośredni matchup z Germanem. To wyjaśnia pozorne zwycięstwo i regresję B21; problemem nie był simulator, lecz projekt eksperymentu.

Uruchomiono właściwszą kampanię `34466997632`:

- 384 osobniki × 4 iteracje, krzyżowanie i mutacje 120 spójnych bloków sześciogodzinnych;
- siedmiu donorów: V16, German, Kanno-lower oraz najlepsze taśmy Yusuke, Himanshu, SpaTaro i binghua;
- pięć kontroli, w tym **pełny G2 realizowany przez zweryfikowany Rust overlay**;
- zmienne bloki seedów między generacjami i osobny holdout 85000–85031;
- **133120 gier** w 1m35 całego Actions joba.

Wynik: zero kandydatów spełniających ścisłą bramkę per-control. Czysty V16 na holdout: G2 64–0 (+10108.9), B21 47–17 (+9698.3), Kanno-lower 59–5. Nie wyemitowano fałszywego „ulepszenia”. To dowód, że V16 jest lokalnym optimum w przestrzeni statycznych splice, nie że LAB jest niesprawny.

Druga kampania `34467193690` sprawdziła 512 reaktywnych profili rynku na TOP7: 34816 gier. Profil treningowy podnosił score rate 0.574→0.632 i margines +1194→+7047. Jednak niezależny A/B `34467434393`, 2048 fresh gier, obalił go na wszystkich kontrolach: vs German delta −62.5 pp/−8318, B21 −16.0 pp/−4995, Kanno-lower −75.4 pp/−3755, G2 −1.6 pp/−4446. Profil został odrzucony.

Wniosek: dalsze masowe losowanie statycznych bloków lub jednego globalnego profilu nie jest właściwą przestrzenią. Następna warstwa musi wybierać akcje na podstawie bieżącego stanu, popytu sklepów i profilu przeciwnika; LAB pozostaje silnikiem oceny, a nie substytutem sensownej reprezentacji polityki.

## Wynik live V16

Pierwszy odczyt Kaggle ref 56142365 po zaledwie kilku minutach pokazał COMPLETE/publicScore **824.9**, ale nie był wynikiem ustabilizowanym. Użytkownik zaobserwował następnie ponad **1100**, 100% wygranych i gry do około 179 tys. złota; pełna stabilizacja zwykle wymaga 20–30 minut lub dłużej. Nie wolno traktować wczesnego publicScore jako finalnej oceny ani na jego podstawie dyskwalifikować V16. G2 (~2300 według użytkownika) pozostaje mocną kontrolą live, a końcowe wnioski wymagają dojrzałej próbki gier.
