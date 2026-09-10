# Peer V4 × własny market champion — hybrydowy LAB

## Wejścia

- Peer head `d38e5b7`, V4 z commita `5842819`: GermanJurado1 przez dni 0–8, następnie Kanno V3 przez dni 9–29.
- Własny parent: `v3_market_genetic_holdout_winner.py`, czysty Kanno V3 farmer/hands z ewoluowanym timingiem rynku.
- Rekonstrukcja peer V4 została zweryfikowana: 719/719 akcji identycznych z `_ACTIONS` peer artefaktu.

## Bezpośrednie porównanie rodziców

Na holdout 96000–96063, oba miejsca: własny parent kontra peer V4 dał 64–64; peer miał średnią przewagę +321.8. To nie jest czysta dominacja W/L: wynik zależy od fizycznego miejsca, dlatego wymagane jest parowanie obu seatów. Peer wnosi German opening, własny parent lepszy timing rynku i wyższy margines przeciw G2.

## Przestrzeń hybryd

Genom zawierał:

- punkt przejścia German→Kanno: dzień 0–12;
- 120 niezależnych bloków rynku po 6 godzin;
- dla każdego bloku wybór rynku: własny evolved market, peer V4 albo czysty V3.

Kontrole każdej generacji: oba rodzice, V3, V16, German, B21, pełny G2 i Yusuke; zmienne seedy oraz oba miejsca.

## Pierwszy przebieg — poprawnie odrzucony

Run `34470636941`, 288768 gier. Znalazł hybrydę bijącą oba rodzice, lecz traciła względem rodziców około 3199/g przeciw B21. Nie została wyemitowana. To wykazało, że H2H rodziców nie może być pierwszym kryterium selekcji.

## Drugi przebieg — fitness z regression floors

Fitness zmieniono tak, by najpierw chronił per-control score-rate i margines względem słabszego wyniku obu rodziców, a dopiero później maksymalizował H2H. Run `34470885258`, kolejne 288768 gier.

Zwycięzca:

- German farmer/hands przez dni 0–4, Kanno od dnia 5;
- market: 70 bloków własnego parenta, 39 peer V4, 11 czystego V3;
- holdout 96000–96063: 122–6/+690 przeciw własnemu parentowi i 119–9/+358 przeciw peer V4;
- B21 104–24/+9354, G2 128–0/+7065;
- przeszedł bramkę i został zapisany jako `agents/candidates/ours_peer_v4_hybrid_holdout_winner.py`.

## Niezależna duża bramka

Run `34471140543`, seedy 97000–97255, oba miejsca, 10240 gier, zero błędów:

- bezpośrednio vs własny parent: **485–27**, +523.6;
- bezpośrednio vs peer V4: **481–31**, +350.5;
- vs V3: 493–19, +964.6;
- vs V16: 509–3, +2401.9;
- vs German: 503–9, +1405.5;
- vs B21: 432–80, +10246.4;
- vs Yusuke: 511–1, +6411.0;
- vs pełny G2: 512–0, +7181.3.

Względem peer V4 hybryda poprawia margines na każdej kontroli (+101 German, +247 B21, +213 G2). Względem własnego parenta poprawia H2H i większość kontroli, ale świadomie wymienia część marginesu G2 (−1840) na opening odporniejszy przeciw rodzinie V3/V16/German; score-rate G2 pozostaje 1.0. Ścisła bramka rodzinna przeszła.

## Decyzja

To najlepszy lokalny hybrydowy kandydat z obu linii, ale nie jest jeszcze automatycznie championem live ani submissionem. Zachowujemy osobno własny market parent jako specjalistę z większym marginesem G2. O wyborze do Kaggle powinien zdecydować ustabilizowany wynik V16 i cel: maksymalna ogólna odporność (hybryda) albo większy margines przeciw G2 (market parent).
