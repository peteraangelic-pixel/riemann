# TOP15 — pierwszy census akcji wykonany na VM

Źródło: `TOP15.7z`, 15 graczy × 7 replayów. Dla każdego replayu policzono
akcje seat-u należącego do danego zespołu. To jest analiza opisowa, nie jeszcze
screen closed-loop.

## Najważniejszy podział strategii

TOP15 nie jest jedną polityką. Widać co najmniej trzy rodziny:

### Otter Vibe — opóźniona sprzedaż i mniejszy turnover

- public rank 1, score 2987.0;
- około 88 buy i 217 sell;
- około 280 HIRE;
- około 11 zakupów zwierząt;
- pierwsza sprzedaż średnio około t37.

To jest nadal delayed-sale, ale bardzo świeży i obecnie najwyżej sklasyfikowany
profil. Powinien być osobnym anchor-em, nie tylko wariantem Subin.

### SpaTaro — wysoki turnover

- rank 2, score 2984.1;
- około 497 buy i 300 sell;
- około 281 HIRE;
- pierwsza sprzedaż około t8;
- około 15 zakupów zwierząt.

To potwierdza, że wysoki turnover jest realną rodziną, ale nie można go łączyć
bezwarunkowo z delayed-sale.

### Himanshu/pensukesan/cooked/kanno/Terry/German/DeeperNet/
ultimatum — aktywna produkcja

Większość tej rodziny ma:

- około 260–276 buy;
- około 424–553 sell;
- około 259–269 HIRE;
- około 12 zakupów zwierząt;
- pierwszą sprzedaż na t1–6, z wyjątkiem późniejszych odchyleń.

To jest szeroka rodzina wysokiej aktywności i dużej liczby sprzedaży.

### binghua i Mengfei Li — profile pośrednie/delayed

- binghua: około 208 buy, 234 sell, 304 HIRE, pierwsza sprzedaż około t32;
- Mengfei Li: około 135 buy, 239 sell, 275 HIRE, pierwsza sprzedaż około t2.

Te profile powinny służyć jako kontrast dla Otter/SpaTaro.

## Nowe hipotezy do LAB

1. **TOP5 → TOP10 → TOP15** jest lepszym curriculum niż TOP10 → TOP20 →
   TOP30, bo nie rozmywa świeżego sygnału liderów.
2. Otter Vibe wymaga osobnego delayed-sale anchoru. Nie zakładamy, że Subin
   jest jego substytutem.
3. SpaTaro wymaga osobnego high-turnover anchoru.
4. Rodzina aktywnej produkcji powinna być testowana z wcześniejszą sprzedażą,
   większą liczbą HIRE i innym miks-em zwierząt.
5. Średnia liczba zakupów nawozu sama nie wyjaśnia przewagi — trzeba porównać
   timing oraz sprzedaż nawozu.
6. `first_sell` i turnover muszą być genami/cechami osobnymi. Nie łączymy ich
   w jeden parametr.

## Ograniczenia

To jest pierwszy census z surowych replayów wykonany na VM. Nie dowodzi jeszcze
przyczynowości, nie rozdziela wszystkich submission IDs tego samego zespołu i
nie zastępuje testu closed-loop. Następny etap powinien generować overlaye i
profile wokół trzech anchorów:

```text
Otter Vibe — delayed-sale
SpaTaro — high-turnover
Himanshu/pensukesan — active-production
```

Każdy anchor musi przejść TOP5, TOP10, TOP15, stary TOP30 oraz świeży holdout.
