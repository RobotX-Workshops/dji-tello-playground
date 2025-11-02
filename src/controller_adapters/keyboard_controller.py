import sys
import os

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
sys.path.append(parent_dir)

import logging
from typing import Callable, Dict, List
from joysticks.pygame_connector import PyGameConnector
import pygame
from services.tello_controller import (
    TelloActionType,
    TelloControlState,
    TelloController,
)
from .utils import run_adapter_test

_LOGGER = logging.getLogger(__name__)


class _State:
    forward_velocity = 0
    right_velocity = 0
    up_velocity = 0
    yaw_right_velocity = 0


class KeyboardControlAdapter(TelloController):

    ENTER_KEY = 13

    _event_key_map = {
        pygame.K_ESCAPE: TelloActionType.EMERGENCY_LAND,
        pygame.K_1: TelloActionType.FLIP_FORWARD,
        pygame.K_2: TelloActionType.FLIP_BACK,
        pygame.K_3: TelloActionType.FLIP_LEFT,
        pygame.K_4: TelloActionType.FLIP_RIGHT,
        pygame.K_RIGHTBRACKET: TelloActionType.INCREASE_SPEED_CM_S,
        pygame.K_LEFTBRACKET: TelloActionType.DECREASE_SPEED_CM_S,
        pygame.K_SPACE: TelloActionType.LAND,
        ENTER_KEY: TelloActionType.TAKEOFF,
    }

    def __init__(
        self,
        pygame_connector: PyGameConnector,
        step_size: int = 10,
    ):
        self.pygame = pygame_connector
        self.step_size = step_size
        self.state = _State()

        self.axis_key_map: Dict[int, Callable] = {
            pygame.K_w: self.increase_forward_speed,
            pygame.K_s: self.increase_backwards_speed,
            pygame.K_d: self.increase_right_speed,
            pygame.K_a: self.increase_left_speed,
            pygame.K_UP: self.increase_up_speed,
            pygame.K_DOWN: self.increase_down_speed,
            pygame.K_RIGHT: self.increase_right_yaw,
            pygame.K_LEFT: self.increase_left_yaw,
        }

    def print_key_mappings(self):
        print("Key Mappings:")
        print("------------")
        print("Event Key Mappings:")
        for key, action in self._event_key_map.items():
            print(f"{pygame.key.name(key)}: {action}")
        print("\nAxis Key Mappings:")
        for key, action in self.axis_key_map.items():
            print(f"{pygame.key.name(key)}: {action.__name__}")

    def update_velocity(self, velocity: int, increment: int) -> int:
        velocity += increment
        velocity = min(max(velocity, -100), 100)
        return velocity

    def t(self, controller_axis_value: float) -> int:
        "Transform the controller axis value to the tello control value"
        return int(controller_axis_value * 100)

    def get_state(self) -> TelloControlState:
        events: List[TelloActionType] = []
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:

                if event.key in self._event_key_map:
                    events.append(self._event_key_map[event.key])

                if event.key in self.axis_key_map:
                    state = self.state
                    self.axis_key_map[event.key](state)

        state = self.state
        return TelloControlState(
            forward_velocity=state.forward_velocity,
            right_velocity=state.right_velocity,
            up_velocity=state.up_velocity,
            yaw_right_velocity=state.yaw_right_velocity,
            events=events,
        )

    def increase_left_yaw(self, state):
        state.yaw_right_velocity = self.update_velocity(
            state.yaw_right_velocity, -self.step_size
        )

    def increase_right_yaw(self, state):
        state.yaw_right_velocity = self.update_velocity(
            state.yaw_right_velocity, self.step_size
        )

    def increase_down_speed(self, state):
        state.up_velocity = self.update_velocity(state.up_velocity, -self.step_size)

    def increase_up_speed(self, state):
        state.up_velocity = self.update_velocity(state.up_velocity, self.step_size)

    def increase_left_speed(self, state):
        state.right_velocity = self.update_velocity(
            state.right_velocity, -self.step_size
        )

    def increase_right_speed(self, state):
        state.right_velocity = self.update_velocity(
            state.right_velocity, self.step_size
        )

    def increase_backwards_speed(self, state):
        state.forward_velocity = self.update_velocity(
            state.forward_velocity, -self.step_size
        )

    def increase_forward_speed(self, state):
        state.forward_velocity = self.update_velocity(
            state.forward_velocity, self.step_size
        )


if __name__ == "__main__":
    _LOGGER.setLevel(logging.DEBUG)
    pygame_connector = PyGameConnector()
    pygame_connector.set_display(400, 300)
    pygame_connector.set_caption("Keyboard as Joystick")
    tello_control = KeyboardControlAdapter(pygame_connector)

    run_adapter_test(tello_control)
