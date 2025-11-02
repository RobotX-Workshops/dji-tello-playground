from typing import Tuple
from services.tello_controller import TelloControlState, TelloController


class FaceFollowingController(TelloController):

    def __init__(self, max_velocity: int = 100):
        self.max_velocity = max_velocity

    def normalize_velocity(self, value: int, max_value: int) -> int:
        """Normalizes the velocity value to the range [-max_velocity, max_velocity]."""
        if max_value == 0:
            return 0
        return int(max(min(value / max_value, 1), -1) * self.max_velocity)

    def get_state(
        self, movement_vector_xyz: Tuple, dead_zone: int = 10
    ) -> TelloControlState:
        """Gets the current controller state of the drone."""
        max_x, max_y, max_z = movement_vector_xyz
        max_z = max_z / 10
        max_value = max(abs(max_x), abs(max_y), abs(max_z))

        normalized_x = self.normalize_velocity(max_x, max_value)
        normalized_y = self.normalize_velocity(max_y, max_value)
        normalized_z = self.normalize_velocity(max_z, max_value)

        x = normalized_x if abs(normalized_x) > dead_zone else 0
        y = normalized_y if abs(normalized_y) > dead_zone else 0
        z = normalized_z if abs(normalized_z) > dead_zone else 0

        return TelloControlState(
            events=[],
            forward_velocity=z,
            right_velocity=0,  # Set right_velocity to 0
            up_velocity=-y,
            yaw_right_velocity=x,
        )
