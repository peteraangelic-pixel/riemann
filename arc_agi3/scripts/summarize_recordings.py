"""Create compact, credential-free Markdown sketches from ARC JSONL recordings.

The summary intentionally contains only public grid observations, action labels,
and game IDs. It ignores request headers, service URLs, and free-form reasoning
so it can be attached to a GitHub Actions check for rapid visual regression
review when raw artifact downloads are inconvenient.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

PALETTE = "0123456789ABCDEF"
MAX_SIDE = 64


def _grid_from_frame(frame: Any) -> list[list[int]]:
    """Return the largest valid 2-D plane from a FrameData-style payload."""
    if not isinstance(frame, list) or not frame:
        return []
    planes = frame if isinstance(frame[0], list) and frame[0] and isinstance(frame[0][0], list) else [frame]
    grids: list[list[list[int]]] = []
    for plane in planes:
        if not isinstance(plane, list) or not all(isinstance(row, list) for row in plane):
            continue
        grid: list[list[int]] = []
        for row in plane[:MAX_SIDE]:
            converted: list[int] = []
            for value in row[:MAX_SIDE]:
                try:
                    converted.append(int(value))
                except (TypeError, ValueError):
                    converted.append(-1)
            grid.append(converted)
        grids.append(grid)
    return max(grids, key=lambda grid: sum(len(row) for row in grid), default=[])


def frame_to_text(frame: Any) -> str:
    """Render a palette-indexed plane as deterministic, terminal-safe text."""
    grid = _grid_from_frame(frame)
    if not grid:
        return "<no frame>"
    width = min(MAX_SIDE, max((len(row) for row in grid), default=0))
    lines = []
    for row in grid:
        lines.append(
            "".join(PALETTE[value] if 0 <= value < len(PALETTE) else "?" for value in row).ljust(width, "?")
        )
    return "\n".join(lines)


def _events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        data = event.get("data") if isinstance(event, dict) else None
        if isinstance(data, dict) and _grid_from_frame(data.get("frame")):
            events.append(data)
    return events


def _action_label(event: dict[str, Any]) -> str:
    action = event.get("action_input")
    if not isinstance(action, dict):
        return "initial"
    identifier = action.get("id")
    return "initial" if identifier is None else f"action {identifier}"


def _game_id(events: Iterable[dict[str, Any]], fallback: str) -> str:
    for event in events:
        value = event.get("game_id")
        if value:
            return str(value).split("-", 1)[0]
    return fallback


def summarize_paths(paths: Iterable[Path]) -> str:
    """Render first and last observations from each usable recording by game."""
    by_game: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(paths):
        events = _events(path)
        if not events:
            continue
        game = _game_id(events, path.stem)
        # The framework and SDK can both create a recording. Retain the longer
        # trajectory, which is the most informative one for each public game.
        if len(events) > len(by_game.get(game, [])):
            by_game[game] = events

    if not by_game:
        return "## Recorded frame sketches\n\nNo usable frame recording was produced.\n"

    output = [
        "## Recorded frame sketches",
        "",
        "Palette indices are hexadecimal-like glyphs (`0`–`F`); these are first and final public observations.",
    ]
    for game, events in sorted(by_game.items()):
        selected = [("first", events[0])]
        if len(events) > 1:
            selected.append(("final", events[-1]))
        output.extend(["", f"### {game} ({len(events)} recorded frames)"])
        for label, event in selected:
            output.extend(
                [
                    "",
                    f"**{label}** — {_action_label(event)}, state `{event.get('state', '?')}`, levels `{event.get('levels_completed', '?')}`",
                    "```text",
                    frame_to_text(event.get("frame")),
                    "```",
                ]
            )
    return "\n".join(output) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recordings", type=Path, help="Directory containing JSONL recordings")
    parser.add_argument("--output", type=Path, help="Optional Markdown output path; stdout otherwise")
    args = parser.parse_args()

    summary = summarize_paths(args.recordings.glob("*.jsonl") if args.recordings.is_dir() else ())
    if args.output:
        args.output.write_text(summary, encoding="utf-8")
    else:
        print(summary, end="")


if __name__ == "__main__":
    main()
