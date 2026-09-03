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
    TileMazeNavigator,
    changed_coordinates,
    connected_components,
    horizontal_hud_mask,
    masked_signature,
    normalize_action_name,
    normalize_actions,
    normalize_planes,
    optimistic_tile_path,
    rank_click_targets,
    snapshot_from_frame,
    tile_maze_view,
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

    @staticmethod
    def _tile_maze_snapshot(
        avatar: tuple[int, int] = (6, 8),
        *,
        levels: int = 0,
        goal_halo: bool = False,
    ) -> Snapshot:
        """Make a visual-only 12×12 navigation fixture with no game ID hint."""
        grid = [[4 for _ in range(64)] for _ in range(64)]

        def paint(cell: tuple[int, int], rows: tuple[int, ...]) -> None:
            x = 4 + 5 * cell[0]
            y = 5 * cell[1]
            for row, color in enumerate(rows):
                for column in range(5):
                    grid[y + row][x + column] = color

        # Two non-uniform landmarks; the striped avatar renders over either
        # landmark when it arrives, as an ordinary sprite layer would.
        paint((3, 6), (3, 3, 0, 1, 3))
        paint((6, 2), (5, 9, 5, 9, 5))
        if goal_halo:
            for cell in ((5, 1), (6, 1), (7, 1), (5, 2), (7, 2), (5, 3), (6, 3), (7, 3)):
                paint(cell, (5, 9, 5, 9, 5))
        paint(avatar, (12, 12, 9, 9, 9))
        return Snapshot("NOT_FINISHED", levels, ("ACTION1", "ACTION2", "ACTION3", "ACTION4"), (tuple(map(tuple, grid)),))

    @staticmethod
    def _token_maze_snapshot(
        avatar: tuple[int, int],
        *,
        turns_to_target: int,
        walls: frozenset[tuple[int, int]] = frozenset(),
    ) -> Snapshot:
        """Make a generic badge/control/target fixture with arbitrary colours."""
        grid = [[4 for _ in range(64)] for _ in range(64)]

        def paint(cell: tuple[int, int], glyph: tuple[tuple[int, ...], ...]) -> None:
            x = 4 + 5 * cell[0]
            y = 5 * cell[1]
            for row, values in enumerate(glyph):
                grid[y + row][x : x + 5] = values

        def rotate(glyph: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
            return tuple(tuple(glyph[4 - x][y] for x in range(5)) for y in range(5))

        target = (
            (5, 5, 5, 5, 5),
            (5, 9, 9, 9, 5),
            (5, 9, 5, 5, 5),
            (5, 9, 5, 9, 5),
            (5, 5, 5, 5, 5),
        )
        badge = target
        for _ in range((-turns_to_target) % 4):
            badge = rotate(badge)
        control = (
            (4, 4, 4, 4, 4),
            (4, 0, 4, 4, 4),
            (4, 4, 1, 1, 4),
            (4, 4, 1, 4, 4),
            (4, 4, 4, 4, 4),
        )
        for wall in walls:
            paint(wall, ((8,) * 5,) * 5)
        paint((7, 2), target)
        paint((3, 6), control)
        paint(avatar, ((12,) * 5, (12,) * 5, (9,) * 5, (9,) * 5, (9,) * 5))
        for y in range(5):
            for x in range(5):
                value = badge[y][x]
                for dy in range(2):
                    for dx in range(2):
                        grid[53 + 2 * y + dy][1 + 2 * x + dx] = value
        return Snapshot(
            "NOT_FINISHED",
            0,
            ("ACTION1", "ACTION2", "ACTION3", "ACTION4"),
            (tuple(map(tuple, grid)),),
        )

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

    def test_tile_maze_view_finds_striped_avatar_and_landmark_centres(self) -> None:
        view = tile_maze_view(self._tile_maze_snapshot())
        self.assertIsNotNone(view)
        assert view is not None
        self.assertEqual(view.avatar, (6, 8))
        self.assertEqual(view.shape, (12, 12))
        self.assertIn((3, 6), [representative for representative, _ in view.landmarks])
        self.assertIn((6, 2), [representative for representative, _ in view.landmarks])

    def test_tile_maze_view_matches_edge_badge_to_rotated_board_target(self) -> None:
        view = tile_maze_view(self._token_maze_snapshot((5, 6), turns_to_target=3))
        self.assertIsNotNone(view)
        assert view is not None
        self.assertEqual(view.control_tiles, ((3, 6),))
        self.assertEqual(
            [(target.coordinate, target.quarter_turns) for target in view.token_targets],
            [((7, 2), 3)],
        )

    def test_tile_maze_navigator_cycles_a_control_until_badge_matches_target(self) -> None:
        navigator = TileMazeNavigator()
        # The token initially needs three visually inferred quarter turns. A
        # successful entry changes it to two, then local exits/re-entries cycle
        # it without any fixed game-specific press count.
        self.assertEqual(
            navigator.choose(self._token_maze_snapshot((4, 6), turns_to_target=3)).name,
            "ACTION3",
        )
        self.assertEqual(
            navigator.choose(self._token_maze_snapshot((3, 6), turns_to_target=2)).name,
            "ACTION4",
        )
        self.assertEqual(
            navigator.choose(self._token_maze_snapshot((4, 6), turns_to_target=2)).name,
            "ACTION3",
        )
        self.assertEqual(
            navigator.choose(self._token_maze_snapshot((3, 6), turns_to_target=1)).name,
            "ACTION4",
        )
        self.assertEqual(
            navigator.choose(self._token_maze_snapshot((4, 6), turns_to_target=1)).name,
            "ACTION3",
        )
        toward_goal = navigator.choose(self._token_maze_snapshot((3, 6), turns_to_target=0))
        self.assertIsNotNone(toward_goal)
        assert toward_goal is not None
        self.assertEqual(toward_goal.reasoning["kind"], "tile-badge-navigation")
        self.assertEqual(toward_goal.reasoning["target"], [7, 2])

    def test_tile_maze_navigator_generalizes_a_confirmed_uniform_collision_style(self) -> None:
        snapshot = self._token_maze_snapshot(
            (4, 6),
            turns_to_target=3,
            walls=frozenset({(5, 6), (5, 5)}),
        )
        view = tile_maze_view(snapshot)
        self.assertIsNotNone(view)
        assert view is not None
        navigator = TileMazeNavigator()
        # A previous successful departure exposed uniform style 4 as walkable.
        # The next attempted move stays in place at a differently styled tile.
        navigator._last_avatar = (4, 6)  # noqa: SLF001 - transition setup
        navigator._last_action = "ACTION4"  # noqa: SLF001 - transition setup
        navigator._last_view = view  # noqa: SLF001 - transition setup
        navigator._traversable_uniform_values.add(4)  # noqa: SLF001
        navigator._observe_avatar(view)  # noqa: SLF001 - test visual evidence update
        self.assertIn(8, navigator._blocked_uniform_values)  # noqa: SLF001
        self.assertIn((5, 6), navigator._known_blocked(view))  # noqa: SLF001
        self.assertIn((5, 5), navigator._known_blocked(view))  # noqa: SLF001
        self.assertNotIn((4, 6), navigator._known_blocked(view))  # noqa: SLF001

    def test_optimistic_tile_path_replans_around_a_learned_collision(self) -> None:
        direct = optimistic_tile_path((6, 8), (3, 6), (12, 12), set())
        self.assertEqual(direct, ("ACTION3", "ACTION3", "ACTION3", "ACTION1", "ACTION1"))
        blocked = optimistic_tile_path((6, 8), (3, 6), (12, 12), {(5, 8)})
        self.assertIsNotNone(blocked)
        assert blocked is not None
        self.assertEqual(blocked[0], "ACTION1")
        self.assertNotIn("ACTION6", blocked)

    def test_tile_maze_navigator_marks_a_reached_switch_before_next_landmark(self) -> None:
        navigator = TileMazeNavigator()
        # The initial nearest landmark is the switch at (3, 6).
        self.assertEqual(navigator.choose(self._tile_maze_snapshot()).name, "ACTION3")
        for avatar in ((5, 8), (4, 8), (3, 8), (3, 7)):
            self.assertIsNotNone(navigator.choose(self._tile_maze_snapshot(avatar)))
        next_target = navigator.choose(self._tile_maze_snapshot((3, 6)))
        self.assertIsNotNone(next_target)
        assert next_target is not None
        self.assertEqual(next_target.reasoning["target"], [6, 2])

    def test_tile_maze_navigator_does_not_finish_on_goal_halo_periphery(self) -> None:
        navigator = TileMazeNavigator()
        goal = frozenset((x, y) for x in (5, 6, 7) for y in (1, 2, 3))
        # Keep the target established from an earlier observation. The avatar
        # has reached its lower visual halo, not the central enterable tile.
        navigator._active = ((6, 2), goal)  # noqa: SLF001 - state-machine regression setup
        proposal = navigator.choose(self._tile_maze_snapshot((6, 3), goal_halo=True))
        self.assertIsNotNone(proposal)
        assert proposal is not None
        self.assertEqual(proposal.name, "ACTION1")
        self.assertEqual(proposal.reasoning["target"], [6, 2])

    def test_policy_uses_tile_maze_navigation_only_when_the_visual_contract_matches(self) -> None:
        policy = ExplorerPolicy()
        proposal = policy.choose(self._tile_maze_snapshot())
        self.assertEqual(proposal.name, "ACTION3")
        self.assertEqual(proposal.reasoning["kind"], "tile-maze-navigation")
        self.assertEqual(proposal.reasoning["target"], [3, 6])

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
