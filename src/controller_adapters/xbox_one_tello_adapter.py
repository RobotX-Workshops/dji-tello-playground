import sys
import os

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
sys.path.append(parent_dir)

from joysticks.pygame_connector import PyGameConnector
from joysticks.xbox_one_controller import XboxOnePyGameController
from controller_adapters.base_gamepad_adapter import BaseGamepadTelloAdapter
from controller_adapters.utils import run_adapter_test


class XboxOneTelloControlAdapter(BaseGamepadTelloAdapter):
    def __init__(self, controller: XboxOnePyGameController) -> None:
        super().__init__(controller)


if __name__ == "__main__":
    pygame_connector = PyGameConnector()
    controller = XboxOnePyGameController(pygame_connector)
    tello_control = XboxOneTelloControlAdapter(controller)
    run_adapter_test(tello_control)
