import os
from typing import Optional
import cv2
from djitellopy import Tello

import time

import numpy as np
from services.tello_connector import TelloConnector


# # Create a Tello instance
# tello = TelloConnector(Tello())

# print("Attempting to connect to drone ...")

# # # Connect to Tello
# tello.connect()

# # print("Starting camera stream ...")
# tello.streamon()


def resolve_video_source(cli_value: Optional[str]) -> str:
    """Resolve the active video source from CLI or environment"""
    env_value = os.getenv("VIDEO_SOURCE")
    if cli_value:
        return cli_value
    if env_value:
        return env_value
    return "0"


def open_capture(source: str) -> cv2.VideoCapture:
    """Create a cv2.VideoCapture using either index or URL"""
    if source.isdigit():
        return cv2.VideoCapture(int(source))
    return cv2.VideoCapture(source)


# Create window and trackbars for parameter tuning
cv2.namedWindow("Circle Detection")
cv2.createTrackbar("param1", "Circle Detection", 60, 200, lambda x: None)
cv2.createTrackbar("param2", "Circle Detection", 175, 300, lambda x: None)
cv2.createTrackbar("minDist", "Circle Detection", 30, 200, lambda x: None)
cv2.createTrackbar("minRadius", "Circle Detection", 20, 200, lambda x: None)
cv2.createTrackbar("maxRadius", "Circle Detection", 440, 500, lambda x: None)

while True:
    # Get camera frame to make sure the camera is working
    # img = tello.get_frame_read().frame
    # img = np.zeros((480, 640, 3), dtype=np.uint8)  # Placeholder for testing
    # Get image from machine camera for testing
    video_source = resolve_video_source(None)
    cap = open_capture(video_source)
    ret, img = cap.read()
    if not ret:
        continue

    # Get trackbar values
    param1 = cv2.getTrackbarPos("param1", "Circle Detection")
    param2 = cv2.getTrackbarPos("param2", "Circle Detection")
    minDist = cv2.getTrackbarPos("minDist", "Circle Detection")
    minRadius = cv2.getTrackbarPos("minRadius", "Circle Detection")
    maxRadius = cv2.getTrackbarPos("maxRadius", "Circle Detection")

    # Ensure minDist is at least 1
    minDist = max(1, minDist)

    # run circle detection here
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_blur = cv2.GaussianBlur(img_gray, (9, 9), 2)
    circles = cv2.HoughCircles(
        img_blur,
        cv2.HOUGH_GRADIENT,
        dp=1,
        minDist=minDist,
        param1=param1,
        param2=param2,
        minRadius=minRadius,
        maxRadius=maxRadius,
    )
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            # draw the outer circle
            cv2.circle(img, (i[0], i[1]), i[2], (0, 255, 0), 2)
            # draw the center of the circle
            cv2.circle(img, (i[0], i[1]), 2, (0, 0, 255), 3)

    cv2.imshow("Circle Detection", img)
    time.sleep(1 / 15)
    # Press 'q' or ESC to quit
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q") or key == 27:
        break

cv2.destroyAllWindows()

# print("Starting flying in ...")
# for i in range(3, 0, -1):
#     print(i)
#     time.sleep(1)

# # Takeoff
# print("Take off")
# tello.take_off()

# # print("Hovering for...")
# # for i in range(3, 0, -1):
# #     print(i)
# #     time.sleep(1)
# print("Height is ", tello.get_height(), "cm")


# print("Landing")
# # Land
# tello.land()

# End the connection
# tello.end()
