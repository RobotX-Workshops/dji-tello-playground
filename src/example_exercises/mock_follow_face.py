"""
This script is used to mock tracking a face in the frame and follow it with the drone.
Instead of the drones camera it uses the hosts computer camera to test functionality.
It prints the facetracking controller outputs but does not dispatch them to a drone
"""

import time
import cv2
from face_tracking.image_drawing_service import ImageDrawingService
from face_tracking.image_compression_service import ImageCompressionService
from face_tracking.recognition_face_identifier import RecognitionFaceIdentifier
from face_tracking.open_cv_wrapper import OpenCvWrapper
from face_tracking.tracking_frame_processor import process_tracking_frame
import logging
import argparse
from controller_adapters.follow_face_controller import FaceFollowingController


args = argparse.ArgumentParser()

logging.basicConfig(level=logging.ERROR)

LOGGER = logging.getLogger(__name__)

# Variables
ZERO_DEPTH_BOX_SIZE = 400
DEPTH_TARGET = 650

open_cv = OpenCvWrapper()

image_compressor = ImageCompressionService(open_cv)

face_identifier = RecognitionFaceIdentifier(open_cv, image_compressor)

image_drawer = ImageDrawingService(open_cv)

controller = FaceFollowingController()

print("Starting flying in ...")
for i in range(3, 0, -1):
    print(i)
    time.sleep(1)

# tello.takeoff()
cam = open_cv.connect_to_camera()


while True:
    time.sleep(0.200)

    ret, frame = cam.read()

    if frame is None or frame.size == 0 or frame.shape[0] == 0 or frame.shape[1] == 0:
        LOGGER.debug("No frame")
        continue

    control_state = process_tracking_frame(
        frame, face_identifier, image_drawer, controller, open_cv, DEPTH_TARGET, LOGGER
    )
    if control_state is None:
        continue

    # dispatcher.send_commands(control_state)

    if open_cv.listen_for_key(1) & 0xFF == ord("q"):
        break

cam.release()
cv2.destroyAllWindows()
