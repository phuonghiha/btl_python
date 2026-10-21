"""Rules and generated layout for the swamp lily-pad puzzle."""

from dataclasses import dataclass
import math
import random

MAX_JUMP_DISTANCE = 240
FAR_BANK_TARGET = (1050, 230)


@dataclass(frozen=True)
class LilyPad:
    """A lily pad's position and the direction shown by its notch."""

    pad_id: int
    x: int
    y: int
    direction: float
    route_index: int | None = None
    size: int = 96


class LilyPadPuzzle:
    """Generate a safe route and validate nearby lily-pad jumps.

    Direction is a fractional clockwise index from north. The eight supplied
    images provide base orientations; the scene rotates them for exact
    alignment from each notch bisector to the next route point.
    """

    # Tọa độ theo pixel màn hình (1280x720), sắp theo thứ tự bước đi.
    # Mỗi dòng là (x, y, kích thước): bạn có thể chỉnh trực tiếp tại đây.
    # Screen pixels for a 1280x720 window; tuples are (x, y, size), in step order.
    _ROUTE_LAYOUT = (
        (600, 390, 86),  # Bước 1
        (533, 286, 72),  # Bước 2
        (681, 330, 92),  # Bước 3
        (830, 390, 78),  # Bước 4
        (826, 522, 88),  # Bước 5
        (960, 552, 76),  # Bước 6
        (1015, 436, 94), # Bước 7
        (1146, 386, 82), # Bước 8
        (1060, 270, 82), # Bước 9, sát bờ bên kia
    )

    # Lá sai: (x, y, kích thước), cũng dùng pixel màn hình.
    # Decoy pads: (x, y, size), also in screen pixels.
    _DECOY_LAYOUT = (
        (206, 325, 70),
        (367, 259, 82),
        (498, 186, 72),
        (648, 233, 68),
        (655, 163, 62),
        (790, 277, 90),
        (901, 268, 74),
        (962, 327, 62),
        (442, 386, 88),
        (713, 452, 76),
        (642, 528, 92),
        (1182, 535, 72),
        (853, 649, 86),
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
        angle = math.atan2(dx, -dy) % (2 * math.pi)
        return angle / (math.pi / 4)

    def reset_layout(self):
        """Build pads in declared step order using screen-pixel coordinates."""
        route_points = [(x, y) for x, y, _ in self._ROUTE_LAYOUT]
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
                size=self._ROUTE_LAYOUT[i][2],
            )
            for i, point in enumerate(route_points)
        ]
        decoys = [
            LilyPad(
                pad_id=len(route_pads) + i,
                x=x,
                y=y,
                direction=self._rng.randrange(8),
                size=size,
            )
            for i, (x, y, size) in enumerate(self._DECOY_LAYOUT)
        ]

        self.pads = route_pads + decoys
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
            if (
                abs(mouse_x - pad.x) <= max(24, round(pad.size * 0.44))
                and abs(mouse_y - pad.y) <= max(20, round(pad.size * 0.34))
            ):
                return pad.pad_id
        return None

    def can_step_on(self, pad_id, player_position):
        """Return whether a pad is a reachable, valid next route step."""
        pad = next((pad for pad in self.pads if pad.pad_id == pad_id), None)
        if pad is None or pad.route_index is None:
            return False
        if math.dist((pad.x, pad.y), player_position) > MAX_JUMP_DISTANCE:
            return False
        if pad.pad_id == self.current_pad_id:
            return False

        next_route_index = (
            0 if self._current_route_index is None
            else self._current_route_index + 1
        )
        if self._current_route_index is None:
            return pad.route_index == next_route_index

        # Allow revisiting any already-cleared pad, plus only the next
        # forward step so the player cannot skip ahead through the route.
        return (
            pad.route_index <= self._current_route_index
            or pad.route_index == next_route_index
        )

    def is_within_jump_range(self, pad_id, player_position):
        """Return whether the player is close enough to jump to this pad."""
        pad = next((pad for pad in self.pads if pad.pad_id == pad_id), None)
        return (
            pad is not None
            and math.dist((pad.x, pad.y), player_position) <= MAX_JUMP_DISTANCE
        )

    def remove_decoy(self, pad_id):
        """Remove a failed decoy pad from the visible and clickable layout."""
        pad = next((pad for pad in self.pads if pad.pad_id == pad_id), None)
        if pad is not None and pad.route_index is None:
            self.pads.remove(pad)

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

        if not self.can_step_on(pad_id, player_position):
            return "wrong"

        self._current_route_index = pad.route_index
        if self.is_complete:
            return "complete"
        return "correct"

    def return_to_shore(self):
        """Forget the current pad when the player steps back onto shore."""
        self._current_route_index = None
