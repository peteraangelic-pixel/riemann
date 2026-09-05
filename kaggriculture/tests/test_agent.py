"""Offline tests for the Kaggriculture baseline agent."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent import FarmerPlanner, act  # noqa: E402
from simulate import randomish  # noqa: E402


class AgentContractTests(unittest.TestCase):
    def test_act_returns_valid_action_shape(self) -> None:
        action = act(
            {
                "player": 0,
                "day": 0,
                "step": 0,
                "farms": [
                    {
                        "money": 3000,
                        "farmer": [4, 4],
                        "hands": [],
                        "tiles": [[None] * 10 for _ in range(10)],
                        "unlocked_quadrants": ["NW"],
                        "hires_today": 0,
                    },
                    {
                        "money": 3000,
                        "farmer": [4, 4],
                        "hands": [],
                        "tiles": [[None] * 10 for _ in range(10)],
                        "unlocked_quadrants": ["NW"],
                        "hires_today": 0,
                    },
                ],
                "private": {
                    "shed": {},
                    "seeds": {"WHEAT": 0},
                    "inventories": [{}, {}],
                },
                "market": {"inventory": {}, "prices": {}},
                "town": {"unlocked_shops": []},
            },
            {},
        )
        self.assertEqual(set(action), {"farmer", "hands", "market"})
        self.assertIsInstance(action["farmer"], list)
        self.assertGreater(len(action["farmer"]), 0)
        self.assertIsInstance(action["farmer"][0], str)
        self.assertIsInstance(action["market"], list)

    def test_planner_never_emits_an_unknown_op(self) -> None:
        planner = FarmerPlanner()
        known = {
            "NORTH", "SOUTH", "EAST", "WEST", "PASS",
            "PICKUP", "DROP", "PLANT", "WATER", "HARVEST", "FERTILIZE",
            "BUILD_COOP", "BUILD_PASTURE", "DIG", "PLACE", "FEED",
            "COLLECT_FERTILIZER", "CARE",
        }
        # Play one short, realistic episode and check every emitted farmer op.
        from kaggle_environments import make

        env = make("kaggriculture", configuration={"episodeSteps": 72, "seed": 1})
        env.run([act, act])
        for step in env.steps:
            for agent_state in step:
                action = agent_state.get("action")
                if not action:
                    continue
                op = action["farmer"]
                self.assertIn(op[0], known)
                for order in action["market"]:
                    self.assertIn(order[0], {"BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL", "SELL", "HIRE", "BUY_LAND"})

    def test_episode_is_deterministic_with_same_seed(self) -> None:
        from kaggle_environments import make

        def reward(seed: int) -> tuple[float, float]:
            env = make("kaggriculture", configuration={"episodeSteps": 120, "seed": seed})
            env.run([act, act])
            return env.state[0].reward, env.state[1].reward

        self.assertEqual(reward(42), reward(42))

    def test_randomish_opponent_is_stateless_and_reproducible(self) -> None:
        from kaggle_environments import make

        env = make("kaggriculture", configuration={"episodeSteps": 24, "seed": 7})
        obs = env.state[0].observation
        first = randomish(obs, env.configuration)
        second = randomish(obs, env.configuration)
        self.assertEqual(first, second)

    def test_goose_subsystem_completes_a_productive_cycle(self) -> None:
        from kaggle_environments import make
        from simulate import passive

        env = make("kaggriculture", configuration={"episodeSteps": 240, "seed": 3})
        env.run([act, passive])
        unit_ops: list[list] = []
        market_ops: list[list] = []
        for step in env.steps:
            action = step[0].get("action") or {}
            unit_ops.extend([action.get("farmer") or []] + (action.get("hands") or []))
            market_ops.extend(action.get("market") or [])

        self.assertTrue(any(op[:2] == ["BUY_ANIMAL", "GOOSE"] for op in market_ops))
        for expected in ("BUILD_COOP", "FEED", "CARE", "COLLECT_FERTILIZER"):
            self.assertTrue(any(op and op[0] == expected for op in unit_ops), expected)
        self.assertTrue(any(op[:2] == ["SELL", "EGG"] for op in market_ops))
        self.assertTrue(any(op[:2] == ["SELL", "FERTILIZER"] for op in market_ops))

    def test_baseline_beats_an_idle_farm_over_a_full_season(self) -> None:
        from kaggle_environments import make
        from simulate import passive

        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 5})
        env.run([act, passive])
        mine, idle = env.state[0].reward, env.state[1].reward
        self.assertGreater(mine, idle)


if __name__ == "__main__":
    unittest.main()
