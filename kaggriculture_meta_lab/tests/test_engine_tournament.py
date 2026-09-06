from pathlib import Path

from kaggriculture_lab.engine import play_game
from kaggriculture_lab.tournament import build_jobs, run
from kaggriculture_lab.stats import aggregate

ROOT = Path(__file__).resolve().parents[1]


def test_play_game_deterministic():
    # same seed -> identical results (full season)
    a = play_game("starter", "pass", seed=7, steps=720)
    b = play_game("starter", "pass", seed=7, steps=720)
    assert a["error"] is None and b["error"] is None
    assert a["rewards"] == b["rewards"]
    # different seed -> a different game (verified over a full season)
    c = play_game("starter", "starter", seed=8, steps=720)
    d = play_game("starter", "starter", seed=7, steps=720)
    assert c["rewards"] != d["rewards"]


def test_bad_agent_does_not_crash_batch():
    # With debug=False the engine swallows agent exceptions and DONEs the turn;
    # the contract is: play_game never raises and returns a finished game.
    def boom(obs, config):
        raise RuntimeError("kaboom")
    res = play_game(boom, "pass", seed=1, steps=24)
    assert res["error"] is None
    assert res["statuses"] == ["DONE", "DONE"]  # batch survives the bad agent


def test_build_jobs_pairing():
    jobs = build_jobs("cand.py", ["starter", "pass"], games=5,
                      start_seed=1, swap_seats=True, steps=48)
    assert len(jobs) == 2 * 5 * 2  # 2 opponents x 5 seeds x 2 seats
    assert {j[3] for j in jobs} == {0, 1}
    assert all(j[4] == 48 for j in jobs)


def test_tournament_end_to_end_small():
    # Full 720-turn games so the starter can actually out-produce pass.
    jobs = build_jobs("starter", ["pass"], games=2, start_seed=100,
                      swap_seats=True, steps=720)
    rows = run(jobs, workers=2, progress_every=10)
    agg = aggregate(rows)
    assert agg.games == 4 and agg.errors == 0
    assert agg.score_rate >= 0.5  # starter beats a do-nothing agent
