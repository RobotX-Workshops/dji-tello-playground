"""
This module contains the implementation of a General "Xbox Wireless" controller.
https://www.amazon.de/-/en/gp/product/B07SDFLVKD/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&th=1
.. image:: docs/images/xbox_pad.jpeg
   :alt: General Xbox Wireless Controller
   :width: 400px
   :align: center
It provides classes for handling the controller's axes, buttons, and D-pad state.
The `Controller` abstract base class defines the interface for getting the current controller state.
The `XboxPyGameJoystick` class is a concrete implementation of the `Controller` interface using the PyGame library.
"""

import logging
import sys
import time
from dataclasses import dataclass
from enum import Enum

try:
    from joysticks.game_controller import (
        ControllerAxesState,
        ControllerButtonPressedState,
        ControllerDPadState,
        GameController,
        GameControllerState,
        read_axis,
        read_stick_state,
    )
    from joysticks.pygame_connector import PyGameConnector
except ModuleNotFoundError:
    from game_controller import (
        ControllerAxesState,
        ControllerButtonPressedState,
        ControllerDPadState,
        GameController,
        GameControllerState,
        read_axis,
        read_stick_state,
    )
    from pygame_connector import PyGameConnector


_LOGGER = logging.getLogger(__name__)


class _ButtonKeys(Enum):
    A = 0
    B = 1
    X = 2
    Y = 3
    LB = 9
    RB = 10
    VIEW = 4
    MENU = 6
    NA = 15
    LEFT_STICK = 7
    RIGHT_STICK = 8
    D_PAD_UP = 11
    D_PAD_DOWN = 12
    D_PAD_LEFT = 13
    D_PAD_RIGHT = 14


class _AxisKeys(Enum):
    LEFT_STICK_HORIZONTAL = 0
    LEFT_STICK_VERTICAL = 1
    LEFT_ANALOG_TRIGGER = 4
    RIGHT_STICK_HORIZONTAL = 2
    RIGHT_STICK_VERTICAL = 3
    RIGHT_ANALOG_TRIGGER = 5


# Button keys that are not assigned to any button on the controller
_VOID_BUTTONS = [5]


@dataclass
class ButtonPressedState(ControllerButtonPressedState):
    A: bool
    B: bool
    X: bool
    Y: bool
    LB: bool
    RB: bool
    VIEW: bool
    MENU: bool
    SHARE: bool
    LEFT_STICK: bool
    RIGHT_STICK: bool


class MacXboxPyGameJoystick(GameController):
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
        _LOGGER.info(f"detected joystick device: {name}")

        if "darwin" not in sys.platform:
            raise ValueError(
                f"Xbox controller not detected. Controller detected was {name}"
            )
        else:
            _LOGGER.info("Running on macOS")
            if name != "Xbox Series X Controller":
                raise ValueError(
                    f"Xbox controller not detected. Controller detected was {name}"
                )

        self.axis_states = [0.0] * self.joystick.get_numaxes()
        self.button_states = [False] * self.joystick.get_numbuttons()
        self.axis_ids = {}
        self.button_ids = {}
        self.dead_zone = 0.07
        for i in range(self.joystick.get_numaxes()):
            self.axis_ids[i] = _AxisKeys(i)
        mapped_buttons = filter(
            lambda x: x not in _VOID_BUTTONS, range(self.joystick.get_numbuttons())
        )
        for i in mapped_buttons:
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
            left_analog_trigger=read_axis(
                self.joystick, _AxisKeys.LEFT_ANALOG_TRIGGER.value, self.dead_zone
            ),
            right_analog_trigger=read_axis(
                self.joystick, _AxisKeys.RIGHT_ANALOG_TRIGGER.value, self.dead_zone
            ),
        )

        buttons = ButtonPressedState(
            A=self.joystick.get_button(_ButtonKeys.A.value),
            B=self.joystick.get_button(_ButtonKeys.B.value),
            X=self.joystick.get_button(_ButtonKeys.X.value),
            Y=self.joystick.get_button(_ButtonKeys.Y.value),
            LB=self.joystick.get_button(_ButtonKeys.LB.value),
            RB=self.joystick.get_button(_ButtonKeys.RB.value),
            VIEW=self.joystick.get_button(_ButtonKeys.VIEW.value),
            MENU=self.joystick.get_button(_ButtonKeys.MENU.value),
            SHARE=self.joystick.get_button(_ButtonKeys.NA.value),
            LEFT_STICK=self.joystick.get_button(_ButtonKeys.LEFT_STICK.value),
            RIGHT_STICK=self.joystick.get_button(_ButtonKeys.RIGHT_STICK.value),
        )

        right = self.joystick.get_button(_ButtonKeys.D_PAD_RIGHT.value)
        left = self.joystick.get_button(_ButtonKeys.D_PAD_LEFT.value)
        up = self.joystick.get_button(_ButtonKeys.D_PAD_UP.value)
        down = self.joystick.get_button(_ButtonKeys.D_PAD_DOWN.value)

        d_pad_state = ControllerDPadState(
            horizontal_right=1 if right else -1 if left else 0,
            vertical_up=1 if up else -1 if down else 0,
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
    pygame_joystick = MacXboxPyGameJoystick(pygame_connector)

    while True:
        os.system("cls" if os.name == "nt" else "clear")  # Clear the console
        print("\033[1;1H")  # Move the cursor to the top-left corner

        state = pygame_joystick.get_state()
        print("Current state:")
        dict_state = state.to_dict()

        print_state(dict_state)

        time.sleep(0.1)
