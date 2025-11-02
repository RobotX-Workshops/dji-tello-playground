"""
This file contains the class for the Tectinter Ali Express Controller.
https://de.aliexpress.com/item/32824692489.html?spm=a2g0o.order_list.order_list_main.5.49305c5fYhRXjs&gatewayAdapt=glo2deu
![Here](./images/ali_express_controller.jpg)
"""

from dataclasses import dataclass, fields
from enum import Enum
import time
import logging
from typing import List


try:
    from joysticks.pygame_connector import PyGameConnector
    from joysticks.game_controller import (
        ControllerAxesState,
        ControllerDPadState,
        GameControllerState,
        StickState,
        ControllerButtonPressedState,
    )
except ModuleNotFoundError:
    from pygame_connector import PyGameConnector
    from game_controller import (
        ControllerAxesState,
        ControllerDPadState,
        GameControllerState,
        StickState,
        ControllerButtonPressedState,
    )


_LOGGER = logging.getLogger(__name__)


class _DPadKeys(Enum):
    HORIZONTAL = 0
    VERTICAL = 1


class _AxisKeys(Enum):
    LEFT_STICK_HORIZONTAL = 0
    LEFT_STICK_VERTICAL = 1
    RIGHT_STICK_HORIZONTAL = 2
    RIGHT_STICK_VERTICAL = 3
    LEFT_TRIGGER = 4
    RIGHT_TRIGGER = 5


class _ButtonKeys(Enum):
    A = 0
    B = 1
    X = 2
    Y = 3
    LB = 4
    RB = 5
    SELECT = 6
    START = 7
    HOME = 10
    LEFT_STICK = 8
    RIGHT_STICK = 9


@dataclass
class _ButtonPressedState(ControllerButtonPressedState):
    A: bool
    B: bool
    X: bool
    Y: bool
    LB: bool
    RB: bool
    SELECT: bool
    START: bool
    HOME: bool
    LEFT_STICK: bool
    RIGHT_STICK: bool

    def get_pressed_buttons(self) -> List[str]:
        return [field.name for field in fields(self) if getattr(self, field.name)]


class TectInterJoystick:
    """
    The controller works on two main principles
        - That the axes act like a stream of data and are constant
        - The buttons are event based as in only when a button is pressed is the button acknowledged.
            The release of the button is not acknowledged directly but can be inferred
    """

    def __init__(self, pygame_connector: PyGameConnector, joystick_id: int = 0):
        self.pygame_connector = pygame_connector
        pygame_connector.init_joystick()
        self.joystick = pygame_connector.create_joystick(joystick_id)
        self.joystick.init()

        name = self.joystick.get_name()
        _LOGGER.info(f"Detected joystick device: {name}")
        # This is how it is dectected on windows
        controller_type = "Xbox 360 Controller"
        if controller_type != name:
            raise ValueError(
                f"{controller_type.capitalize()} controller not detected. Controller detected was {name}"
            )

        num_axes = self.joystick.get_numaxes()
        num_buttons = self.joystick.get_numbuttons()
        self.axis_states = [0.0 for i in range(num_axes)]
        self.button_states = [False for i in range(num_buttons)]
        self.axis_ids = {}
        self.button_ids = {}
        self.dead_zone = 0.07
        for i in range(num_axes):
            self.axis_ids[i] = _AxisKeys(i)
        for i in range(num_buttons):
            self.button_ids[i] = _ButtonKeys(i)

    def get_state(self) -> GameControllerState:
        self.pygame_connector.get_events()

        left_stick_horizontal = self.joystick.get_axis(
            _AxisKeys.LEFT_STICK_HORIZONTAL.value
        )
        left_stick_vertical = self.joystick.get_axis(
            _AxisKeys.LEFT_STICK_VERTICAL.value
        )
        right_stick_horizontal = self.joystick.get_axis(
            _AxisKeys.RIGHT_STICK_HORIZONTAL.value
        )
        right_stick_vertical = self.joystick.get_axis(
            _AxisKeys.RIGHT_STICK_VERTICAL.value
        )
        left_analog_trigger = self.joystick.get_axis(_AxisKeys.LEFT_TRIGGER.value)
        right_analog_trigger = self.joystick.get_axis(_AxisKeys.RIGHT_TRIGGER.value)

        if abs(left_stick_horizontal) < self.dead_zone:
            left_stick_horizontal = 0.0
        if abs(left_stick_vertical) < self.dead_zone:
            left_stick_vertical = 0.0
        if abs(right_stick_horizontal) < self.dead_zone:
            right_stick_horizontal = 0.0
        if abs(right_stick_vertical) < self.dead_zone:
            right_stick_vertical = 0.0

        axes = ControllerAxesState(
            left_stick=StickState(
                horizontal_right=left_stick_horizontal,
                vertical_down=left_stick_vertical,
            ),
            right_stick=StickState(
                horizontal_right=right_stick_horizontal,
                vertical_down=right_stick_vertical,
            ),
            left_analog_trigger=left_analog_trigger,
            right_analog_trigger=right_analog_trigger,
        )

        buttons = _ButtonPressedState(
            A=self.joystick.get_button(_ButtonKeys.A.value),
            B=self.joystick.get_button(_ButtonKeys.B.value),
            X=self.joystick.get_button(_ButtonKeys.X.value),
            Y=self.joystick.get_button(_ButtonKeys.Y.value),
            LB=self.joystick.get_button(_ButtonKeys.LB.value),
            RB=self.joystick.get_button(_ButtonKeys.RB.value),
            LEFT_STICK=self.joystick.get_button(_ButtonKeys.LEFT_STICK.value),
            RIGHT_STICK=self.joystick.get_button(_ButtonKeys.RIGHT_STICK.value),
            HOME=self.joystick.get_button(_ButtonKeys.HOME.value),
            SELECT=self.joystick.get_button(_ButtonKeys.SELECT.value),
            START=self.joystick.get_button(_ButtonKeys.START.value),
        )

        # Retrieve the state of the D-pad buttons
        hat = self.joystick.get_hat(0)
        d_pad_state = ControllerDPadState(
            int(hat[_DPadKeys.HORIZONTAL.value]),
            int(hat[_DPadKeys.VERTICAL.value]),
        )

        print("Current state")
        print(axes)
        print(self.joystick.get_numbuttons(), self.joystick)
        print(d_pad_state)

        pressed_button_ids = [
            button.value
            for button in _ButtonKeys
            if self.joystick.get_button(button.value)
        ]
        pressed_buttons = [_ButtonKeys(button_id) for button_id in pressed_button_ids]

        if _LOGGER.getEffectiveLevel() == logging.DEBUG:
            _LOGGER.debug(f"Axes: {axes}")
            _LOGGER.debug(f"Buttons: {buttons}")
            _LOGGER.debug(
                f"Pressed Buttons: {[button.name for button in pressed_buttons]}"
            )

        return GameControllerState(axes=axes, buttons=buttons, d_pad=d_pad_state)


if __name__ == "__main__":
    pygame_connector = PyGameConnector()
    pygame_joystick = TectInterJoystick(pygame_connector)
    _LOGGER.setLevel("DEBUG")
    while True:
        state = pygame_joystick.get_state()
        print("Current state")
        dict_state = state.to_dict()

        for k, v in dict_state.items():
            print(k, v)

        time.sleep(0.1)
