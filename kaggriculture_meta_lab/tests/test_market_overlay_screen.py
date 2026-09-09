from __future__ import annotations

from scripts.generate_market_overlays import generate_local_profiles, generate_profiles
from scripts.screen_market_overlays import summarize


def test_generation_zero_is_deterministic_unique_and_control_first():
    a = generate_profiles(100, 7)
    assert a == generate_profiles(100, 7)
    assert a[0] == {"enabled": False}
    assert len({repr(sorted(profile.items())) for profile in a}) == 100
    assert all(profile.get("enabled") is True for profile in a[1:])


def test_local_generation_starts_with_disabled_and_enabled_identity():
    profiles = generate_local_profiles(200, 11)
    assert profiles[:2] == [{"enabled": False}, {"enabled": True}]
    assert profiles == generate_local_profiles(200, 11)
    assert len({repr(sorted(profile.items())) for profile in profiles}) == 200
    assert all(2 <= len(profile) <= 5 for profile in profiles[2:])
    assert all(profile["start_day"] >= 8 for profile in profiles[2:])


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
