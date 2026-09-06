"""Statistical primitives: Wilson CI, result aggregation, promotion gate.

The competition's final ranking is a Bradley-Terry model over head-to-head
episodes between *active* agents. Local decisions must therefore be based on
**win rate against a strong opponent pool, from both seats**, with a confidence
interval - not on mean cash. A mutation is promoted only when the lower bound of
its 95% Wilson interval clears 0.5 (score rate) across enough games.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, asdict
from typing import Any


def wilson(successes: float, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Two-sided Wilson score interval for a (possibly fractional) proportion."""
    if trials <= 0:
        return (0.0, 0.0)
    successes = max(0.0, min(float(trials), float(successes)))
    phat = successes / trials
    z2 = z * z
    denom = 1.0 + z2 / trials
    centre = (phat + z2 / (2.0 * trials)) / denom
    half = z * math.sqrt(phat * (1.0 - phat) / trials + z2 / (4.0 * trials * trials)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


@dataclass
class Aggregate:
    games: int = 0
    wins: int = 0
    losses: int = 0
    ties: int = 0
    errors: int = 0
    win_rate: float = 0.0
    score_rate: float = 0.0
    ci_low: float = 0.0
    ci_high: float = 0.0
    mean_margin: float = 0.0
    median_margin: float = 0.0
    p10_margin: float = 0.0
    mean_self: float = 0.0
    mean_opp: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def aggregate(rows: list[dict[str, Any]]) -> Aggregate:
    """Aggregate result rows. Rows with outcome=='error' are counted but excluded
    from win/margin stats (they usually mean the agent threw)."""
    good = [r for r in rows if r.get("outcome") in ("win", "loss", "tie")]
    n = len(good)
    wins = sum(r["outcome"] == "win" for r in good)
    losses = sum(r["outcome"] == "loss" for r in good)
    ties = n - wins - losses
    errors = len(rows) - n
    margins = [float(r.get("margin", 0.0)) for r in good]
    score = wins + 0.5 * ties
    lo, hi = wilson(score, n)
    margins_sorted = sorted(margins)
    p10 = margins_sorted[max(0, int(0.10 * len(margins_sorted)) - 1)] if margins_sorted else 0.0
    return Aggregate(
        games=n, wins=wins, losses=losses, ties=ties, errors=errors,
        win_rate=wins / n if n else 0.0,
        score_rate=score / n if n else 0.0,
        ci_low=lo, ci_high=hi,
        mean_margin=statistics.mean(margins) if margins else 0.0,
        median_margin=statistics.median(margins) if margins else 0.0,
        p10_margin=p10,
        mean_self=statistics.mean([float(r.get("self_reward", 0.0)) for r in good]) if good else 0.0,
        mean_opp=statistics.mean([float(r.get("opp_reward", 0.0)) for r in good]) if good else 0.0,
    )


def bradley_terry(wins: dict[tuple[str, str], float],
                  games: dict[tuple[str, str], int],
                  labels: list[str], iters: int = 500, eps: float = 0.5) -> dict[str, float]:
    """Bradley-Terry MLE strengths (ties count 0.5), smoothed with a weak prior."""
    rating = {l: 1.0 for l in labels}
    for _ in range(iters):
        new: dict[str, float] = {}
        for i in labels:
            num = eps
            den = 0.0
            for j in labels:
                if i == j:
                    continue
                num += wins.get((i, j), 0.0)
                tot = games.get((i, j), 0) + games.get((j, i), 0)
                if tot > 0:
                    den += tot / (rating[i] + rating[j])
            den += eps * sum(1.0 / (rating[i] + rating[j]) for j in labels if j != i)
            new[i] = num / den if den else rating[i]
        logmean = sum(math.log(max(v, 1e-12)) for v in new.values()) / len(new)
        rating = {k: max(v, 1e-12) / math.exp(logmean) for k, v in new.items()}
    return rating


def promotion_gate(agg: Aggregate, min_games: int = 200, ci_threshold: float = 0.5,
                   max_errors: int = 0) -> tuple[bool, list[str]]:
    """Decide whether a candidate is safe to promote over the baseline pool.

    Returns (passed, reasons). A mutation passes only if it has enough games,
    the lower 95% Wilson bound on score rate beats 0.5, mean margin is positive,
    and there are no crashes.
    """
    reasons: list[str] = []
    ok = True
    if agg.errors > max_errors:
        ok = False
        reasons.append(f"{agg.errors} error games (agent threw / timed out)")
    if agg.games < min_games:
        ok = False
        reasons.append(f"only {agg.games} games (< {min_games})")
    if agg.ci_low <= ci_threshold:
        ok = False
        reasons.append(f"95% CI low {agg.ci_low*100:.1f}% <= {ci_threshold*100:.0f}% "
                       f"(score rate {agg.score_rate*100:.1f}%)")
    if agg.mean_margin <= 0:
        ok = False
        reasons.append(f"mean margin {agg.mean_margin:.0f} <= 0")
    if ok:
        reasons.append(f"PASS: {agg.wins}W/{agg.losses}L/{agg.ties}T, "
                       f"score {agg.score_rate*100:.1f}% (CI {agg.ci_low*100:.1f}-"
                       f"{agg.ci_high*100:.1f}), margin +{agg.mean_margin:.0f}")
    return ok, reasons
