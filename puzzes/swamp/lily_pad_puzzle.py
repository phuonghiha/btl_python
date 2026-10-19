"""Rules and generated layout for the swamp lily-pad puzzle."""

from dataclasses import dataclass
import math
import random


MAX_JUMP_DISTANCE = 150
FAR_BANK_TARGET = (1050, 210)


@dataclass(frozen=True)
class LilyPad:
    """A lily pad's position and the direction shown by its notch."""

    pad_id: int
    x: int
    y: int
    direction: int
    route_index: int | None = None


class LilyPadPuzzle:
    """Generate a safe route and validate nearby lily-pad jumps.

    Direction indexes follow the supplied artwork clockwise, starting at
    north: N, NE, E, SE, S, SW, W, NW. The route pads point toward the next
    route pad, and the last route pad points toward the far bank.
    """

    _ROUTE_POINTS = (
        (520, 400),
        (620, 360),
        (720, 400),
        (820, 360),
        (920, 400),
        (1020, 360),
        (1120, 270),
    )
    _DECOY_POINTS = (
        (650, 500),
        (820, 500),
        (990, 500),
        (1170, 430),
    )

    def __init__(self, rng=None):
        self._rng = rng or random.Random()
        self.pads = []
        self._route = []
        self._current_route_index = None
        self.reset_layout()

    @staticmethod
    def _direction_between(start, end):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        angle = math.degrees(math.atan2(dy, dx))
        return int(round((angle + 90) / 45)) % 8

    def reset_layout(self):
        """Create a slightly varied layout while preserving a safe route."""
        route_points = [
            (
                x + self._rng.randint(-8, 8),
                y + self._rng.randint(-5, 5),
            )
            for x, y in self._ROUTE_POINTS
        ]
        route_directions = [
            self._direction_between(route_points[i], route_points[i + 1])
            for i in range(len(route_points) - 1)
        ]
        route_directions.append(
            self._direction_between(route_points[-1], FAR_BANK_TARGET)
        )

        route_pads = [
            LilyPad(
                pad_id=i,
                x=point[0],
                y=point[1],
                direction=route_directions[i],
                route_index=i,
            )
            for i, point in enumerate(route_points)
        ]
        decoys = [
            LilyPad(
                pad_id=len(route_pads) + i,
                x=x + self._rng.randint(-8, 8),
                y=y + self._rng.randint(-8, 8),
                direction=self._rng.randrange(8),
            )
            for i, (x, y) in enumerate(self._DECOY_POINTS)
        ]

        self.pads = route_pads + decoys
        self._rng.shuffle(self.pads)
        self._route = route_pads
        self._current_route_index = None

    @property
    def current_pad_id(self):
        if self._current_route_index is None:
            return None
        return self._route[self._current_route_index].pad_id

    @property
    def current_pad(self):
        if self._current_route_index is None:
            return None
        return self._route[self._current_route_index]

    @property
    def is_complete(self):
        return self._current_route_index == len(self._route) - 1

    def pad_at(self, position):
        """Return a clicked pad id, or None when the click missed all pads."""
        mouse_x, mouse_y = position
        for pad in self.pads:
            if abs(mouse_x - pad.x) <= 42 and abs(mouse_y - pad.y) <= 32:
                return pad.pad_id
        return None

    def select(self, pad_id, player_position):
        """Validate a nearby jump and update the player's current pad.

        Returns 'correct', 'wrong', 'too_far', 'stay', or 'complete'. Route
        pads can be visited in either direction; decoys remain unsafe.
        """
        pad = next((pad for pad in self.pads if pad.pad_id == pad_id), None)
        if pad is None:
            return "wrong"

        distance = math.hypot(
            pad.x - player_position[0], pad.y - player_position[1]
        )
        if distance > MAX_JUMP_DISTANCE:
            return "too_far"

        if pad.route_index is None:
            return "wrong"

        if pad.pad_id == self.current_pad_id:
            return "stay"

        self._current_route_index = pad.route_index
        if self.is_complete:
            return "complete"
        return "correct"

    def return_to_shore(self):
        """Forget the current pad when the player steps back onto shore."""
        self._current_route_index = None
