"""
This module contains the class that select the correct implementation of the xbox controller based on the platform.
"""

import logging
import time
import sys


try:
    from joysticks.pygame_connector import PyGameConnector
    from joysticks.xbox_one_controller_linux import LinuxXboxOnePyGameJoystick
    from joysticks.xbox_one_controller_windows import WindowsXboxOnePyGameJoystick
    from joysticks.game_controller import (
        GameController,
        GameControllerState,
    )
except ModuleNotFoundError:
    from xbox_one_controller_linux import LinuxXboxOnePyGameJoystick
    from xbox_one_controller_windows import WindowsXboxOnePyGameJoystick
    from pygame_connector import PyGameConnector
    from game_controller import (
        GameController,
        GameControllerState,
    )


LOGGER = logging.getLogger(__name__)


class XboxOnePyGameController(GameController):
    """
    The controller works on two main principles
        - That the axes act like a stream of data and are constant
        - The buttons are event based as in only when a button is pressed is the button acknowledged.
            The release of the button is not acknowledged directly but can be inferred
    """

    platform_controller: GameController

    def __init__(self, pygame_connector: PyGameConnector, joystick_id: int = 0):
        if sys.platform == "win32":
            self.platform_controller = WindowsXboxOnePyGameJoystick(
                pygame_connector, joystick_id
            )
        elif sys.platform.startswith("linux"):
            self.platform_controller = LinuxXboxOnePyGameJoystick(
                pygame_connector, joystick_id
            )
        else:
            raise ValueError(
                f"Unknown platform {sys.platform}. Cannot create {self.__class__.__name__}"
            )

    def get_state(self) -> GameControllerState:
        return self.platform_controller.get_state()


if __name__ == "__main__":
    import os

    def print_state(state_dict, indent=""):
        for k, v in state_dict.items():
            if isinstance(v, dict):
                print(f"{indent}{k}:")
                print_state(v, indent + "  ")
            else:
                print(f"{indent}{k}: {v}")

    log_level = logging.DEBUG
    logging.basicConfig(level=log_level)
    LOGGER.setLevel(log_level)
    pygame_connector = PyGameConnector()
    pygame_joystick = XboxOnePyGameController(pygame_connector)

    while True:
        os.system("cls" if os.name == "nt" else "clear")  # Clear the console
        print("\033[1;1H")  # Move the cursor to the top-left corner

        state = pygame_joystick.get_state()
        print("Current state:")
        dict_state = state.to_dict()

        print_state(dict_state)

        time.sleep(0.1)
