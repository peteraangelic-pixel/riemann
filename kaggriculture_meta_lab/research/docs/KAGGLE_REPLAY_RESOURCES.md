# Kaggle replay resources reviewed 2026-09-06

## Scheduled notebook

`https://www.kaggle.com/code/ashok205/top10-replay-dataset-archive`

Useful and real. The notebook is scheduled daily and maintains an append-only archive. It reads the official episodes index, scans replay headers for team names, ranks teams using daily rating evidence, stores complete replay bodies for selected top teams, and deletes large temporary daily ZIPs.

Confirmed dataset slug from the notebook:

`ashok205/kaggriculture-top10-replay-archive`

The earlier `nnmax/...` suggestion in one transcript was incorrect.

## Discussion

`https://www.kaggle.com/competitions/kaggriculture/discussion/737764`

Useful as the announcement and canonical link to the notebook/dataset. It recommends adjusting `TOP_N` and scheduling daily updates. It contains no additional strategy result beyond those resources.

## How to use it

- Download daily snapshots and retain dates/fingerprints so strategy evolution is measurable.
- Select diverse strategy clusters, not only many near-duplicate episodes from current rank 1.
- Feed replay tapes into open-loop regression and contrastive loss mining.
- Do not call them closed-loop opponents unless executable public agent code is available.
- Keep large archives outside Git or compressed according to existing repository conventions.
