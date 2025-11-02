from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, fields
from typing import List


@dataclass
class StickState:
    horizontal_right: float
    "If positive the stick is in the right position, else left"
    vertical_down: float
    "If positive the stick is in the down position, else up"


@dataclass
class ControllerAxesState:
    left_stick: StickState
    right_stick: StickState
    left_analog_trigger: float
    right_analog_trigger: float


@dataclass
class ControllerDPadState:
    horizontal_right: int
    """If positive, the D-pad is pressed right, if negative, the D-pad is pressed left. If 0, the D-pad is not pressed"""
    vertical_up: int
    """If positive, the D-pad is pressed up, if negative, the D-pad is pressed down. If 0, the D-pad is not pressed"""

    def get_active(self) -> List[str]:
        return [field.name for field in fields(self) if getattr(self, field.name) != 0]


class ControllerButtonPressedState(ABC):
    @abstractmethod
    def get_pressed_buttons(self) -> List[str]:
        pass


@dataclass
class GameControllerState:
    """
    This state represents the desired state for the controller.
    """

    # The axis control range
    AXIS_MIN_VAL = -1
    AXIS_MAX_VAL = 1

    axes: ControllerAxesState
    buttons: ControllerButtonPressedState
    d_pad: ControllerDPadState

    def __post_init__(self):
        self.validate_direction(
            "axes.left_stick.horizontal", self.axes.left_stick.horizontal_right
        )
        self.validate_direction(
            "axes.left_stick.vertical", self.axes.left_stick.vertical_down
        )
        self.validate_direction(
            "axes.right_stick.horizontal", self.axes.right_stick.horizontal_right
        )
        self.validate_direction(
            "axes.right_stick.vertical", self.axes.right_stick.vertical_down
        )
        self.validate_direction(
            "axes.left_analog_trigger", self.axes.left_analog_trigger
        )
        self.validate_direction(
            "axes.right_analog_trigger", self.axes.right_analog_trigger
        )

    def validate_direction(self, attribute_name: str, value: float):
        if not isinstance(value, float):
            raise ValueError(
                f"{attribute_name} value needs to be an float. Got {type(value)}"
            )
        if not (self.AXIS_MIN_VAL <= value <= self.AXIS_MAX_VAL):
            raise ValueError(
                f"Value {value} for attribute '{attribute_name}' is not in the range [{self.AXIS_MIN_VAL}, {self.AXIS_MAX_VAL}]"
            )

    def to_dict(self):
        return asdict(self)


class GameController(ABC):
    @abstractmethod
    def get_state(self) -> GameControllerState:
        """Gets the current controller state of the drone"""
