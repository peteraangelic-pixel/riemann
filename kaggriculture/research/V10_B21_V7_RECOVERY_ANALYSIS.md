# B21 versus V7 strict-win recovery analysis

Inputs: `TOP49_ALL5_EPISODES.json` V7 rows and `V10_B21_RATING_FINALISTS_TOP49.json` B21 control rows. Same 245 player-tape records, both seats.

## Summary

- Aggregate: V7 188/490; B21 184/490.
- Changed records: **14**.
- V7-only both-seat wins: **8 records (16 wins)**.
- B21-only both-seat wins: **6 records (12 wins)**.
- Net: V7 +4 wins. The recovery task must not destroy the six B21 gains.

## Changed player-tape records

| Direction | Player | Episode | V7 wins | V7 margin | B21 wins | B21 margin | B21 score |
|---|---|---:|---:|---:|---:|---:|---:|
| V7 only | Andrey Tikhomirov | 106180056 | 2 | +25,779 | 0 | -12,509 | 42,894 |
| V7 only | Kenneth Alonso | 106178365 | 2 | +1,791 | 0 | -81 | 83,784 |
| V7 only | OceanMix | 106178373 | 2 | +22,995 | 0 | -3,143 | 87,629 |
| V7 only | Raya and the Last Dragon | 106181389 | 2 | +944 | 0 | -15,577 | 87,575 |
| V7 only | Tomoki Hirose | 106183152 | 2 | +4,471 | 0 | -2,365 | 114,297 |
| V7 only | elmo | 106180027 | 2 | +5,310 | 0 | -412 | 126,876 |
| V7 only | elmo | 106180659 | 2 | +1,339 | 0 | -4,127 | 85,209 |
| V7 only | liyuting | 106182330 | 2 | +1,685 | 0 | -1,561 | 92,772 |
| B21 only | Andrey Tikhomirov | 106178223 | 0 | -8,929 | 2 | +20,399 | 99,341 |
| B21 only | Dhruvik Chauhan | 106177150 | 0 | -55,695 | 2 | +1,860 | 115,606 |
| B21 only | Dhruvik Chauhan | 106181859 | 0 | -32,333 | 2 | +2,153 | 93,616 |
| B21 only | mandgeee | 106181316 | 0 | -40,869 | 2 | +429 | 69,506 |
| B21 only | yfy | 106177450 | 0 | -1,157 | 2 | +26,894 | 91,439 |
| B21 only | ymg_aq | 106180731 | 0 | -3,222 | 2 | +97,718 | 144,558 |

## Near-loss recovery pool

- Within 500 coins: **3 records**.
- Within 1,000 coins: **7 records**.
- Within 2,500 coins: **27 records / 23 unique underlying episodes**.

| Player | Episode | B21 margin | B21 score | Opponent score |
|---|---:|---:|---:|---:|
| Kenneth Alonso | 106178365 | -81 | 83,784 | 83,865 |
| Mengfei Li | 106180186 | -280 | 57,726 | 58,006 |
| elmo | 106180027 | -412 | 126,876 | 127,288 |
| Beyond | 106180122 | -549 | 130,535 | 131,084 |
| John Doge | 106178292 | -813 | 124,038 | 124,851 |
| Marlubie | 106180186 | -874 | 57,520 | 58,394 |
| Ueddy | 106175612 | -946 | 62,689 | 63,635 |
| 我都先道歉 | 106179828 | -1,047 | 129,936 | 130,983 |
| keiz | 106178578 | -1,128 | 68,778 | 69,906 |
| MtN | 106183227 | -1,148 | 59,421 | 60,569 |
| Tiannan Zhang | 106178266 | -1,182 | 88,738 | 89,920 |
| Beyond | 106180157 | -1,254 | 101,899 | 103,153 |
| John Doge | 106182806 | -1,403 | 72,873 | 74,276 |
| mandgeee | 106180444 | -1,443 | 71,614 | 73,057 |
| CemBas | 106180122 | -1,487 | 130,978 | 132,465 |
| liyuting | 106182330 | -1,561 | 92,772 | 94,333 |
| t-enstar | 106181905 | -1,564 | 42,153 | 43,717 |
| Dresden | 106180123 | -1,667 | 92,762 | 94,429 |
| rian | 106180176 | -1,696 | 56,743 | 58,439 |
| Tomoki Hirose | 106180176 | -1,888 | 56,681 | 58,569 |
| pensukesan | 106183257 | -1,906 | 97,032 | 98,938 |
| Scott Willis | 106182374 | -2,111 | 88,931 | 91,042 |
| Dhruvik Chauhan | 106177290 | -2,187 | 62,344 | 64,531 |
| Andrey Tikhomirov | 106179229 | -2,365 | 70,597 | 72,962 |
| Tomoki Hirose | 106183152 | -2,365 | 114,297 | 116,662 |
| Scott Willis | 106180737 | -2,454 | 99,292 | 101,746 |
| Mengfei Li | 106179828 | -2,478 | 131,994 | 134,472 |

## Next action attribution

For the eight V7-only records and the closest unique near-loss episodes, compare action streams at: opening steps 0-5, first invalid/missing downstream operation, and final liquidation window. Classify opening-state cascade separately from recoverable late sale. Test any patch against the six B21-only gains before promotion.
