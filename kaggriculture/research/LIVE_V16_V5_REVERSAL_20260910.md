# Live V16/V5 — odwrócenie rankingu lokalnego

Odczyt wykonany 2026-09-10 13:47 UTC przez Kaggle API.

| submission | ref | status | publicScore |
|---|---:|---|---:|
| V16, czysty Kanno ep107384200 | 56142365 | COMPLETE | **2779.1** |
| V5, evolved shared champion | 56143699 | COMPLETE | **1868.8** |

Użytkownik raportuje 91. miejsce i srebrny medal, wobec pozycji >1700 kilka godzin wcześniej. Najwyższy wynik jest związany z V16.

## Najważniejszy eksperyment naturalny

Lokalnie V5 pokonywał bezpośrednio najlepsze artefakty obu gałęzi:

- 472–40 przeciw naszej hybrydzie na niezależnych seedach;
- 512–0 przeciw kontroli nazwanej G2;
- 424–88 przeciw B21;
- pełne 2^14 kombinacji V5/hybryda potwierdziło V5 jako lokalne optimum.

Live kolejność jest odwrotna: V16 przewyższa V5 o **910.3 ratingu**. To nie jest mały szum ani problem wczesnego odczytu: obie submisje mają COMPLETE, V16 działa ponad 3 godziny, V5 prawie 2 godziny. Rating nadal może dryfować, ale skala różnicy wymaga zmiany metodologii.

## Co różni polityki

V5 względem V16:

- farmer różni się tylko na 1/719 kroku;
- hands różnią się tylko na 1/719 kroku;
- market różni się na **115/719 krokach**, rozsianych od openingu do endgame;
- V3 różnił się od V16 wyłącznie na 84 krokach market.

Zatem głównym podejrzanym nie jest German opening jednostek, lecz ewoluowany, posklejany harmonogram rynku. Lokalny LAB konsekwentnie optymalizował interakcję ze wspólnym rynkiem panelu statycznych taśm. Live populacja ma inną podaż, popyt i timing; przewaga antagonistyczna przeciw kontrolom nie jest przewagą populacyjną.

## Korekta nazewnictwa G2

„Pełny G2” w lokalnych raportach oznaczał statyczną taśmę Subina plus dokładnie zweryfikowany **market overlay G2**. Nie jest to oryginalna pełna reaktywna polityka jednostek G2. Od teraz kontrolę należy nazywać `G2-market-overlay control`, nie „pełny reaktywny G2”. Jej 512–0 nie gwarantuje transferu live.

## Dlaczego czysty V16 transferuje

V16 jest kompletną, koherentną trajektorią jednego rzeczywistego meczu polityki Kanno o publicScore źródła około 2975.9. Zachowuje współzależności produkcji, zapasów i rynku z demonstracji. V5 zachowuje prawie te same jednostki, ale miesza decyzje rynku wybrane pod lokalnych przeciwników. Lokalny H2H premiuje eksploatację konkretnej podaży przeciwnika; live premiuje odporność na rozkład całej populacji.

## Nowe reguły promocji

1. Koherentny replay źródłowy o wysokim live jest silniejszym priorem niż lokalny Frankenstein.
2. Nie promować market splice na podstawie H2H ze statycznymi taśmami, nawet przy setkach tysięcy gier.
3. Oddzielać `absolute economy` od `shared-market denial`; raportować własne złoto, nie tylko margines.
4. Panel musi zawierać przeciwników generujących różne rozkłady podaży, a nie kilka wariantów tej samej rodziny taśm.
5. Zmiany rynku powinny być state-gated względem bieżących cen/inventory, nie przypisane na sztywno do kroku.
6. Kolejna V6 powinna zachować koherentny rdzeń V16 i dodawać małe, odwracalne reakcje. German/Kanno crossover nie jest już bazą domyślną.
7. Live A/B ma pierwszeństwo przed lokalnym H2H przy wyborze championa.

## Decyzja

V16 jest aktualnym championem live. V5 pozostaje wartościowym negatywnym eksperymentem i nie powinna zastępować V16 mimo lokalnej dominacji. Jej wynik wyznacza koszt overfitu LAB-a do statycznego wspólnego rynku.
