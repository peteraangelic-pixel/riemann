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
    horizontal_hud_mask,
    masked_signature,
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

    def test_hud_mask_ignores_outer_progress_strip_for_state_and_clicks(self) -> None:
        base = [[0 for _ in range(16)] for _ in range(16)]
        base[0][2] = 9  # A visually salient HUD pixel.
        base[4][4] = 8  # A visually salient world object.
        altered = [row[:] for row in base]
        altered[15][5] = 7
        interior_change = [row[:] for row in base]
        interior_change[5][5] = 7
        snapshot = Snapshot("NOT_FINISHED", 0, (COMPLEX_ACTION,), (tuple(map(tuple, base)),))
        hud_only = Snapshot("NOT_FINISHED", 0, (COMPLEX_ACTION,), (tuple(map(tuple, altered)),))
        world_change = Snapshot("NOT_FINISHED", 0, (COMPLEX_ACTION,), (tuple(map(tuple, interior_change)),))

        mask = horizontal_hud_mask(snapshot)
        self.assertIn((2, 0), mask)
        self.assertIn((5, 15), mask)
        self.assertEqual(masked_signature(snapshot, mask), masked_signature(hud_only, mask))
        self.assertNotEqual(masked_signature(snapshot, mask), masked_signature(world_change, mask))
        self.assertEqual(changed_coordinates(snapshot.planes, hud_only.planes, mask), set())
        targets = rank_click_targets(snapshot, excluded=mask)
        self.assertEqual(targets[0][1], (4, 4))
        self.assertTrue(all(point not in mask for _, point, _ in targets))


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

    def test_graph_returns_via_directional_inverse_before_expanding_child(self) -> None:
        policy = ExplorerPolicy()
        start = self._snapshot(actions=("ACTION1", "ACTION2"), grid=((0, 0), (0, 9)))
        middle = self._snapshot(actions=("ACTION1", "ACTION2"), grid=((0, 1), (0, 9)))

        self.assertEqual(policy.choose(start).name, "ACTION1")
        # A fresh directional successor tests its protocol inverse first. This
        # establishes a cheap route home rather than immediately walking deeper.
        self.assertEqual(policy.choose(middle).name, "ACTION2")
        # The shallow parent is reachable again and still has ACTION2 untested.
        self.assertEqual(policy.choose(start).name, "ACTION2")

    def test_graph_replays_route_to_a_scheduled_frontier(self) -> None:
        policy = ExplorerPolicy()
        start = self._snapshot(actions=("ACTION1",), grid=((0, 0), (0, 9)))
        middle = self._snapshot(actions=("ACTION1", "ACTION2"), grid=((0, 1), (0, 9)))
        frontier = self._snapshot(actions=("ACTION1", "ACTION2"), grid=((0, 2), (0, 9)))

        self.assertEqual(policy.choose(start).name, "ACTION1")
        self.assertEqual(policy.choose(middle).name, "ACTION2")  # return to start
        # Start is closed, so replay the known route to the shallow open middle.
        self.assertEqual(policy.choose(start).name, "ACTION1")
        self.assertEqual(policy.choose(middle).name, "ACTION1")
        # The fresh deeper successor similarly establishes its return route.
        self.assertEqual(policy.choose(frontier).name, "ACTION2")
        # Middle is closed; replay its known edge to frontier's remaining action.
        self.assertEqual(policy.choose(middle).name, "ACTION1")

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
        trace = policy.transition_trace()
        self.assertEqual([entry["action"] for entry in trace], ["ACTION1", "ACTION1"])
        self.assertTrue(trace[0]["changed"])
        self.assertTrue(trace[-1]["game_over"])
        self.assertEqual(policy.transition_trace(limit=0), [])

    def test_finalize_accounts_for_last_action_once_without_proposing_again(self) -> None:
        policy = ExplorerPolicy()
        start = self._snapshot(actions=("ACTION1",), grid=((0, 0), (0, 9)))
        final = self._snapshot(actions=("ACTION1",), grid=((0, 1), (0, 9)))
        policy.choose(start)
        policy.finalize(final)
        policy.finalize(final)
        self.assertEqual(policy.diagnostics()["ACTION1"]["attempts"], 1)
        self.assertEqual(len(policy.transition_trace()), 1)
        self.assertTrue(policy.transition_trace()[0]["changed"])

    def test_action_name_catalog_has_every_protocol_action(self) -> None:
        self.assertEqual(ACTION_NAMES, ("RESET", "ACTION1", "ACTION2", "ACTION3", "ACTION4", "ACTION5", "ACTION6", "ACTION7"))


if __name__ == "__main__":
    unittest.main()
