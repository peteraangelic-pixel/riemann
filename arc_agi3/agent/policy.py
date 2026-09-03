"""Deterministic, observation-driven exploration policy for ARC-AGI-3.

This module deliberately has no ARC SDK or model dependency.  It turns a frame
into a small, JSON-safe ``Snapshot`` and proposes one legal action.  Keeping the
policy pure Python makes its decision rules unit-testable locally and lets the
Kaggle adapter stay thin.

The policy is a baseline, not a claim of a solved ARC-AGI-3 agent.  Its purpose
is to replace a random-action starter with reproducible exploration that:

* honours the action set advertised by each environment;
* prioritises visually salient click targets over uniform random pixels;
* tracks whether actions changed a state, advanced a level, revisited a state,
  or caused a game-over; and
* avoids repeating the same click in an unchanged state.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from hashlib import blake2b
from math import sqrt
from typing import Any, Iterable, Sequence

RESET = "RESET"
ACTION_NAMES = (RESET, *(f"ACTION{i}" for i in range(1, 8)))
ACTION_SET = frozenset(ACTION_NAMES)
COMPLEX_ACTION = "ACTION6"
DIRECTIONAL_ACTIONS = ("ACTION1", "ACTION2", "ACTION3", "ACTION4")

Grid = tuple[tuple[int, ...], ...]
Planes = tuple[Grid, ...]
Coordinate = tuple[int, int]


@dataclass(frozen=True)
class Snapshot:
    """A dependency-free representation of one ARC observation."""

    state: str
    levels_completed: int
    available_actions: tuple[str, ...]
    planes: Planes

    @property
    def signature(self) -> str:
        """Stable content signature used for state-graph bookkeeping."""
        payload = repr(
            (self.state, self.levels_completed, self.available_actions, self.planes)
        ).encode("utf-8")
        return blake2b(payload, digest_size=12).hexdigest()


@dataclass(frozen=True)
class ActionProposal:
    """An action selected by the pure policy before SDK conversion."""

    name: str
    x: int | None = None
    y: int | None = None
    reasoning: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        if self.name == COMPLEX_ACTION:
            return f"{self.name}:{self.x}:{self.y}"
        return self.name


@dataclass
class ActionStats:
    """Observed consequences of a proposal, accumulated across states."""

    attempts: int = 0
    changed: int = 0
    level_gains: int = 0
    game_overs: int = 0
    revisits: int = 0

    @property
    def noops(self) -> int:
        return self.attempts - self.changed

    def observe(
        self,
        *,
        changed: bool,
        level_gain: int,
        game_over: bool,
        revisit: bool,
    ) -> None:
        self.attempts += 1
        self.changed += int(changed)
        self.level_gains += max(0, level_gain)
        self.game_overs += int(game_over)
        self.revisits += int(revisit)

    def utility(self) -> int:
        """Conservative integer utility for tie-breaking future probes."""
        if not self.attempts:
            return 0
        changed_rate = self.changed / self.attempts
        noop_rate = self.noops / self.attempts
        death_rate = self.game_overs / self.attempts
        revisit_rate = self.revisits / self.attempts
        return int(
            320 * changed_rate
            - 160 * noop_rate
            - 500 * death_rate
            - 90 * revisit_rate
            + 900 * self.level_gains
        )


@dataclass(frozen=True)
class Component:
    """One four-connected region of a same-colour grid."""

    color: int
    cells: tuple[Coordinate, ...]

    @property
    def size(self) -> int:
        return len(self.cells)


def normalize_state(value: Any) -> str:
    """Return an SDK-independent game-state name."""
    raw = getattr(value, "value", value)
    text = str(raw).strip().upper()
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    return text or "NOT_PLAYED"


def normalize_action_name(value: Any) -> str | None:
    """Normalize int, Enum, or string action identifiers to ``ACTIONn``."""
    raw = getattr(value, "name", value)
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        candidate = RESET if raw == 0 else f"ACTION{raw}"
        return candidate if candidate in ACTION_SET else None

    text = str(raw).strip().upper().replace(" ", "")
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    if text.isdigit():
        return normalize_action_name(int(text))
    return text if text in ACTION_SET else None


def normalize_actions(values: Iterable[Any] | None) -> tuple[str, ...]:
    """Return unique action names in the protocol's canonical order."""
    found = {
        normalized
        for value in (values or ())
        if (normalized := normalize_action_name(value)) is not None
    }
    return tuple(name for name in ACTION_NAMES if name in found)


def _as_builtin(value: Any) -> Any:
    """Convert NumPy-like values without making NumPy a project dependency."""
    converter = getattr(value, "tolist", None)
    if callable(converter):
        return converter()
    return value


def _is_sequence(value: Any) -> bool:
    value = _as_builtin(value)
    return isinstance(value, (list, tuple))


def _looks_like_grid(value: Any) -> bool:
    value = _as_builtin(value)
    if not _is_sequence(value):
        return False
    for row in value:
        row = _as_builtin(row)
        if not _is_sequence(row):
            return False
        if any(_is_sequence(cell) for cell in row):
            return False
    return True


def _freeze_grid(value: Any) -> Grid:
    rows = _as_builtin(value)
    frozen_rows: list[tuple[int, ...]] = []
    for row in rows:
        converted: list[int] = []
        for cell in _as_builtin(row):
            try:
                converted.append(int(cell))
            except (TypeError, ValueError):
                converted.append(0)
        frozen_rows.append(tuple(converted))
    return tuple(frozen_rows)


def normalize_planes(value: Any) -> Planes:
    """Normalize a 2-D grid or a list of 2-D grids into immutable planes."""
    value = _as_builtin(value)
    if not _is_sequence(value) or not value:
        return ()
    if _looks_like_grid(value):
        return (_freeze_grid(value),)
    planes = [_freeze_grid(plane) for plane in value if _looks_like_grid(plane)]
    return tuple(planes)


def snapshot_from_frame(frame: Any) -> Snapshot:
    """Build a ``Snapshot`` from an ARC FrameData-like object."""
    return Snapshot(
        state=normalize_state(getattr(frame, "state", "NOT_PLAYED")),
        levels_completed=int(getattr(frame, "levels_completed", 0) or 0),
        available_actions=normalize_actions(getattr(frame, "available_actions", ())),
        planes=normalize_planes(getattr(frame, "frame", ())),
    )


def primary_grid(planes: Planes) -> Grid:
    """Choose the largest plane; ARC frames normally contain exactly one."""
    if not planes:
        return ()
    return max(planes, key=lambda grid: sum(len(row) for row in grid))


def grid_shape(grid: Grid) -> tuple[int, int]:
    """Return maximum width and height, tolerating malformed/jagged grids."""
    return (max((len(row) for row in grid), default=0), len(grid))


def _at(planes: Planes, plane: int, x: int, y: int) -> int | None:
    if plane >= len(planes) or y >= len(planes[plane]) or y < 0 or x < 0:
        return None
    row = planes[plane][y]
    return row[x] if x < len(row) else None


def changed_coordinates(previous: Planes, current: Planes) -> set[Coordinate]:
    """Find visible coordinates whose value changed in any frame plane."""
    changed: set[Coordinate] = set()
    max_planes = max(len(previous), len(current))
    for plane_idx in range(max_planes):
        before = previous[plane_idx] if plane_idx < len(previous) else ()
        after = current[plane_idx] if plane_idx < len(current) else ()
        width = max(grid_shape(before)[0], grid_shape(after)[0])
        height = max(grid_shape(before)[1], grid_shape(after)[1])
        for y in range(height):
            for x in range(width):
                if _at(previous, plane_idx, x, y) != _at(current, plane_idx, x, y):
                    changed.add((x, y))
    return changed


def connected_components(grid: Grid) -> tuple[Component, ...]:
    """Return four-connected same-colour components in deterministic order."""
    width, height = grid_shape(grid)
    seen: set[Coordinate] = set()
    out: list[Component] = []

    for y in range(height):
        for x in range(width):
            if (x, y) in seen or x >= len(grid[y]):
                continue
            color = grid[y][x]
            todo: deque[Coordinate] = deque([(x, y)])
            seen.add((x, y))
            cells: list[Coordinate] = []
            while todo:
                cx, cy = todo.popleft()
                cells.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if (
                        nx < 0
                        or ny < 0
                        or nx >= width
                        or ny >= height
                        or (nx, ny) in seen
                        or nx >= len(grid[ny])
                        or grid[ny][nx] != color
                    ):
                        continue
                    seen.add((nx, ny))
                    todo.append((nx, ny))
            out.append(Component(color=color, cells=tuple(sorted(cells, key=lambda p: (p[1], p[0])))))
    return tuple(out)


def _component_representatives(component: Component) -> tuple[Coordinate, ...]:
    """Produce a few stable in-component targets rather than every pixel."""
    cells = component.cells
    if not cells:
        return ()
    center_x = sum(x for x, _ in cells) / len(cells)
    center_y = sum(y for _, y in cells) / len(cells)
    closest_center = min(
        cells,
        key=lambda point: ((point[0] - center_x) ** 2 + (point[1] - center_y) ** 2, point[1], point[0]),
    )
    points = [closest_center, cells[0], cells[-1]]
    unique: list[Coordinate] = []
    for point in points:
        if point not in unique:
            unique.append(point)
    return tuple(unique)


def _fallback_clicks(width: int, height: int) -> tuple[Coordinate, ...]:
    """A deterministic 4×4 lattice used only when perception has no target."""
    if width <= 0 or height <= 0:
        return ()
    points: list[Coordinate] = []
    fractions = (1, 3, 5, 7)
    for fy in fractions:
        for fx in fractions:
            x = min(width - 1, (fx * width) // 8)
            y = min(height - 1, (fy * height) // 8)
            if (x, y) not in points:
                points.append((x, y))
    for point in ((width // 2, height // 2), (0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
        if point not in points:
            points.append(point)
    return tuple(points)


def rank_click_targets(snapshot: Snapshot, changed: set[Coordinate] | None = None) -> tuple[tuple[int, Coordinate, dict[str, Any]], ...]:
    """Rank likely clickable pixels using rarity, component size, and change.

    It intentionally does not assume a colour palette or a game's mechanics.
    A small non-background component is a better first probe than a uniformly
    random coordinate, while a coordinate that recently changed gains a bonus.
    """
    grid = primary_grid(snapshot.planes)
    width, height = grid_shape(grid)
    if not width or not height:
        return ()

    changed = changed or set()
    cells = [cell for row in grid for cell in row]
    color_counts = Counter(cells)
    background = color_counts.most_common(1)[0][0] if color_counts else 0
    candidates: dict[Coordinate, tuple[int, dict[str, Any]]] = {}

    for component in connected_components(grid):
        # The largest modal region is normally background. Keep it as a weak
        # fallback but strongly prefer compact or colour-rare regions.
        count_for_color = color_counts[component.color]
        component_size = component.size
        rarity = min(700, int(3600 / max(1, count_for_color)))
        compactness = min(700, int(2200 / max(1.0, sqrt(component_size))))
        foreground = 500 if component.color != background else 0
        size_penalty = min(500, max(0, component_size - 32) * 4)
        base_score = max(20, 100 + rarity + compactness + foreground - size_penalty)

        for x, y in _component_representatives(component):
            score = base_score + (1000 if (x, y) in changed else 0)
            reason = {
                "policy": "novelty-explorer-v1",
                "kind": "salient-component",
                "color": component.color,
                "component_size": component_size,
                "recent_change": (x, y) in changed,
            }
            old = candidates.get((x, y))
            if old is None or score > old[0]:
                candidates[(x, y)] = (score, reason)

    for rank, point in enumerate(_fallback_clicks(width, height)):
        score = 120 - rank
        if point in changed:
            score += 1000
        candidates.setdefault(
            point,
            (
                score,
                {
                    "policy": "novelty-explorer-v1",
                    "kind": "lattice-fallback",
                    "recent_change": point in changed,
                },
            ),
        )

    ordered = [
        (score, point, reason)
        for point, (score, reason) in candidates.items()
        if 0 <= point[0] <= 63 and 0 <= point[1] <= 63
    ]
    ordered.sort(key=lambda item: (-item[0], item[1][1], item[1][0]))
    return tuple(ordered)


@dataclass(frozen=True)
class Transition:
    changed: bool
    level_gain: int
    game_over: bool
    revisit: bool


class ExplorerPolicy:
    """State-aware, deterministic exploration policy.

    The policy maintains a very small state graph keyed by frame fingerprints.
    It favours actions that visibly changed a board or advanced a level, then
    probes untried actions. A repeated no-op click is never selected in the
    same visual state.
    """

    def __init__(self) -> None:
        self._previous: Snapshot | None = None
        self._previous_signature: str | None = None
        self._pending: ActionProposal | None = None
        self._last_transition: Transition | None = None
        self._state_visits: Counter[str] = Counter()
        self._global_stats: dict[str, ActionStats] = defaultdict(ActionStats)
        self._state_stats: dict[tuple[str, str], ActionStats] = defaultdict(ActionStats)
        self._tried_clicks: dict[str, set[Coordinate]] = defaultdict(set)
        self._transition_trace: list[dict[str, Any]] = []

    def diagnostics(self) -> dict[str, dict[str, int]]:
        """Return compact, serializable aggregate evidence for a replay."""
        return {
            action: {
                "attempts": stats.attempts,
                "changed": stats.changed,
                "level_gains": stats.level_gains,
                "game_overs": stats.game_overs,
                "revisits": stats.revisits,
            }
            for action, stats in sorted(self._global_stats.items())
        }

    def transition_trace(self, limit: int = 80) -> list[dict[str, Any]]:
        """Return recent action/outcome evidence without retaining grid pixels.

        The compact trace is intended for local and CI smoke reports. It lets a
        replay show which probes changed a state without exporting frames or any
        service credential.
        """
        if limit < 1:
            return []
        return [dict(entry) for entry in self._transition_trace[-limit:]]

    def _observe_transition(self, current: Snapshot, signature: str) -> set[Coordinate]:
        changed: set[Coordinate] = set()
        self._last_transition = None
        if self._previous is None or self._pending is None or self._previous_signature is None:
            return changed

        changed = changed_coordinates(self._previous.planes, current.planes)
        level_gain = current.levels_completed - self._previous.levels_completed
        transition = Transition(
            changed=bool(changed) or level_gain > 0,
            level_gain=max(0, level_gain),
            game_over=current.state == "GAME_OVER",
            revisit=self._state_visits[signature] > 0,
        )
        self._last_transition = transition
        self._global_stats[self._pending.name].observe(
            changed=transition.changed,
            level_gain=transition.level_gain,
            game_over=transition.game_over,
            revisit=transition.revisit,
        )
        self._state_stats[(self._previous_signature, self._pending.key)].observe(
            changed=transition.changed,
            level_gain=transition.level_gain,
            game_over=transition.game_over,
            revisit=transition.revisit,
        )
        self._transition_trace.append(
            {
                "action": self._pending.key,
                "changed": transition.changed,
                "level_gain": transition.level_gain,
                "game_over": transition.game_over,
                "revisit": transition.revisit,
                "next_state": current.state,
                "levels_completed": current.levels_completed,
            }
        )
        return changed

    @staticmethod
    def _simple_priority(name: str) -> int:
        if name in DIRECTIONAL_ACTIONS:
            return 80 - DIRECTIONAL_ACTIONS.index(name) * 5
        if name == "ACTION5":
            return 45
        if name == "ACTION7":
            return -80
        return 0

    def _score_simple(self, signature: str, name: str) -> int:
        key = (signature, name)
        local = self._state_stats[key]
        global_stats = self._global_stats[name]
        score = self._simple_priority(name) + global_stats.utility() + local.utility()
        if local.attempts == 0:
            score += 520
        if self._last_transition and self._pending and self._pending.name == name:
            if self._last_transition.changed and not self._last_transition.game_over:
                # Repeating an action that just moved a player is useful, but
                # less valuable than an explicit level advance.
                score += 350
        return score

    def _best_click(
        self,
        snapshot: Snapshot,
        signature: str,
        changed: set[Coordinate],
    ) -> tuple[int, ActionProposal] | None:
        for salience, (x, y), reason in rank_click_targets(snapshot, changed):
            if (x, y) in self._tried_clicks[signature]:
                continue
            proposal = ActionProposal(
                name=COMPLEX_ACTION,
                x=x,
                y=y,
                reasoning={**reason, "target": [x, y], "salience": salience},
            )
            # Salient objects outrank an untried directional button; generic
            # lattice points do not.
            return 180 + salience, proposal
        return None

    def choose(self, snapshot: Snapshot) -> ActionProposal:
        """Observe ``snapshot`` and return one valid, deterministic proposal."""
        signature = snapshot.signature
        changed = self._observe_transition(snapshot, signature)
        self._state_visits[signature] += 1

        if snapshot.state in {"NOT_PLAYED", "GAME_OVER"}:
            proposal = ActionProposal(
                RESET,
                reasoning={
                    "policy": "novelty-explorer-v1",
                    "kind": "reset",
                    "state": snapshot.state,
                },
            )
            self._remember(snapshot, signature, proposal)
            return proposal

        valid = tuple(action for action in snapshot.available_actions if action != RESET)
        if not valid:
            # The protocol guarantees RESET in terminal states. This defensive
            # fallback prevents an invalid numbered action on a malformed frame.
            proposal = ActionProposal(
                RESET,
                reasoning={"policy": "novelty-explorer-v1", "kind": "no-valid-actions"},
            )
            self._remember(snapshot, signature, proposal)
            return proposal

        candidates: list[tuple[int, int, str, ActionProposal]] = []
        for action in valid:
            if action == COMPLEX_ACTION:
                continue
            score = self._score_simple(signature, action)
            proposal = ActionProposal(
                action,
                reasoning={
                    "policy": "novelty-explorer-v1",
                    "kind": "simple-action",
                    "state_visits": self._state_visits[signature],
                },
            )
            candidates.append((score, 1, action, proposal))

        if COMPLEX_ACTION in valid:
            best_click = self._best_click(snapshot, signature, changed)
            if best_click is not None:
                click_score, click_proposal = best_click
                candidates.append((click_score, 0, click_proposal.key, click_proposal))

        # Every valid set contains either a simple action or ACTION6. The sort
        # makes the policy reproducible when utilities tie (lower action number
        # wins after utility and action kind).
        candidates.sort(
            key=lambda item: (
                -item[0],
                item[1],
                ACTION_NAMES.index(item[3].name),
                item[3].y if item[3].y is not None else -1,
                item[3].x if item[3].x is not None else -1,
            )
        )
        proposal = candidates[0][3]
        self._remember(snapshot, signature, proposal)
        return proposal

    def _remember(self, snapshot: Snapshot, signature: str, proposal: ActionProposal) -> None:
        if proposal.name == COMPLEX_ACTION and proposal.x is not None and proposal.y is not None:
            self._tried_clicks[signature].add((proposal.x, proposal.y))
        self._previous = snapshot
        self._previous_signature = signature
        self._pending = proposal
