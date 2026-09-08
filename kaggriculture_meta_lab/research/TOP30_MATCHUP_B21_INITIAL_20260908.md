# B21/S16 kontra TOP30 — pierwszy replay matchup

Data: 2026-09-08. Kandydat: `agents/current/agent_v9_b21_s16.py`.
Źródło: 30 replayów (po 5) z TOP30. Test wykonano na oryginalnych seedach,
w oryginalnym seat, przeciwko zapisanej akcji przeciwnika.

## Wynik dla sześciu najwyższych profili

| Profil | W-L | Średni margin kandydata |
|---|---:|---:|
| SpaTaro | 5-0 | +44 185 |
| Otter Vibe | 5-0 | +71 894 |
| binghua | 5-0 | +58 141 |
| Mengfei Li | 5-0 | +51 081 |
| Matthew Huang | 5-0 | +61 857 |
| Tarang222 | 5-0 | +73 657 |

Łącznie: **30-0**, bez błędów.

## Krytyczne zastrzeżenie

To nie jest dowód, że B21 pokonałby te submissiony closed-loop. To jest
**open-loop replay diagnostic**: zapisane akcje TOP30 nie reagują na to, że
kandydat zmienił rynek, zapasy i ceny. Wysokie dodatnie marginesy pokazują, że
B21 potrafi bardzo dobrze wykorzystać przeciwnika, gdy ten kontynuuje starą
trajektorię, ale mogą również oznaczać, że akcje przeciwnika stają się
nieoptymalne lub częściowo nielegalne po zmianie stanu.

Dlatego ten test służy przede wszystkim do odpowiedzi „gdzie zapisany profil
przegrywa”, a nie „jaki ma closed-loop win rate”.

## Co mimo to jest użyteczne

- wszystkie sześć rodzin daje B21 duży margines w replayu;
- nie ma podstaw, by ślepo kopiować high-turnover SpaTaro albo delayed-sale
  Otter Vibe;
- następnym krokiem jest porównanie stanów i pierwszej materialnej dywergencji,
  nie kolejny ranking W/L;
- jeżeli B21 wygrywa open-loop tak wysoko, a ranking TOP30 jest wysoki, to
  prawdopodobnie przewaga TOP30 zależy od reakcji na aktualny rynek, a nie od
  samej zapisanej sekwencji.

## Następny eksperyment

1. Uruchomić ten sam matchup dla wszystkich 30 profili.
2. Zapisać snapshoty cash/inventory/market co 10–24 kroki.
3. Znaleźć pierwszy krok, gdzie różnica przekracza ustalony próg.
4. Zbudować uproszczone polityki closed-loop z rodzin TOP30, nie z pojedynczych
   taśm.
5. Dopiero wtedy porównywać je z B21 i v12 na świeżych seedach.

Reprodukcja:

```bash
python scripts/top30_matchup.py /path/to/extracted/TOP30 \
  --team SpaTaro --team "Otter Vibe" --team binghua
```
