"""Tests for the SDK-free ARC-AGI-3 exploration policy."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))

from policy import (  # noqa: E402
    ACTION_NAMES,
    COMPLEX_ACTION,
    RESET,
    ExplorerPolicy,
    Snapshot,
    changed_coordinates,
    connected_components,
    normalize_action_name,
    normalize_actions,
    normalize_planes,
    rank_click_targets,
    snapshot_from_frame,
)


class PolicyHelpersTests(unittest.TestCase):
    def test_normalizes_protocol_actions(self) -> None:
        self.assertEqual(normalize_action_name(0), RESET)
        self.assertEqual(normalize_action_name(6), COMPLEX_ACTION)
        self.assertEqual(normalize_action_name("GameAction.ACTION3"), "ACTION3")
        self.assertIsNone(normalize_action_name(99))
        self.assertIsNone(normalize_action_name(True))
        self.assertEqual(
            normalize_actions([6, "ACTION1", 1, "GameAction.ACTION7", 99]),
            ("ACTION1", "ACTION6", "ACTION7"),
        )

    def test_normalizes_2d_and_multi_plane_frames(self) -> None:
        single = normalize_planes([[1, 2], [3, 4]])
        multi = normalize_planes([[[1, 2]], [[3, 4]]])
        self.assertEqual(single, (((1, 2), (3, 4)),))
        self.assertEqual(multi, (((1, 2),), ((3, 4),)))

        frame = SimpleNamespace(
            state=SimpleNamespace(value="NOT_FINISHED"),
            levels_completed=2,
            available_actions=[1, 6],
            frame=[[[0, 9], [0, 0]]],
        )
        snapshot = snapshot_from_frame(frame)
        self.assertEqual(snapshot.state, "NOT_FINISHED")
        self.assertEqual(snapshot.levels_completed, 2)
        self.assertEqual(snapshot.available_actions, ("ACTION1", "ACTION6"))
        self.assertEqual(snapshot.planes, (((0, 9), (0, 0)),))

    def test_components_and_diffs_are_deterministic(self) -> None:
        grid = ((0, 0, 9), (0, 1, 9))
        components = connected_components(grid)
        self.assertEqual([(component.color, component.size) for component in components], [(0, 3), (9, 2), (1, 1)])
        before = (grid,)
        after = (((0, 2, 9), (0, 1, 9)),)
        self.assertEqual(changed_coordinates(before, after), {(1, 0)})

    def test_salience_prefers_a_small_non_background_object(self) -> None:
        snapshot = Snapshot(
            state="NOT_FINISHED",
            levels_completed=0,
            available_actions=(COMPLEX_ACTION,),
            planes=(((0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 9), (0, 0, 0, 0)),),
        )
        targets = rank_click_targets(snapshot)
        self.assertTrue(targets)
        _, coordinate, reason = targets[0]
        self.assertEqual(coordinate, (3, 2))
        self.assertEqual(reason["kind"], "salient-component")
        self.assertEqual(reason["color"], 9)


class ExplorerPolicyTests(unittest.TestCase):
    @staticmethod
    def _snapshot(
        state: str = "NOT_FINISHED",
        actions: tuple[str, ...] = ("ACTION1", "ACTION2", "ACTION6"),
        grid: tuple[tuple[int, ...], ...] = ((0, 0, 0), (0, 9, 0), (0, 0, 0)),
        levels: int = 0,
    ) -> Snapshot:
        return Snapshot(state, levels, actions, (grid,))

    def test_resets_unplayed_and_game_over(self) -> None:
        policy = ExplorerPolicy()
        initial = self._snapshot(state="NOT_PLAYED", actions=())
        self.assertEqual(policy.choose(initial).name, RESET)
        self.assertEqual(policy.choose(self._snapshot(state="GAME_OVER", actions=())).name, RESET)

    def test_only_emits_advertised_action(self) -> None:
        policy = ExplorerPolicy()
        snapshot = self._snapshot(actions=("ACTION3",))
        proposal = policy.choose(snapshot)
        self.assertEqual(proposal.name, "ACTION3")

    def test_clicks_salient_target_then_does_not_repeat_same_click_on_noop(self) -> None:
        policy = ExplorerPolicy()
        snapshot = self._snapshot(actions=(COMPLEX_ACTION,))
        first = policy.choose(snapshot)
        second = policy.choose(snapshot)  # ACTION6 had no visible effect.
        self.assertEqual(first.name, COMPLEX_ACTION)
        self.assertEqual((first.x, first.y), (1, 1))
        self.assertEqual(second.name, COMPLEX_ACTION)
        self.assertNotEqual((second.x, second.y), (first.x, first.y))
        diagnostics = policy.diagnostics()[COMPLEX_ACTION]
        self.assertEqual(diagnostics["attempts"], 1)
        self.assertEqual(diagnostics["changed"], 0)

    def test_records_level_progress_and_death(self) -> None:
        policy = ExplorerPolicy()
        start = self._snapshot(actions=("ACTION1",), levels=0)
        policy.choose(start)
        progressed = self._snapshot(actions=("ACTION1",), levels=1, grid=((0, 1, 0), (0, 9, 0), (0, 0, 0)))
        policy.choose(progressed)
        died = self._snapshot(state="GAME_OVER", actions=(), levels=1, grid=((0, 1, 0), (0, 9, 0), (0, 0, 0)))
        self.assertEqual(policy.choose(died).name, RESET)
        stats = policy.diagnostics()["ACTION1"]
        self.assertEqual(stats["attempts"], 2)
        self.assertEqual(stats["level_gains"], 1)
        self.assertEqual(stats["game_overs"], 1)

    def test_action_name_catalog_has_every_protocol_action(self) -> None:
        self.assertEqual(ACTION_NAMES, ("RESET", "ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5", "ACTION6", "ACTION7"))


if __name__ == "__main__":
    unittest.main()
