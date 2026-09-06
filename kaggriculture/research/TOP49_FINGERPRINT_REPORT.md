# TOP49 compact replay fingerprint report

- Player records: **245** (49 players × 5)
- Unique episodes: **196**; cross-folder duplicates: **49**
- Fingerprint dimensions: **327**
- Selected exploratory clusters: **3**

## Cluster-selection diagnostics

| k | silhouette | SSE |
|---:|---:|---:|
| 2 | 0.683 | 4188.2 |
| 3 | 0.560 | 3569.2 |
| 4 | 0.538 | 3030.2 |
| 5 | 0.424 | 2455.1 |
| 6 | 0.310 | 1850.5 |
| 7 | 0.299 | 1577.5 |
| 8 | 0.292 | 1464.5 |
| 9 | 0.320 | 1238.5 |
| 10 | 0.328 | 1025.7 |

## Policy-family clusters

### Cluster 0 (contains Aastik)

Aastik Rajan15, Agent 0, Andrey Tikhomirov, Ant, Beyond, CemBas, Crop Dusta, Dhruvik Chauhan, Dresden, Driz Lo, Foxure, JamesJJJJJ, Jiro2, John Doge, Kenneth Alonso, KongKongDe, LI Mufeng, Marlubie, Mengfei Li, Milan Leonard, MtN, OceanMix, Raya and the Last Dragon, SJY321, Scott Willis, Suliman Tadros, Syed Asad Ali, THIRD FARM CLUB, Tiannan Zhang, Tomoki Hirose, Ueddy, daulettoibazar, elmo, hana87hana, keiz, liyuting, mandgeee, mikelou1, peikopon, pensukesan, rian, sunyuxiang136, t-enstar, taiseiu, tetsuya & yuanzhe zhou, yfy, ymg_aq

### Cluster 1

我都先道歉

### Cluster 2

get some fries

## Distinct and internally stable discovery shortlist

This list excludes already-tested Crop Dusta and keiz. Distance is from the Aastik family; lower instability means the player's five samples agree more closely.

| player | distance from Aastik | within-player instability | nearest policy |
|---|---:|---:|---|
| 我都先道歉 | 38.48 | 0.59 | Ueddy (35.35) |
| Ant | 13.79 | 5.00 | Dresden (6.51) |
| JamesJJJJJ | 12.60 | 5.68 | taiseiu (2.97) |
| taiseiu | 11.53 | 5.90 | Beyond (2.84) |
| Raya and the Last Dragon | 10.00 | 5.15 | Dhruvik Chauhan (6.49) |
| Scott Willis | 7.91 | 4.16 | KongKongDe (5.41) |
| tetsuya & yuanzhe zhou | 5.83 | 6.13 | elmo (2.81) |
| Mengfei Li | 4.88 | 1.21 | Marlubie (2.32) |
| elmo | 4.52 | 4.31 | pensukesan (0.52) |
| John Doge | 4.40 | 2.60 | daulettoibazar (4.11) |

## Important limitations

- generic export has null final scores/winners
- product labels and quantities were lost by the generic action parser
- only turns 0-24 have state snapshots
- clusters are discovery aids, not evidence that a policy beats V8

The shortlist identifies where full-replay retrieval and executable tape reconstruction should begin. It does not justify modifying or submitting V8.
