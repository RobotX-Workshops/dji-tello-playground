import time
import cv2

from services.tello_command_dispatcher import TelloCommandDispatcher
from services.tello_controller import TelloController
from .tello_connector import TelloConnector
import logging


LOGGER = logging.getLogger(__name__)


class FrontEnd:
    def __init__(
        self,
        dispatcher: TelloCommandDispatcher,
        tello_service: TelloConnector,
        controller: TelloController,
    ):
        self.dispatcher = dispatcher
        self.tello_service = tello_service
        self.controller = controller

    def run(self, cadence_secs: float = 0):
        frame_read = self.tello_service.get_frame_read()
        while True:
            time.sleep(cadence_secs)
            controller_state = self.controller.get_state()
            self.dispatcher.send_commands(controller_state)

            if frame_read.stopped:
                frame_read.stop()
                break

            frame = frame_read.frame
            if frame is not None:
                cv2.imshow("Tello Stream", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC key
                break

        self.tello_service.end()
