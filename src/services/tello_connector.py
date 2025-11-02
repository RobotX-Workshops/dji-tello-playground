import logging
import time
from typing import Any, Dict, Literal, Union
from djitellopy import Tello, BackgroundFrameRead

LOGGER = logging.getLogger(__name__)


class TelloConnector:
    """
    A wrapper class around the Tello SDK that provides a interface for controlling the Tello drone.
    """

    def __init__(self, tello: Tello):
        self.tello = tello

    def connect(self):
        self.tello.connect()
        for second in range(3, 0, -1):
            LOGGER.info(f"Connecting in {second}")
            time.sleep(1)

        LOGGER.debug("Connected to Tello")

    def streamoff(self):
        self.tello.streamoff()
        LOGGER.debug("Video stream off")

    def streamon(self):
        LOGGER.info("Restarting video stream")
        time.sleep(1)
        self.streamoff()
        time.sleep(1)
        self.tello.streamon()
        LOGGER.info("Video stream on")

    def get_frame_read(self) -> BackgroundFrameRead:
        LOGGER.debug("Getting frame read")
        return self.tello.get_frame_read()

    def take_off(self):
        LOGGER.info("Taking off...")
        self.tello.takeoff()

    def is_flying(self) -> bool:
        return self.tello.is_flying

    def land(self):
        LOGGER.info("Landing...")
        self.tello.land()

    def send_rc_control(
        self,
        left_right_velocity: int,
        for_back_velocity: int,
        up_down_velocity: int,
        yaw_velocity: int,
    ):
        LOGGER.debug(
            f"Sending RC control: {left_right_velocity}, {for_back_velocity}, {up_down_velocity}, {yaw_velocity}"
        )
        self.tello.send_rc_control(
            left_right_velocity, for_back_velocity, up_down_velocity, yaw_velocity
        )

    def emergency_stop(self) -> None:
        self.tello.emergency()

    def set_speed_cm_s(self, cm_s: int) -> None:
        """Set speed to x cm/s.
        Arguments:
            x: 10-100
        """
        assert 10 <= cm_s <= 100
        self.tello.set_speed(cm_s)

    def end(self) -> None:
        LOGGER.debug("Ending Tello service")
        self.tello.end()

    def flip_forward(self) -> None:
        self.tello.flip_forward()

    def flip_back(self) -> None:
        self.tello.flip_back()

    def flip_left(self) -> None:
        self.tello.flip_left()

    def flip_right(self) -> None:
        self.tello.flip_right()

    def get_battery(self) -> int:
        return self.tello.get_battery()
    
    @property
    def address(self) -> tuple[str, Literal[8889]]:
        return self.tello.address

    def get_barometer(self) -> int:
        return self.tello.get_barometer()
    
    def get_distance_tof(self) -> int:
        return self.tello.get_distance_tof()
    
    def get_height(self) -> int:
        return self.tello.get_height()
    
    def get_flight_time(self) -> int:
        return self.tello.get_flight_time()
    
    def get_speed_x(self) -> int:
        return self.tello.get_speed_x()
    
    def get_speed_y(self) -> int:
        return self.tello.get_speed_y()
    
    def get_speed_z(self) -> int:
        return self.tello.get_speed_z()
    
    def get_acceleration_x(self) -> float:
        return self.tello.get_acceleration_x()
    
    def get_acceleration_y(self) -> float:
        return self.tello.get_acceleration_y()
    
    def get_acceleration_z(self) -> float:
        return self.tello.get_acceleration_z()
    
    def query_serial_number(self) -> str:
        return self.tello.query_serial_number()

    def get_pitch(self) -> int:
        return self.tello.get_pitch()

    def get_roll(self) -> int:
        return self.tello.get_roll()

    def get_yaw(self) -> int:
        return self.tello.get_yaw()

    def query_attitude(self) -> Dict[str, Union[int, float, str]]:
        return self.tello.query_attitude()

    def get_lowest_temperature(self) -> int:
        return self.tello.get_lowest_temperature()

    def get_highest_temperature(self) -> int:   
        return self.tello.get_highest_temperature()

    def get_temperature(self) -> float:
        return self.tello.get_temperature()

    def get_current_state(self) -> Dict[Any, Any]:
        return self.tello.get_current_state()
