"""
This script is used as a Sanity check abd performs face tracking using a camera feed.
It identifies faces in each frame, calculates the distance between the center of the frame
and each face, and selects the closest face.
It then draws a box around the closest face and displays the frame with the box.
The script continues to track faces until the user presses 'q' to quit.

A Camera must be connected to the system to run this script properly.
"""

from image_drawing_service import ImageDrawingService
from image_compression_service import ImageCompressionService
from recognition_face_identifier import RecognitionFaceIdentifier
from open_cv_wrapper import OpenCvWrapper
import cv2
import logging
import argparse
from utils.positioning_utils import (
    get_box_center_xyz,
    get_distance_xyz,
    get_frame_center_xy,
    get_vector_xyz,
)


args = argparse.ArgumentParser()

logging.basicConfig(level=logging.DEBUG)

LOGGER = logging.getLogger(__name__)

# Variables
ZERO_DEPTH_BOX_SIZE = 400
DEPTH_TARGET = 650


open_cv = OpenCvWrapper()

image_compressor = ImageCompressionService(open_cv)

face_identifier = RecognitionFaceIdentifier(open_cv, image_compressor)
print(face_identifier)
image_drawer = ImageDrawingService(open_cv)

cam = open_cv.connect_to_camera()

LOGGER.debug("Starting face tracking")

while True:
    ret, frame = cam.read()
    if not ret:
        LOGGER.debug("No frame")
        continue

    faces_trbl = face_identifier.identify_faces(frame)
    if not faces_trbl:
        LOGGER.debug("No faces")
        continue

    frame_center_xyz = (*get_frame_center_xy(frame), DEPTH_TARGET)

    closest = None
    for face_trbl in faces_trbl:
        box_center = get_box_center_xyz(face_trbl, DEPTH_TARGET)
        distance = get_distance_xyz(frame_center_xyz, box_center)
        if closest is None or distance < closest[1]:
            closest = (face_trbl, distance, box_center)
        frame = image_drawer.draw_box(
            frame,
            face_trbl,
            "green",
            f"{box_center}",
        )
        frame = image_drawer.draw_cross_hair_in_box(frame, face_trbl, 4, "green")

    assert closest is not None
    closest_box = closest[0]
    closest_distance = closest[1]
    closest_center = closest[2]

    vector_to_center = get_vector_xyz(frame_center_xyz, closest_center)

    frame = image_drawer.draw_box(frame, closest_box, "red")
    frame = image_drawer.draw_frame_center_cross_hair(frame, 2, 20, "red")

    LOGGER.debug(
        f"Closest face at {frame_center_xyz, closest_center} with distance {closest_distance}"
    )

    LOGGER.debug(f"Drone movement {vector_to_center} to center the face in the frame.")

    open_cv.show_image("frame", frame)
    if open_cv.listen_for_key(1) & 0xFF == ord("q"):
        break

cam.release()
cv2.destroyAllWindows()
