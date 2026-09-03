"""Run the local ARC-AGI-3 novelty-explorer against public environments.

This runner uses the official MIT-licensed ARC-AGI-3-Agents framework after it
has been cloned to ``vendor/`` by ``make setup``. It is intentionally separate
from Kaggle submission mode: a local run is an inexpensive debugging signal,
not a leaderboard submission.
"""
from __future__ import annotations

import argparse
import importlib
import logging
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "ARC-AGI-3-Agents"


def prepare_framework() -> None:
    """Copy the current source agent into the generated framework checkout."""
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "prepare_framework.py")],
        check=True,
    )


def load_agent_class():
    if not VENDOR.is_dir():
        raise SystemExit(f"Framework not found at {VENDOR}. Run `make setup` first.")
    prepare_framework()
    sys.path.insert(0, str(VENDOR))
    module = importlib.import_module("agents.templates.my_agent")
    return module.MyAgent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--game",
        default="ls20,vc33",
        help="Comma-separated short game IDs; use --all for every discovered game.",
    )
    parser.add_argument("--all", action="store_true", help="Play all discovered local/remote games.")
    parser.add_argument("--list", action="store_true", help="List discovered games and exit.")
    parser.add_argument("--max-steps", type=int, default=120, help="Per-game action ceiling.")
    parser.add_argument("--record", action="store_true", help="Save JSONL recordings under recordings/.")
    parser.add_argument("--offline", action="store_true", help="Use only already-downloaded game files.")
    args = parser.parse_args()

    if args.max_steps < 1:
        parser.error("--max-steps must be positive")

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    # Optional local ARC_API_KEY lives in ignored .env and unlocks the full
    # public game catalogue. The baseline still works with anonymous access.
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    MyAgent = load_agent_class()

    import arc_agi
    from arc_agi import OperationMode

    mode = OperationMode.OFFLINE if args.offline else OperationMode.NORMAL
    arcade = arc_agi.Arcade(
        operation_mode=mode,
        environments_dir=str(ROOT / "environment_files"),
        recordings_dir=str(ROOT / "recordings"),
    )
    environments = arcade.get_environments()

    if args.list:
        for env in environments:
            print(f"{env.game_id}\t{getattr(env, 'title', '')}")
        return
    if not environments:
        raise SystemExit(
            "No environments available. Run without --offline while connected to the "
            "ARC service, or add the public environment files first."
        )

    known = {env.game_id.split("-", 1)[0] for env in environments}
    requested = {game.strip().split("-", 1)[0] for game in args.game.split(",") if game.strip()}
    game_ids = sorted(known if args.all else known.intersection(requested))
    missing = requested - known if not args.all else set()
    if missing:
        raise SystemExit(f"Unknown/unavailable game IDs: {sorted(missing)}. Try --list.")
    if not game_ids:
        raise SystemExit("No games selected.")

    MyAgent.MAX_ACTIONS = args.max_steps
    results: list[tuple[str, object, int, int]] = []
    for game_id in game_ids:
        print(f"\n=== {game_id} ===")
        env = arcade.make(game_id, save_recording=args.record)
        if env is None:
            print("Could not create environment; skipped.")
            continue
        agent = MyAgent(
            card_id="local-dev",
            game_id=game_id,
            agent_name=f"novelty-v1.{game_id}",
            ROOT_URL="http://localhost",
            record=args.record,
            arc_env=env,
            tags=["local-dev", "novelty-v1"],
        )
        agent.main()
        final = agent.frames[-1]
        results.append((game_id, final.state, final.levels_completed, agent.action_counter))
        print(
            f"state={final.state} levels={final.levels_completed} "
            f"actions={agent.action_counter}"
        )
        print(f"policy evidence={agent.policy.diagnostics()}")

    print("\n=== summary ===")
    for game_id, state, levels, actions in results:
        print(f"{game_id}: state={state}, levels={levels}, actions={actions}")
    scorecard = arcade.get_scorecard()
    if scorecard is not None:
        print(f"local scorecard score={getattr(scorecard, 'score', scorecard)}")


if __name__ == "__main__":
    main()
