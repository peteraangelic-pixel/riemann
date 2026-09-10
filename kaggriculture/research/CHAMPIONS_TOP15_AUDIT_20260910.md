# V16/V3/V4/V5 kontra pełny TOP15

## Odpowiedź na lukę metodologiczną

Przed tym audytem **nie wykonano porównywalnego pełnego TOP15** dla V3, V4 ani V5. V3 był screenowany na wszystkich epizodach TOP7 i testowany szerzej przeciw wybranym kontrolom; V4/V5 miały kontrole V3/V16/B21/G2-market-overlay/Yusuke/Himanshu. To nie zastępowało TOP15. Użytkownik słusznie wskazał krytyczną lukę.

## Kampania

Workflow `34486377501`:

1. standardowy corpus benchmark na oryginalnym seedzie każdego replaya, wszystkie 105 wybranych polityk TOP15, kandydat na obu miejscach — 210 gier na championa;
2. matched fresh stress: wszystkie 105 polityk × 8 nowych seedów 101000–101007 × oba miejsca × 4 championów — **6720 gier**;
3. zero błędów, natywny Rust.

## Fresh TOP15 — wszystkie wybrane polityki

| agent | W-L | score rate | mean margin | własna nagroda |
|---|---:|---:|---:|---:|
| V16 | 1471–209 | 0.8756 | **+10028** | **90022** |
| V3 | **1510–170** | **0.8988** | +9551 | 89373 |
| V4 | 1449–231 | 0.8625 | +5996 | 83630 |
| V5 | 1455–225 | 0.8661 | +6897 | 84579 |

V3 ma najlepszy ogólny win-rate. V16 ma najwyższy absolutny bank i margines. V5 minimalnie poprawia V4, ale obie hybrydy są słabsze od koherentnych Kanno V16/V3.

## Fresh TOP15 — tylko best-listed submissions

| agent | W-L | score rate | mean margin |
|---|---:|---:|---:|
| V16 | 751–145 | 0.8382 | **+7980** |
| V3 | **793–103** | **0.8850** | +7754 |
| V4 | 731–165 | 0.8158 | +1062 |
| V5 | 732–164 | 0.8170 | +2546 |

## Oryginalne seedy replayów — tylko best-listed

| agent | W-L | score rate | mean margin |
|---|---:|---:|---:|
| V16 | 60–52 | 0.5357 | +980 |
| V3 | **75–37** | **0.6696** | +978 |
| V4 | 67–45 | 0.5982 | −7198 |
| V5 | 67–45 | 0.5982 | −5236 |

## Ukryty przeciwnik, którego zabrakło w LAB-ie

Pełny per-team rozkład ujawnił przyczynę błędu promocji hybryd:

- przeciw **DeeperNet** V16: 90/112 wygranych, +1624;
- V3: **104/112**, +2777;
- V4: **16/112**, −53590;
- V5: **16/112**, −42334.

Jeden pominięty archetyp kompletnie łamie V4/V5 i tłumaczy dużą część słabego transferu V5 live. Panel V3/V16/B21/G2/Yusuke/Himanshu nie reprezentował tej presji. TOP10 maskował problem: V5 miała tam nawet najwyższy score-rate 0.9161; załamanie pojawia się dopiero na pełnym TOP15.

## Matched różnice

Na 1680 identycznych tape/seed/seat przypadkach:

- V16 ma wyższą własną nagrodę od V3 średnio o +649 i lepszy margines o +478 w 1252 przypadkach;
- V3 mimo tego wygrywa więcej binarnych meczów, głównie dzięki Kanno, GermanJurado1 i DeeperNet;
- V5 poprawia V4 średnio o +949 własnej nagrody i +901 marginesu, lecz nie naprawia DeeperNet;
- V16 poprawia V5 o +5442 własnej nagrody i +3131 marginesu.

## Decyzje

- V16 pozostaje championem live (2779.1) i championem absolute economy TOP15.
- V3 jest jedynym niewysłanym kandydatem, dla którego pełny TOP15 daje realny argument, że mógłby konkurować z V16: najlepszy score-rate zarówno fresh, jak i na oryginalnych best-listed replayach.
- V4 i V5 nie zasługują na miejsce przed V3; ich lokalne H2H ukrywa katastrofalny archetyp DeeperNet.
- Każdy kolejny LAB musi mieć pełny TOP15 lub co najmniej zestaw archetypów zawierający DeeperNet jako twardą bramkę. TOP7 i własne wersje nie wystarczają.
- Starszy TOP30 jest obecnie mniej świeży niż TOP15/TOP7 i nie jest dostępny jako bieżący korpus w repo; jego stare agregaty nie zastąpią matched testu nowych agentów.
