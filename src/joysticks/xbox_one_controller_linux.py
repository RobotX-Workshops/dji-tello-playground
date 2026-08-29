"""
This module contains the implementation of a "Turtle Beach Recon Controller Xbox Series X|S, Xbox One and PC" controller for a Linux host.
This controller does not work on MAC OS. It is a wired controller that can be connected to a PC via USB.
https://www.amazon.de/-/en/gp/product/B0977MTK65/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&th=1
.. image:: docs/images/xbox_one_turtle_beach_controller.jpg
   :alt: Turtle Beach Recon Controller Xbox Series X|S, Xbox One and PC
   :width: 400px
   :align: center
It provides classes for handling the controller's axes, buttons, and D-pad state.
The `Controller` abstract base class defines the interface for getting the current controller state.
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


LOGGER = logging.getLogger(__name__)


class _DPadKeys(Enum):
    HORIZONTAL = 0
    VERTICAL = 1


class _AxisKeys(Enum):
    LEFT_STICK_HORIZONTAL = 0
    LEFT_STICK_VERTICAL = 1
    LEFT_ANALOG_TRIGGER = 2
    RIGHT_STICK_HORIZONTAL = 3
    RIGHT_STICK_VERTICAL = 4
    RIGHT_ANALOG_TRIGGER = 5


class _ButtonKeys(Enum):
    A = 0
    B = 1
    X = 2
    Y = 3
    LB = 4
    RB = 5
    VIEW = 6
    MENU = 7
    NA = 8
    LEFT_STICK = 9
    RIGHT_STICK = 10


@dataclass
class _ButtonPressedState(ControllerButtonPressedState):
    A: bool
    B: bool
    X: bool
    Y: bool
    LB: bool
    RB: bool
    VIEW: bool
    MENU: bool
    NA: bool
    LEFT_STICK: bool
    RIGHT_STICK: bool


class LinuxXboxOnePyGameJoystick(GameController):
    """
    The controller works on two main principles
        - That the axes act like a stream of data and are constant
        - The buttons are event based as in only when a button is pressed is the button acknowledged.
            The release of the button is not acknowledged directly but can be inferred
    """

    def __init__(self, pygame_connector: PyGameConnector, joystick_id: int = 0):
        if "linux" not in sys.platform.lower():
            raise ValueError(f"Linux adapter is being used on a {sys.platform} system")

        self.pygame_connector = pygame_connector
        pygame_connector.init_joystick()
        self.joystick = pygame_connector.create_joystick(joystick_id)
        self.joystick.init()

        name = self.joystick.get_name()
        LOGGER.info(f"detected joystick device: {name}")
        if "Microsoft X-Box One" not in name:
            raise ValueError(
                f"Xbox One controller not detected. Controller detected was {name}"
            )

        axes_count = self.joystick.get_numaxes()
        buttons_count = self.joystick.get_numbuttons()
        self.axis_states = [0.0 for i in range(axes_count)]
        self.button_states = [False for i in range(buttons_count)]
        self.axis_ids = {}
        self.button_ids = {}
        self.dead_zone = 0.07
        for i in range(axes_count):
            self.axis_ids[i] = _AxisKeys(i)
        for i in range(buttons_count):
            try:
                self.button_ids[i] = _ButtonKeys(i)
            except Exception as e:
                LOGGER.error(f"Error when trying to match button {i}", e)

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

        buttons = _ButtonPressedState(
            A=self.joystick.get_button(_ButtonKeys.A.value),
            B=self.joystick.get_button(_ButtonKeys.B.value),
            X=self.joystick.get_button(_ButtonKeys.X.value),
            Y=self.joystick.get_button(_ButtonKeys.Y.value),
            LB=self.joystick.get_button(_ButtonKeys.LB.value),
            RB=self.joystick.get_button(_ButtonKeys.RB.value),
            VIEW=self.joystick.get_button(_ButtonKeys.VIEW.value),
            MENU=self.joystick.get_button(_ButtonKeys.MENU.value),
            NA=self.joystick.get_button(_ButtonKeys.NA.value),
            LEFT_STICK=self.joystick.get_button(_ButtonKeys.LEFT_STICK.value),
            RIGHT_STICK=self.joystick.get_button(_ButtonKeys.RIGHT_STICK.value),
        )

        # Retrieve the state of the D-pad buttons
        hat = self.joystick.get_hat(0)
        d_pad_state = ControllerDPadState(
            int(hat[_DPadKeys.HORIZONTAL.value]),
            int(hat[_DPadKeys.VERTICAL.value]),
        )

        if LOGGER.getEffectiveLevel() == logging.DEBUG:
            LOGGER.debug(f"Axes: {axes}")
            LOGGER.debug(f"Buttons: {buttons}")
            LOGGER.debug(f"Pressed Buttons: {buttons.get_pressed_buttons()}")

        return GameControllerState(axes=axes, buttons=buttons, d_pad=d_pad_state)


if __name__ == "__main__":
    import os

    try:
        from joysticks.utils import print_state
    except ModuleNotFoundError:
        from utils import print_state

    log_level = logging.INFO
    logging.basicConfig(level=log_level)
    LOGGER.setLevel(log_level)
    pygame_connector = PyGameConnector()
    pygame_joystick = LinuxXboxOnePyGameJoystick(pygame_connector)

    while True:
        os.system("cls" if os.name == "nt" else "clear")  # Clear the console
        print("\033[1;1H")  # Move the cursor to the top-left corner

        state = pygame_joystick.get_state()
        print("Current state:")
        dict_state = state.to_dict()

        print_state(dict_state)

        time.sleep(0.1)
