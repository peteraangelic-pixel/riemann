# TOP7 latest leaders audit

Źródło: `TOP7.7z` z `arena/01a0712c-riemann`, 7 teams × 12 replayów.
Archiwum rozpakowane lokalnie i przeanalizowane opisowo.

## Ranking w archiwum

```text
1 SpaTaro          3055.3
2 Himanshu Kumar   3022.1
3 Otter Vibe       2988.5
4 binghua          2980.6
5 デワンシュ       2978.8
6 kanno            2972.3
7 Yusuke Hayashi   2965.7
```

To jest świeższy i bardziej wymagający snapshot niż wcześniejszy TOP15.
Nie zastępuje TOP15 jako corpus bez pełnego audytu, ale jest bardzo dobrym
fresh/near-live diagnostic i holdoutem rozwojowym.

## Pierwszy census akcji

Średnie na 12 replayów na teamie:

| Team | buy | sell | HIRE | animal orders | fertilizer orders | first SELL |
|---|---:|---:|---:|---:|---:|---:|
| Himanshu Kumar | 268.8 | 406.9 | 263.3 | 12.0 | 126.3 | 1 |
| Otter Vibe | 85.2 | 206.2 | 279.4 | 11.3 | 59.8 | 38.4 |
| SpaTaro | 507.2 | 306.2 | 280.2 | 11.9 | 42.1 | 9.4 |
| Yusuke Hayashi | 274.0 | 411.2 | 263.5 | 12.2 | 119.8 | 1 |
| binghua | 218.9 | 240.0 | 298.0 | 11.8 | 80.6 | 31.4 |
| kanno | 267.8 | 469.0 | 262.6 | 12.1 | 127.7 | 1 |
| デワンシュ | 275.2 | 555.3 | 262.8 | 12.0 | 128.4 | 1 |

## Co jest nowe względem wcześniejszego TOP15

1. **SpaTaro ma najwyższy rating 3055.3**, ale jego profil nadal jest
   high-turnover: około 507 buy, 306 sell, pierwsza sprzedaż około t9.
2. **Himanshu/Yusuke/kanno/デワンシュ** tworzą rodzinę bardzo aktywnej
   produkcji: pierwsza sprzedaż na t1, około 263 HIRE i 407–555 sell.
3. **Otter/binghua** pozostają rodziną delayed/pośrednią, z pierwszą sprzedażą
   około t31–38.
4. Wszystkie zespoły mają około 11–12 zakupów zwierząt, ale mocno różnią się
   fertilizer orders. To wzmacnia hipotezę, że nawóz i timing produkcji są
   ważniejsze niż sam animal count.
5. TOP7 ma świeższy lider signal niż poprzedni TOP15: SpaTaro wzrósł do 3055.3,
   Himanshu do 3022.1. Nie należy trenować wyłącznie na starym rankingu.

## Decyzja strategiczna

Nie wybieramy między GermanJurado1 a hybrydą jako alternatywnymi „mistrzami”.
Role są różne:

```text
GermanJurado1 corrected tape = strongest verified open-loop control
G2 = strongest live submission control in current observations
G4 = negative structural/open-loop control until live collapse is explained
hybrid = experiment, currently rejected as weaker than pure tape
TOP7 = fresh leader corpus and stress/holdout diagnostic
```

Następne testy powinny porównywać GermanJurado1 i G2 na TOP7, ale nie jako
proof of adaptation. Dodatkowo trzeba wyciągnąć z TOP7 rodziny plannerów:

```text
SpaTaro        high-turnover
Himanshu/Yusuke/kanno/デワンシュ active-production + fertilizer
Otter/binghua  delayed/late-sale
```

Każdą rodzinę testować osobno, z tym samym seedem i oboma seatami.
