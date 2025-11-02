"""
This module contains the class that select the correct implementation of the gc102 controller based on the platform.
"""

import logging
import time
import sys


try:
    from joysticks.gc102_controller_windows import WindowsGC102PyGameJoystick
    from joysticks.pygame_connector import PyGameConnector
    from joysticks.game_controller import (
        GameController,
        GameControllerState,
    )
except ModuleNotFoundError:
    from gc102_controller_windows import WindowsGC102PyGameJoystick
    from pygame_connector import PyGameConnector
    from game_controller import (
        GameController,
        GameControllerState,
    )


_LOGGER = logging.getLogger(__name__)


class GC102PyGameController(GameController):
    """
    The controller works on two main principles
        - That the axes act like a stream of data and are constant
        - The buttons are event based as in only when a button is pressed is the button acknowledged.
            The release of the button is not acknowledged directly but can be inferred
    """

    platform_controller: GameController

    def __init__(self, pygame_connector: PyGameConnector, joystick_id: int = 0):

        if sys.platform.startswith("win"):
            self.platform_controller = WindowsGC102PyGameJoystick(
                pygame_connector, joystick_id
            )
        else:
            raise ValueError(
                f"Unknown platform {sys.platform}. Cannot create GC102PyGameJoystick"
            )

    def get_state(self) -> GameControllerState:
        return self.platform_controller.get_state()


if __name__ == "__main__":
    import os

    log_level = logging.INFO
    logging.basicConfig(level=log_level)
    _LOGGER.setLevel(log_level)
    pygame_connector = PyGameConnector()
    pygame_joystick = GC102PyGameController(pygame_connector)

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
        print(f"Current state on platform {sys.platform} :")
        dict_state = state.to_dict()

        print_state(dict_state)

        time.sleep(0.1)
