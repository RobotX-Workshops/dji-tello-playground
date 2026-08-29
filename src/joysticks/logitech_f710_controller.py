"""
This module provides a LogitechF710Joystick class that represents a Logitech F710 controller.
It allows you to retrieve the state of the controller's axes, buttons, and D-pad.

Confirmed working on Windows and Linux systems.
   
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum

try:
    from joysticks.game_controller import (
        ControllerAxesState,
        ControllerButtonPressedState,
        ControllerDPadState,
        GameControllerState,
        read_stick_state,
    )
    from joysticks.pygame_connector import PyGameConnector
except ModuleNotFoundError:
    from game_controller import (
        ControllerAxesState,
        ControllerButtonPressedState,
        ControllerDPadState,
        GameControllerState,
        read_stick_state,
    )
    from pygame_connector import PyGameConnector


_LOGGER = logging.getLogger(__name__)


class _DPadKeys(Enum):
    HORIZONTAL = 0
    VERTICAL = 1


class _AxisKeys(Enum):
    LEFT_STICK_HORIZONTAL = 0
    LEFT_STICK_VERTICAL = 1
    RIGHT_STICK_HORIZONTAL = 2
    RIGHT_STICK_VERTICAL = 3


class _ButtonKeys(Enum):
    A = 1
    B = 2
    X = 0
    Y = 3
    LB = 4
    RB = 5
    Back = 8
    Start = 9
    LeftTrigger = 6
    RightTrigger = 7
    LEFT_STICK = 10
    RIGHT_STICK = 11


@dataclass
class _ControllerButtonPressedState(ControllerButtonPressedState):
    A: bool
    B: bool
    X: bool
    Y: bool
    LB: bool
    RB: bool
    Back: bool
    Start: bool
    LEFT_STICK: bool
    RIGHT_STICK: bool


class LogitechF710Joystick:
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
        controller_type = "logitech"
        if controller_type not in name.lower():
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

        axes = ControllerAxesState(
            left_stick=read_stick_state(
                self.joystick,
                _AxisKeys.LEFT_STICK_HORIZONTAL.value,
                _AxisKeys.LEFT_STICK_VERTICAL.value,
                self.dead_zone,
            ),
            right_stick=read_stick_state(
                self.joystick,
                _AxisKeys.RIGHT_STICK_HORIZONTAL.value,
                _AxisKeys.RIGHT_STICK_VERTICAL.value,
                self.dead_zone,
            ),
            left_analog_trigger=float(
                self.joystick.get_button(_ButtonKeys.LeftTrigger.value)
            ),
            right_analog_trigger=float(
                self.joystick.get_button(_ButtonKeys.RightTrigger.value)
            ),
        )

        buttons = _ControllerButtonPressedState(
            A=self.joystick.get_button(_ButtonKeys.A.value),
            B=self.joystick.get_button(_ButtonKeys.B.value),
            X=self.joystick.get_button(_ButtonKeys.X.value),
            Y=self.joystick.get_button(_ButtonKeys.Y.value),
            LB=self.joystick.get_button(_ButtonKeys.LB.value),
            RB=self.joystick.get_button(_ButtonKeys.RB.value),
            LEFT_STICK=self.joystick.get_button(_ButtonKeys.LEFT_STICK.value),
            RIGHT_STICK=self.joystick.get_button(_ButtonKeys.RIGHT_STICK.value),
            Start=self.joystick.get_button(_ButtonKeys.Start.value),
            Back=self.joystick.get_button(_ButtonKeys.Back.value),
        )

        # Retrieve the state of the D-pad buttons
        hat = self.joystick.get_hat(0)
        d_pad_state = ControllerDPadState(
            int(hat[_DPadKeys.HORIZONTAL.value]),
            int(hat[_DPadKeys.VERTICAL.value]),
        )

        if _LOGGER.getEffectiveLevel() == logging.DEBUG:
            _LOGGER.debug(f"Axes: {axes}")
            _LOGGER.debug(f"Buttons: {buttons}")
            _LOGGER.debug(f"Pressed Buttons: {buttons.get_pressed_buttons()}")

        return GameControllerState(axes=axes, buttons=buttons, d_pad=d_pad_state)


if __name__ == "__main__":
    import os

    try:
        from joysticks.utils import print_state
    except ModuleNotFoundError:
        from utils import print_state

    log_level = logging.INFO
    logging.basicConfig(level=log_level)
    _LOGGER.setLevel(log_level)
    pygame_connector = PyGameConnector()
    pygame_joystick = LogitechF710Joystick(pygame_connector)

    while True:
        os.system("cls" if os.name == "nt" else "clear")  # Clear the console
        print("\033[1;1H")  # Move the cursor to the top-left corner

        state = pygame_joystick.get_state()
        print("Current state:")
        dict_state = state.to_dict()

        print_state(dict_state)

        time.sleep(0.1)
