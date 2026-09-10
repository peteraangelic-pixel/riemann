# Peer V5 — niezależny audyt i wyczerpująca hybrydyzacja

## Źródło

Audytowany peer head `a6073fe`. V5 powstał już z 11 donorów, w tym trzech artefaktów tej gałęzi: market-parenta, hybrydy z peer V4 i rekonstrukcji peer V4. Nie jest niezależnym konkurentem ignorującym nasze wyniki — jest kolejną generacją wspólnej linii.

Artefakt `champion_tape_evolved_v5.py` został przepisany do konserwatywnego formatu taśmy jako `agents/candidates/peer_v5_evolved.py`; zgodność: 719/719 akcji.

## Mechanizm V5

V5 i nasz poprzedni `ours_peer_v4_hybrid_holdout_winner` mają identyczne farmer i hands na wszystkich 719 krokach. Różnią się tylko **14 krokami market**:

`240, 241, 265, 266, 346, 409, 577, 589, 593, 693, 694, 697, 709, 718`.

To umożliwiło dokładniejsze badanie niż kolejny losowy genetic search: wszystkie **2^14 = 16384** kombinacje cech obu agentów.

## Wyczerpujący LAB

Run `34472814645`:

- 16384 kombinacje;
- etap 1: każda kombinacja przeciw obu rodzicom, oba miejsca;
- etap 2: top 512 przeciw 8 kontrolom;
- holdout: top 32 plus oba rodzice, seedy 99000–99063;
- łącznie **428288 gier** w Rust;
- per-control regression floors.

Wynik: żadna częściowa kombinacja nie przeszła bramki pokonania obu rodziców bez regresji. Wyczerpującym zwycięzcą pozostał pełny zestaw wszystkich 14 zmian V5. Nie wyemitowano fałszywego V6.

Na holdout V5 przeciw naszemu hybrid parentowi: 116–12, +23.3. B21 111–17/+10832, pełny G2 128–0/+6876. Wąski margines nad parentem przy wysokim W/L jest powtarzalny i wynika z drobnych różnic rozliczenia rynku/seatów.

## Niezależna walidacja V5

Run `34473324902`, całkowicie nowe seedy 100000–100255, oba miejsca, 3584 gry, zero błędów:

- vs nasza hybryda: **472–40**, +26.0;
- vs nasz market-parent: **483–29**, +600.5;
- vs peer V4: **479–33**, +381.7;
- vs V3: **490–22**, +1211.3;
- vs B21: **424–88**, +9940.1;
- vs Yusuke: 511–1, +6515.4;
- vs pełny G2: **512–0**, +7238.4.

Peer deklarował 359–25 przeciw hybrydzie na swoich blokach seedów; niezależny blok potwierdził kierunek i skalę score-rate. V5 jest obecnie najlepszym lokalnym artefaktem wspólnej statycznej linii.

## Decyzja

Nie ma uczciwej podstawy do nazwania którejkolwiek z 16383 częściowych mieszanek „lepszą V6”. V5 zawiera wszystkie 14 zmian, które jako komplet dominują naszego parenta; usunięcie dowolnego podzbioru nie dało kandydata przechodzącego pełną bramkę. Następny skok musi rozszerzyć przestrzeń poza binarne cechy rodziców — np. state-gated timing lub nowe akcje — zamiast ponownie tasować te same 14 wartości.
