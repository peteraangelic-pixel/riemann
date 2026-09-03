"""Deterministic, graph-driven exploration policy for ARC-AGI-3.

This module deliberately has no ARC SDK or model dependency.  It turns a frame
into a small, JSON-safe ``Snapshot`` and proposes one legal action.  Keeping the
policy pure Python makes its decision rules unit-testable locally and lets the
Kaggle adapter stay thin.

The policy is a baseline, not a claim of a solved ARC-AGI-3 agent.  Its purpose
is to replace a random-action starter with reproducible exploration that:

* honours the action set advertised by each environment;
* prioritises visually salient click targets over uniform random pixels;
* learns local obstacles while navigating visually recognized tile mazes;
* tracks whether actions changed a state, advanced a level, revisited a state,
  or caused a game-over; and
* avoids repeating the same click in an unchanged state.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from hashlib import blake2b
from heapq import heappop, heappush
from math import sqrt
from typing import Any, Iterable, Sequence

RESET = "RESET"
ACTION_NAMES = (RESET, *(f"ACTION{i}" for i in range(1, 8)))
ACTION_SET = frozenset(ACTION_NAMES)
COMPLEX_ACTION = "ACTION6"
DIRECTIONAL_ACTIONS = ("ACTION1", "ACTION2", "ACTION3", "ACTION4")
# The standard directional protocol forms two inverse pairs.  Treating a newly
# discovered movement edge as reversible first lets the explorer expand a state
# graph breadth-first rather than walking one action direction into every
# corridor before trying its siblings.  The observed successor still decides
# whether the inverse actually returns, so this remains safe for games with
# one-way mechanics.
INVERSE_DIRECTIONAL_ACTION = {
    "ACTION1": "ACTION2",
    "ACTION2": "ACTION1",
    "ACTION3": "ACTION4",
    "ACTION4": "ACTION3",
}

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


def changed_coordinates(
    previous: Planes,
    current: Planes,
    excluded: set[Coordinate] | frozenset[Coordinate] | None = None,
) -> set[Coordinate]:
    """Find coordinates changed in any plane, optionally ignoring HUD cells."""
    changed: set[Coordinate] = set()
    excluded = excluded or frozenset()
    max_planes = max(len(previous), len(current))
    for plane_idx in range(max_planes):
        before = previous[plane_idx] if plane_idx < len(previous) else ()
        after = current[plane_idx] if plane_idx < len(current) else ()
        width = max(grid_shape(before)[0], grid_shape(after)[0])
        height = max(grid_shape(before)[1], grid_shape(after)[1])
        for y in range(height):
            for x in range(width):
                if (x, y) in excluded:
                    continue
                if _at(previous, plane_idx, x, y) != _at(current, plane_idx, x, y):
                    changed.add((x, y))
    return changed


def horizontal_hud_mask(snapshot: Snapshot) -> frozenset[Coordinate]:
    """Mask conservative top/bottom HUD bands on normal-sized ARC frames.

    ARC game frames commonly contain a changing progress/step strip along an
    outer horizontal edge. Treating that strip as world state makes a blocked
    move appear novel and breaks graph revisits. Small synthetic grids are left
    untouched; on a 64×64 frame only the outer four rows at each horizontal
    edge are excluded.
    """
    width, height = grid_shape(primary_grid(snapshot.planes))
    if width < 12 or height < 12:
        return frozenset()
    band = min(4, max(1, height // 16))
    return frozenset(
        (x, y)
        for y in (*range(band), *range(height - band, height))
        for x in range(width)
    )


def masked_signature(snapshot: Snapshot, excluded: set[Coordinate] | frozenset[Coordinate]) -> str:
    """Hash an observation after replacing known HUD coordinates with ``-1``."""
    masked_planes = tuple(
        tuple(
            tuple(-1 if (x, y) in excluded else cell for x, cell in enumerate(row))
            for y, row in enumerate(grid)
        )
        for grid in snapshot.planes
    )
    payload = repr(
        (snapshot.state, snapshot.levels_completed, snapshot.available_actions, masked_planes)
    ).encode("utf-8")
    return blake2b(payload, digest_size=12).hexdigest()


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


def rank_click_targets(
    snapshot: Snapshot,
    changed: set[Coordinate] | None = None,
    excluded: set[Coordinate] | frozenset[Coordinate] | None = None,
) -> tuple[tuple[int, Coordinate, dict[str, Any]], ...]:
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
    excluded = excluded or frozenset()
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
            if (x, y) in excluded:
                continue
            score = base_score + (1000 if (x, y) in changed else 0)
            reason = {
                "policy": "novelty-explorer-v4",
                "kind": "salient-component",
                "color": component.color,
                "component_size": component_size,
                "recent_change": (x, y) in changed,
            }
            old = candidates.get((x, y))
            if old is None or score > old[0]:
                candidates[(x, y)] = (score, reason)

    for rank, point in enumerate(_fallback_clicks(width, height)):
        if point in excluded:
            continue
        score = 120 - rank
        if point in changed:
            score += 1000
        candidates.setdefault(
            point,
            (
                score,
                {
                    "policy": "novelty-explorer-v4",
                    "kind": "lattice-fallback",
                    "recent_change": point in changed,
                },
            ),
        )

    ordered = [
        (score, point, reason)
        for point, (score, reason) in candidates.items()
        if 0 <= point[0] <= 63 and 0 <= point[1] <= 63 and point not in excluded
    ]
    ordered.sort(key=lambda item: (-item[0], item[1][1], item[1][0]))
    return tuple(ordered)

TILE_SIZE = 5
# Canonical control semantics used by ARC's directional protocol.  The order is
# only a deterministic tie-break for an optimistic path; observed movement is
# what adds a location to the learned obstacle map.
MAZE_DIRECTION_DELTAS: dict[str, Coordinate] = {
    "ACTION1": (0, -1),
    "ACTION2": (0, 1),
    "ACTION3": (-1, 0),
    "ACTION4": (1, 0),
}
MAZE_ACTION_ORDER = ("ACTION3", "ACTION1", "ACTION4", "ACTION2")


@dataclass(frozen=True)
class TileMazeView:
    """A conservative visual view of a regular tile-navigation board.

    This recognizer is deliberately opt-in: it requires a 5×5 two-colour
    striped avatar and all four directional controls.  It does not inspect a
    game ID or assume a particular colour palette.  ``landmarks`` are compact
    non-uniform tile clusters that can be reached as potential switches/goals.
    """

    avatar: Coordinate
    shape: tuple[int, int]
    landmarks: tuple[tuple[Coordinate, frozenset[Coordinate]], ...]


def _tile(grid: Grid, x: int, y: int) -> tuple[tuple[int, ...], ...] | None:
    """Return one complete ``TILE_SIZE`` square, or ``None`` at an edge."""
    if x < 0 or y < 0 or y + TILE_SIZE > len(grid):
        return None
    rows = grid[y : y + TILE_SIZE]
    if any(x + TILE_SIZE > len(row) for row in rows):
        return None
    return tuple(tuple(row[x : x + TILE_SIZE]) for row in rows)


def _striped_avatar_origins(grid: Grid) -> tuple[Coordinate, ...]:
    """Find rare, full 5×5 two-colour horizontal stripe glyphs.

    An avatar is learned from geometry rather than a colour ID: every row in
    its glyph is solid, exactly two colours form contiguous horizontal bands,
    and neither is the board's dominant background.  This is intentionally
    stricter than general component detection so ordinary colourful UI does not
    seize control from the graph explorer.
    """
    width, height = grid_shape(grid)
    if width < TILE_SIZE or height < TILE_SIZE:
        return ()
    counts = Counter(cell for row in grid for cell in row)
    if not counts:
        return ()
    background = counts.most_common(1)[0][0]
    candidates: list[tuple[int, int, int]] = []
    for y in range(height - TILE_SIZE + 1):
        for x in range(width - TILE_SIZE + 1):
            glyph = _tile(grid, x, y)
            if glyph is None or any(len(set(row)) != 1 for row in glyph):
                continue
            row_colours = tuple(row[0] for row in glyph)
            colours = set(row_colours)
            if len(colours) != 2 or background in colours:
                continue
            if sum(left != right for left, right in zip(row_colours, row_colours[1:])) != 1:
                continue
            # The rarest valid striped glyph is the most likely movable actor.
            candidates.append((sum(counts[colour] for colour in colours), y, x))
    return tuple((x, y) for _, y, x in sorted(candidates))


def _tile_groups(points: set[Coordinate]) -> tuple[frozenset[Coordinate], ...]:
    """Group four-connected landmark tiles deterministically."""
    groups: list[frozenset[Coordinate]] = []
    remaining = set(points)
    while remaining:
        seed = min(remaining, key=lambda point: (point[1], point[0]))
        remaining.remove(seed)
        group = {seed}
        queue: deque[Coordinate] = deque([seed])
        while queue:
            x, y = queue.popleft()
            for neighbour in ((x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)):
                if neighbour not in remaining:
                    continue
                remaining.remove(neighbour)
                group.add(neighbour)
                queue.append(neighbour)
        groups.append(frozenset(group))
    return tuple(groups)


def _group_representative(group: frozenset[Coordinate]) -> Coordinate:
    """Choose a central, stable target coordinate for a landmark cluster."""
    mean_x = sum(x for x, _ in group) / len(group)
    mean_y = sum(y for _, y in group) / len(group)
    return min(
        group,
        key=lambda point: ((point[0] - mean_x) ** 2 + (point[1] - mean_y) ** 2, point[1], point[0]),
    )


def tile_maze_view(snapshot: Snapshot) -> TileMazeView | None:
    """Recognize a regular directional tile maze from one visual observation."""
    if not set(DIRECTIONAL_ACTIONS).issubset(snapshot.available_actions):
        return None
    grid = primary_grid(snapshot.planes)
    width, height = grid_shape(grid)
    if width < 8 * TILE_SIZE or height < 8 * TILE_SIZE:
        return None
    avatars = _striped_avatar_origins(grid)
    if not avatars:
        return None
    avatar_x, avatar_y = avatars[0]
    offset_x, offset_y = avatar_x % TILE_SIZE, avatar_y % TILE_SIZE
    origins_x = tuple(range(offset_x, width - TILE_SIZE + 1, TILE_SIZE))
    origins_y = tuple(range(offset_y, height - TILE_SIZE + 1, TILE_SIZE))
    if len(origins_x) < 8 or len(origins_y) < 8:
        return None
    avatar = ((avatar_x - offset_x) // TILE_SIZE, (avatar_y - offset_y) // TILE_SIZE)

    # A non-uniform grid tile is a possible game object.  Adjacent tiles are
    # clustered because a goal marker may span several tiles around its actual
    # enterable centre.  Fully uniform tiles are deliberately not guessed as
    # walls: unsuccessful moves learn collisions safely from observations.
    special: set[Coordinate] = set()
    for tile_y, origin_y in enumerate(origins_y):
        for tile_x, origin_x in enumerate(origins_x):
            glyph = _tile(grid, origin_x, origin_y)
            if glyph is None:
                continue
            if len({cell for row in glyph for cell in row}) > 1:
                special.add((tile_x, tile_y))

    landmarks: list[tuple[Coordinate, frozenset[Coordinate]]] = []
    for group in _tile_groups(special):
        if avatar in group:
            continue
        landmarks.append((_group_representative(group), group))
    landmarks.sort(key=lambda item: (item[0][1], item[0][0]))
    if not landmarks:
        return None
    return TileMazeView(avatar=avatar, shape=(len(origins_x), len(origins_y)), landmarks=tuple(landmarks))


def optimistic_tile_path(
    start: Coordinate,
    target: Coordinate,
    shape: tuple[int, int],
    blocked: set[Coordinate] | frozenset[Coordinate],
) -> tuple[str, ...] | None:
    """Plan through observed-free and as-yet-unseen tiles with deterministic A*."""
    if start == target:
        return ()
    width, height = shape
    sequence = 0
    queue: list[tuple[int, int, int, int, Coordinate, tuple[str, ...]]] = []
    costs: dict[Coordinate, int] = {start: 0}
    heappush(
        queue,
        (abs(start[0] - target[0]) + abs(start[1] - target[1]), 0, 0, sequence, start, ()),
    )
    while queue:
        _, cost, _, _, point, path = heappop(queue)
        if cost != costs.get(point):
            continue
        if point == target:
            return path
        for rank, action in enumerate(MAZE_ACTION_ORDER):
            dx, dy = MAZE_DIRECTION_DELTAS[action]
            neighbour = (point[0] + dx, point[1] + dy)
            if (
                neighbour in blocked
                or neighbour[0] < 0
                or neighbour[1] < 0
                or neighbour[0] >= width
                or neighbour[1] >= height
            ):
                continue
            next_cost = cost + 1
            if next_cost >= costs.get(neighbour, next_cost + 1):
                continue
            costs[neighbour] = next_cost
            sequence += 1
            heuristic = abs(neighbour[0] - target[0]) + abs(neighbour[1] - target[1])
            heappush(
                queue,
                (next_cost + heuristic, next_cost, rank, sequence, neighbour, path + (action,)),
            )
    return None


class TileMazeNavigator:
    """Learn collisions online while steering to visible interior landmarks.

    It is a small navigation primitive, not a game-specific route: a failed
    directional move records one blocked tile, then optimistic A* replans.  A
    reached landmark is not selected again in the same episode, which makes a
    nearby switch naturally precede a farther revealed target.  Any missing
    avatar/modal frame resets this short-lived model and hands control back to
    the general graph explorer.
    """

    def __init__(self) -> None:
        self._blocked: set[Coordinate] = set()
        self._visited: set[Coordinate] = set()
        self._active: tuple[Coordinate, frozenset[Coordinate]] | None = None
        self._last_avatar: Coordinate | None = None
        self._last_action: str | None = None
        self._levels_completed: int | None = None

    def reset(self) -> None:
        """Forget episode-local geometry after terminal or modal feedback."""
        self._blocked.clear()
        self._visited.clear()
        self._active = None
        self._last_avatar = None
        self._last_action = None
        self._levels_completed = None

    def _observe_avatar(self, view: TileMazeView) -> None:
        if self._last_avatar is None or self._last_action is None:
            return
        dx, dy = MAZE_DIRECTION_DELTAS[self._last_action]
        expected = (self._last_avatar[0] + dx, self._last_avatar[1] + dy)
        if view.avatar == self._last_avatar:
            self._blocked.add(expected)
        elif view.avatar != expected:
            # A teleport, moving platform, or a changed tile scale invalidates
            # a one-step model.  Rebuild it from this ordinary observation.
            self._blocked.clear()
            self._visited.clear()
            self._active = None

    @staticmethod
    def _interior_landmarks(view: TileMazeView) -> tuple[tuple[Coordinate, frozenset[Coordinate]], ...]:
        width, height = view.shape
        interior = tuple(
            landmark
            for landmark in view.landmarks
            if 1 <= landmark[0][0] < width - 1 and 1 <= landmark[0][1] < height - 2
        )
        return interior or view.landmarks

    def choose(self, snapshot: Snapshot) -> ActionProposal | None:
        """Return one legal tile-navigation action, or ``None`` to use graph fallback."""
        view = tile_maze_view(snapshot)
        if view is None:
            self.reset()
            return None
        if self._levels_completed is not None and snapshot.levels_completed != self._levels_completed:
            self.reset()
        self._levels_completed = snapshot.levels_completed
        self._observe_avatar(view)

        if self._active is not None and view.avatar in self._active[1]:
            self._visited.add(self._active[0])
            self._active = None

        active = self._active
        path: tuple[str, ...] | None = None
        if active is not None:
            path = optimistic_tile_path(view.avatar, active[0], view.shape, self._blocked)
            if path is None:
                self._active = None

        if self._active is None:
            candidates: list[tuple[int, int, int, Coordinate, frozenset[Coordinate], tuple[str, ...]]] = []
            for representative, cells in self._interior_landmarks(view):
                if representative in self._visited or view.avatar in cells:
                    continue
                candidate_path = optimistic_tile_path(view.avatar, representative, view.shape, self._blocked)
                if candidate_path is None:
                    continue
                candidates.append(
                    (
                        len(candidate_path),
                        abs(view.avatar[0] - representative[0]) + abs(view.avatar[1] - representative[1]),
                        representative[1],
                        representative,
                        cells,
                        candidate_path,
                    )
                )
            if not candidates:
                self._last_avatar = view.avatar
                self._last_action = None
                return None
            _, _, _, representative, cells, path = min(candidates)
            self._active = (representative, cells)

        if not path:
            # A target that became the current tile is handled on the next
            # observation; do not invent an action merely to make progress.
            self._last_avatar = view.avatar
            self._last_action = None
            return None
        action = path[0]
        self._last_avatar = view.avatar
        self._last_action = action
        return ActionProposal(
            action,
            reasoning={
                "policy": "novelty-explorer-v4",
                "kind": "tile-maze-navigation",
                "target": list(self._active[0]) if self._active is not None else [],
                "path_length": len(path),
                "learned_blocked_tiles": len(self._blocked),
            },
        )


@dataclass(frozen=True)
class Transition:
    """Observed result of one state-action transition."""

    changed: bool
    level_gain: int
    game_over: bool
    revisit: bool


@dataclass
class GraphEdge:
    """A deterministic action edge discovered between semantic game states."""

    proposal: ActionProposal
    successor: str | None = None
    transition: Transition | None = None


@dataclass
class StateNode:
    """Lazily generated action frontier for one semantic game state."""

    actions: tuple[ActionProposal, ...]
    # Discovery depth supplies a stable, low-action-cost traversal order when
    # several graph frontiers are reachable from the current observation.
    depth: int = 0
    tried: set[str] = field(default_factory=set)


class ExplorerPolicy:
    """Deterministic frontier explorer over visually canonicalized states.

    The policy records every attempted state-action edge before observing its
    result. A strict visual tile-maze recognizer gets first use of directional
    controls and learns collision cells online. Otherwise fresh directional
    successors test their protocol inverse first; thereafter the graph follows
    known edges to the shallowest reachable frontier. This avoids mistaking a
    ticking HUD for useful progress, walking an entire corridor before testing
    sibling moves, and repeating one movement that merely changes a status bar.
    """

    def __init__(self) -> None:
        self._previous: Snapshot | None = None
        self._previous_signature: str | None = None
        self._previous_excluded: frozenset[Coordinate] = frozenset()
        self._pending: ActionProposal | None = None
        self._last_transition: Transition | None = None
        self._state_visits: Counter[str] = Counter()
        self._global_stats: dict[str, ActionStats] = defaultdict(ActionStats)
        self._state_stats: dict[tuple[str, str], ActionStats] = defaultdict(ActionStats)
        self._nodes: dict[str, StateNode] = {}
        self._edges: dict[tuple[str, str], GraphEdge] = {}
        self._transition_trace: list[dict[str, Any]] = []
        self._tile_maze = TileMazeNavigator()

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
        """Return recent action/outcome evidence without retaining grid pixels."""
        if limit < 1:
            return []
        return [dict(entry) for entry in self._transition_trace[-limit:]]

    def finalize(self, snapshot: Snapshot) -> None:
        """Account for a final environment response when no next action is due.

        Framework loops stop immediately on a win or an action budget, leaving
        the final step without a subsequent ``choose`` call. The local runner
        invokes this method solely for accurate diagnostics; it never proposes
        or executes another action.
        """
        if self._pending is None:
            return
        excluded = horizontal_hud_mask(snapshot)
        signature = masked_signature(snapshot, excluded)
        self._observe_transition(snapshot, signature, excluded)
        self._pending = None

    def _observe_transition(
        self,
        current: Snapshot,
        signature: str,
        excluded: frozenset[Coordinate],
    ) -> set[Coordinate]:
        changed: set[Coordinate] = set()
        self._last_transition = None
        if self._previous is None or self._pending is None or self._previous_signature is None:
            return changed

        changed = changed_coordinates(
            self._previous.planes,
            current.planes,
            set(excluded | self._previous_excluded),
        )
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
        edge = self._edges.setdefault(
            (self._previous_signature, self._pending.key),
            GraphEdge(proposal=self._pending),
        )
        edge.successor = signature
        edge.transition = transition
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

    def _candidate_actions(
        self,
        snapshot: Snapshot,
        changed: set[Coordinate],
        excluded: frozenset[Coordinate],
    ) -> tuple[ActionProposal, ...]:
        """Build a deterministic, finite action frontier for a new node."""
        valid = tuple(action for action in snapshot.available_actions if action != RESET)
        candidates: list[tuple[int, int, str, ActionProposal]] = []

        for action in valid:
            if action == COMPLEX_ACTION:
                continue
            proposal = ActionProposal(
                action,
                reasoning={
                    "policy": "novelty-explorer-v4",
                    "kind": "graph-simple-frontier",
                },
            )
            candidates.append((600 + self._simple_priority(action), 1, action, proposal))

        if COMPLEX_ACTION in valid:
            for salience, (x, y), reason in rank_click_targets(snapshot, changed, excluded):
                proposal = ActionProposal(
                    name=COMPLEX_ACTION,
                    x=x,
                    y=y,
                    reasoning={
                        **reason,
                        "policy": "novelty-explorer-v4",
                        "kind": "graph-click-frontier",
                        "target": [x, y],
                        "salience": salience,
                    },
                )
                # A visually salient component should beat a directional probe;
                # the generic lattice remains a lower-priority fallback.
                candidates.append((200 + salience, 0, proposal.key, proposal))

        candidates.sort(
            key=lambda item: (
                -item[0],
                item[1],
                ACTION_NAMES.index(item[3].name),
                item[3].y if item[3].y is not None else -1,
                item[3].x if item[3].x is not None else -1,
            )
        )
        return tuple(item[3] for item in candidates)

    def _node(
        self,
        snapshot: Snapshot,
        signature: str,
        changed: set[Coordinate],
        excluded: frozenset[Coordinate],
    ) -> StateNode:
        """Get a graph node, prioritising a validated inverse on discovery.

        A move into a previously unseen screen state normally leaves its parent
        with other untried actions.  Probing the protocol inverse first is a
        cheap way to establish the return edge; subsequent choices can then
        navigate to the shallowest remaining frontier rather than committing
        to an arbitrary depth-first walk.
        """
        node = self._nodes.get(signature)
        if node is not None:
            return node

        actions = list(self._candidate_actions(snapshot, changed, excluded))
        parent = self._nodes.get(self._previous_signature or "")
        incoming = self._pending
        transition = self._last_transition
        depth = 0
        if parent is not None and incoming is not None and transition is not None and not transition.game_over:
            depth = parent.depth + 1
            inverse = INVERSE_DIRECTIONAL_ACTION.get(incoming.name)
            if inverse is not None:
                # Keep the policy-generated proposal (and its reasoning) but
                # put the likely return movement ahead of deeper probes.
                actions.sort(key=lambda proposal: proposal.name != inverse)

        node = StateNode(tuple(actions), depth=depth)
        self._nodes[signature] = node
        return node

    @staticmethod
    def _next_untested(node: StateNode) -> ActionProposal | None:
        return next((action for action in node.actions if action.key not in node.tried), None)

    def _route_to(self, start: str, target: str) -> tuple[ActionProposal, ...] | None:
        """Return a shortest safe known directed route, if one exists."""
        if start == target:
            return ()
        queue: deque[str] = deque([start])
        parents: dict[str, tuple[str, GraphEdge]] = {}
        visited = {start}

        while queue:
            state = queue.popleft()
            outgoing = [
                edge
                for (origin, _), edge in self._edges.items()
                if origin == state
                and edge.successor is not None
                and edge.successor not in visited
                and (edge.transition is None or not edge.transition.game_over)
            ]
            for edge in sorted(outgoing, key=lambda candidate: candidate.proposal.key):
                assert edge.successor is not None
                successor = edge.successor
                visited.add(successor)
                parents[successor] = (state, edge)
                if successor == target:
                    route: list[ActionProposal] = []
                    while successor != start:
                        previous, parent_edge = parents[successor]
                        route.append(parent_edge.proposal)
                        successor = previous
                    return tuple(reversed(route))
                queue.append(successor)
        return None

    def _scheduled_frontier(self, current: str) -> ActionProposal | None:
        """Choose the shallowest reachable open node and route toward it.

        Local expansion alone is depth-first: a successful ``ACTION1`` causes
        another ``ACTION1`` at every fresh successor.  Scheduling globally by
        discovery depth keeps inverse-verified routes short and samples all
        sibling directions before spending an entire episode down one branch.
        """
        options: list[tuple[int, int, int, str, tuple[ActionProposal, ...], ActionProposal]] = []
        for state, node in self._nodes.items():
            next_action = self._next_untested(node)
            if next_action is None:
                continue
            route = self._route_to(current, state)
            if route is None:
                continue
            options.append((node.depth, len(node.tried), len(route), state, route, next_action))
        if not options:
            return None
        _, _, _, _, route, next_action = min(options)
        return route[0] if route else next_action

    def choose(self, snapshot: Snapshot) -> ActionProposal:
        """Observe ``snapshot`` and select one legal, systematic probe."""
        excluded = horizontal_hud_mask(snapshot)
        signature = masked_signature(snapshot, excluded)
        changed = self._observe_transition(snapshot, signature, excluded)
        self._state_visits[signature] += 1

        if snapshot.state in {"NOT_PLAYED", "GAME_OVER"}:
            self._tile_maze.reset()
            proposal = ActionProposal(
                RESET,
                reasoning={
                    "policy": "novelty-explorer-v4",
                    "kind": "reset",
                    "state": snapshot.state,
                },
            )
            self._remember(snapshot, signature, excluded, proposal)
            return proposal

        valid = tuple(action for action in snapshot.available_actions if action != RESET)
        if not valid:
            proposal = ActionProposal(
                RESET,
                reasoning={"policy": "novelty-explorer-v4", "kind": "no-valid-actions"},
            )
            self._remember(snapshot, signature, excluded, proposal)
            return proposal

        self._node(snapshot, signature, changed, excluded)
        proposal = self._tile_maze.choose(snapshot)
        if proposal is None:
            proposal = self._scheduled_frontier(signature)
        if proposal is None or proposal.name not in valid:
            # A reset is the deterministic way to revisit a known root when
            # this directed graph has no safe route to another unexplored node.
            proposal = ActionProposal(
                RESET,
                reasoning={
                    "policy": "novelty-explorer-v4",
                    "kind": "frontier-reset",
                    "state_visits": self._state_visits[signature],
                },
            )

        self._remember(snapshot, signature, excluded, proposal)
        return proposal

    def _remember(
        self,
        snapshot: Snapshot,
        signature: str,
        excluded: frozenset[Coordinate],
        proposal: ActionProposal,
    ) -> None:
        # Mark an edge before execution. A reset or terminal response can end a
        # loop before another observation, and must not make this edge appear
        # untested on the next visit.
        node = self._nodes.get(signature)
        if node is not None:
            node.tried.add(proposal.key)
        self._edges.setdefault((signature, proposal.key), GraphEdge(proposal=proposal))
        self._previous = snapshot
        self._previous_signature = signature
        self._previous_excluded = excluded
        self._pending = proposal
