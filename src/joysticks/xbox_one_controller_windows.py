"""
This module contains the implementation of a "Turtle Beach Recon Controller Xbox Series X|S, Xbox One and PC" controller for a Windows host.
This controller does not work on MAC OS. It is a wired controller that can be connected to a PC via USB.
https://www.amazon.de/-/en/gp/product/B0977MTK65/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&th=1
.. image:: docs/images/xbox_one_turtle_beach_controller.jpg
   :alt: Turtle Beach Recon Controller Xbox Series X|S, Xbox One and PC
   :width: 400px
   :align: center
It provides classes for handling the controller's axes, buttons, and D-pad state.
The `Controller` abstract base class defines the interface for getting the current controller state.
"""

from dataclasses import dataclass, fields
from typing import List
from enum import Enum
import logging
import sys
import time


try:
    from joysticks.pygame_connector import PyGameConnector
    from joysticks.game_controller import (
        GameController,
        ControllerAxesState,
        ControllerDPadState,
        GameControllerState,
        StickState,
        ControllerButtonPressedState,
    )
except ModuleNotFoundError:
    from pygame_connector import PyGameConnector
    from game_controller import (
        GameController,
        ControllerAxesState,
        ControllerDPadState,
        GameControllerState,
        StickState,
        ControllerButtonPressedState,
    )

LOGGER = logging.getLogger(__name__)


class DPadKeys(Enum):
    HORIZONTAL = 0
    VERTICAL = 1


class AxisKeys(Enum):
    LEFT_STICK_HORIZONTAL = 0
    LEFT_STICK_VERTICAL = 1
    LEFT_ANALOG_TRIGGER = 4
    RIGHT_STICK_HORIZONTAL = 2
    RIGHT_STICK_VERTICAL = 3
    RIGHT_ANALOG_TRIGGER = 5


class ButtonKeys(Enum):
    A = 0
    B = 1
    X = 2
    Y = 3
    LB = 4
    RB = 5
    VIEW = 6
    MENU = 7
    LEFT_STICK = 8
    RIGHT_STICK = 9
    SCREENSHOT = 11


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
    SCREENSHOT: bool
    LEFT_STICK: bool
    RIGHT_STICK: bool

    def get_pressed_buttons(self) -> List[str]:
        return [field.name for field in fields(self) if getattr(self, field.name)]


class WindowsXboxOnePyGameJoystick(GameController):
    """
    The controller works on two main principles
        - That the axes act like a stream of data and are constant
        - The buttons are event based as in only when a button is pressed is the button acknowledged.
            The release of the button is not acknowledged directly but can be inferred
    """

    def __init__(self, pygame_connector: PyGameConnector, joystick_id: int = 0):

        if "win" not in sys.platform.lower():
            raise ValueError(
                f"Windows adapter is being used on a {sys.platform} system"
            )

        self.pygame_connector = pygame_connector
        pygame_connector.init_joystick()
        self.joystick = pygame_connector.create_joystick(joystick_id)
        self.joystick.init()

        name = self.joystick.get_name()
        LOGGER.info(f"Detected joystick device: {name}")
        if "Controller (Xbox One For Windows)" not in name:
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
            self.axis_ids[i] = AxisKeys(i)
        for i in range(buttons_count):
            try:
                self.button_ids[i] = ButtonKeys(i)
            except Exception as e:
                LOGGER.error(f"Error when trying to match button {i}", e)

    def get_state(self) -> GameControllerState:
        self.pygame_connector.get_events()

        left_stick_horizontal = self.joystick.get_axis(
            AxisKeys.LEFT_STICK_HORIZONTAL.value
        )
        left_stick_vertical = self.joystick.get_axis(AxisKeys.LEFT_STICK_VERTICAL.value)
        right_stick_horizontal = self.joystick.get_axis(
            AxisKeys.RIGHT_STICK_HORIZONTAL.value
        )
        right_stick_vertical = self.joystick.get_axis(
            AxisKeys.RIGHT_STICK_VERTICAL.value
        )
        left_analog_trigger = self.joystick.get_axis(AxisKeys.LEFT_ANALOG_TRIGGER.value)
        right_analog_trigger = self.joystick.get_axis(
            AxisKeys.RIGHT_ANALOG_TRIGGER.value
        )

        if abs(left_stick_horizontal) < self.dead_zone:
            left_stick_horizontal = 0.0
        if abs(left_stick_vertical) < self.dead_zone:
            left_stick_vertical = 0.0
        if abs(right_stick_horizontal) < self.dead_zone:
            right_stick_horizontal = 0.0
        if abs(right_stick_vertical) < self.dead_zone:
            right_stick_vertical = 0.0
        if abs(left_analog_trigger) < self.dead_zone:
            left_analog_trigger = 0.0
        if abs(right_analog_trigger) < self.dead_zone:
            right_analog_trigger = 0.0

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

        buttons = ButtonPressedState(
            A=self.joystick.get_button(ButtonKeys.A.value),
            B=self.joystick.get_button(ButtonKeys.B.value),
            X=self.joystick.get_button(ButtonKeys.X.value),
            Y=self.joystick.get_button(ButtonKeys.Y.value),
            LB=self.joystick.get_button(ButtonKeys.LB.value),
            RB=self.joystick.get_button(ButtonKeys.RB.value),
            VIEW=self.joystick.get_button(ButtonKeys.VIEW.value),
            MENU=self.joystick.get_button(ButtonKeys.MENU.value),
            SCREENSHOT=self.joystick.get_button(ButtonKeys.SCREENSHOT.value),
            LEFT_STICK=self.joystick.get_button(ButtonKeys.LEFT_STICK.value),
            RIGHT_STICK=self.joystick.get_button(ButtonKeys.RIGHT_STICK.value),
        )

        # Retrieve the state of the D-pad buttons
        hat = self.joystick.get_hat(0)
        d_pad_state = ControllerDPadState(
            int(hat[DPadKeys.HORIZONTAL.value]),
            int(hat[DPadKeys.VERTICAL.value]),
        )

        pressed_button_ids = [
            button.value
            for button in ButtonKeys
            if self.joystick.get_button(button.value)
        ]
        pressed_buttons = [ButtonKeys(button_id) for button_id in pressed_button_ids]

        if LOGGER.getEffectiveLevel() == logging.DEBUG:
            LOGGER.debug(f"Axes: {axes}")
            LOGGER.debug(f"Buttons: {buttons}")
            LOGGER.debug(
                f"Pressed Buttons: {[button.name for button in pressed_buttons]}"
            )

        return GameControllerState(axes=axes, buttons=buttons, d_pad=d_pad_state)


if __name__ == "__main__":
    import os

    log_level = logging.INFO
    logging.basicConfig(level=log_level)
    LOGGER.setLevel(log_level)
    pygame_connector = PyGameConnector()
    pygame_joystick = WindowsXboxOnePyGameJoystick(pygame_connector)

    def print_state(state_dict: dict, indent=""):
        for k, v in state_dict.items():
            if isinstance(v, dict):
                print(f"{indent}{k}:")
                print_state(v, indent + "  ")
            else:
                print(f"{indent}{k}: {v}")

    while True:
        os.system("cls" if os.name == "nt" else "clear")  # Clear the console
        print("\033[1;1H")  # Move the cursor to the top-left corner

        state = pygame_joystick.get_state()
        print("Current state:")
        dict_state = state.to_dict()

        print_state(dict_state)

        time.sleep(0.1)
