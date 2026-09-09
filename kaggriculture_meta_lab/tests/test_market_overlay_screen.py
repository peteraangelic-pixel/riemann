from __future__ import annotations

from scripts.generate_market_overlays import generate_profiles
from scripts.screen_market_overlays import summarize


def test_generation_zero_is_deterministic_unique_and_control_first():
    a = generate_profiles(100, 7)
    assert a == generate_profiles(100, 7)
    assert a[0] == {"enabled": False}
    assert len({repr(sorted(profile.items())) for profile in a}) == 100
    assert all(profile.get("enabled") is True for profile in a[1:])


def test_team_balanced_summary_does_not_overweight_more_records():
    rows = [
        ({"rewards": [2, 1], "errors": []}, {"team": "A"}),
        ({"rewards": [2, 1], "errors": []}, {"team": "A"}),
        ({"rewards": [0, 1], "errors": []}, {"team": "B"}),
    ]
    out = summarize(rows)
    assert out["score_rate"] == 2 / 3
    assert out["team_balanced_score"] == 0.5
    assert out["worst_team_score"] == 0.0


def test_failed_games_are_rejected():
    try:
        summarize([({"rewards": None, "errors": ["boom"]}, {"team": "A"})])
    except RuntimeError as exc:
        assert "failed" in str(exc)
    else:
        raise AssertionError("failed game entered ranking")
