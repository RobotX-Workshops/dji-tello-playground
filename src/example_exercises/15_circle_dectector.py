import os
from typing import Optional
import cv2
from djitellopy import Tello
import signal
import sys
import time

import numpy as np
from djitellopy import Tello

# Set to True to use local camera for debugging, False to use drone
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
# Set to True to use drone camera but not take off (for testing detection)
NO_TAKEOFF = os.getenv("NO_TAKEOFF", "false").lower() == "true"

# Global variable to hold tello instance for signal handler
tello = None
cap = None


def emergency_landing(signum=None, frame=None):
    """Emergency landing handler for signals"""
    print("\n⚠️  Emergency shutdown triggered!")
    if tello is not None and not DEBUG_MODE:
        try:
            print("Sending emergency land command...")
            tello.send_rc_control(0, 0, 0, 0)
            tello.land()
            tello.end()
            print("✓ Drone landed safely")
        except Exception as e:
            print(f"Error during emergency landing: {e}")
    if cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print("Cleanup complete. Exiting...")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, emergency_landing)  # Ctrl+C
signal.signal(signal.SIGTERM, emergency_landing)  # Termination signal

# Register signal handlers
signal.signal(signal.SIGINT, emergency_landing)  # Ctrl+C
signal.signal(signal.SIGTERM, emergency_landing)  # Termination signal

if DEBUG_MODE:
    print("Running in DEBUG mode with local camera")
    tello = None
    cap = None
else:
    # Create a Tello instance
    tello = Tello()

    # Connect to Tello
    tello.connect()

    print("Attempting to connect to drone ...")

    # Connect to Tello
    tello.connect()

    print("Starting camera stream ...")
    tello.streamon()

    print("Waiting for camera to stabilize...")
    time.sleep(2)
    cap = None


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
cv2.createTrackbar(
    "blurKernel", "Circle Detection", 9, 31, lambda x: None
)  # Must be odd
cv2.createTrackbar("blurSigma", "Circle Detection", 2, 10, lambda x: None)
cv2.createTrackbar(
    "dp", "Circle Detection", 10, 30, lambda x: None
)  # Will be divided by 10
cv2.createTrackbar("param1", "Circle Detection", 60, 200, lambda x: None)
cv2.createTrackbar("param2", "Circle Detection", 175, 300, lambda x: None)
cv2.createTrackbar("minDist", "Circle Detection", 30, 200, lambda x: None)
cv2.createTrackbar("minRadius", "Circle Detection", 20, 200, lambda x: None)
cv2.createTrackbar("maxRadius", "Circle Detection", 440, 500, lambda x: None)

if DEBUG_MODE:
    video_source = resolve_video_source(None)
    cap = open_capture(video_source)
    print(f"Opened camera: {video_source}")
elif not NO_TAKEOFF:
    print("Taking off...")
    tello.takeoff()
    time.sleep(2)
else:
    print("NO_TAKEOFF mode - drone will hover but not take off")

# Control parameters
FORWARD_SPEED = 20  # cm/s forward speed
YAW_SENSITIVITY = 0.3  # Rotation sensitivity
TARGET_RADIUS_MIN = 50  # Minimum radius to consider for navigation
CENTER_TOLERANCE = 50  # Pixel tolerance for centering

while True:
    # Get camera frame from drone or debug camera
    if DEBUG_MODE:
        ret, img = cap.read()
        if not ret or img is None:
            continue
    else:
        img = tello.get_frame_read().frame
        if img is None:
            continue

    # Get frame dimensions
    height, width = img.shape[:2]
    frame_center_x = width // 2
    frame_center_y = height // 2

    # Get trackbar values
    blur_kernel = cv2.getTrackbarPos("blurKernel", "Circle Detection")
    blur_sigma = cv2.getTrackbarPos("blurSigma", "Circle Detection")
    dp_value = cv2.getTrackbarPos("dp", "Circle Detection")
    param1 = cv2.getTrackbarPos("param1", "Circle Detection")
    param2 = cv2.getTrackbarPos("param2", "Circle Detection")
    minDist = cv2.getTrackbarPos("minDist", "Circle Detection")
    minRadius = cv2.getTrackbarPos("minRadius", "Circle Detection")
    maxRadius = cv2.getTrackbarPos("maxRadius", "Circle Detection")

    # Ensure values are valid
    minDist = max(1, minDist)
    blur_kernel = (
        blur_kernel if blur_kernel % 2 == 1 else blur_kernel + 1
    )  # Must be odd
    blur_kernel = max(1, blur_kernel)
    blur_sigma = max(0.1, blur_sigma)
    dp = max(0.1, dp_value / 10.0)  # Convert to decimal

    # run circle detection here
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_blur = cv2.GaussianBlur(img_gray, (blur_kernel, blur_kernel), blur_sigma)
    circles = cv2.HoughCircles(
        img_blur,
        cv2.HOUGH_GRADIENT,
        dp=dp,
        minDist=minDist,
        param1=param1,
        param2=param2,
        minRadius=minRadius,
        maxRadius=maxRadius,
    )

    # Draw frame center crosshair
    cv2.line(
        img,
        (frame_center_x - 20, frame_center_y),
        (frame_center_x + 20, frame_center_y),
        (255, 255, 255),
        2,
    )
    cv2.line(
        img,
        (frame_center_x, frame_center_y - 20),
        (frame_center_x, frame_center_y + 20),
        (255, 255, 255),
        2,
    )

    # Default RC values (no movement)
    yaw_velocity = 0
    forward_velocity = 0

    # Add mode indicator
    if DEBUG_MODE:
        mode_text = "DEBUG MODE"
    elif NO_TAKEOFF:
        mode_text = "NO TAKEOFF"
    else:
        mode_text = "DRONE FLYING"
    cv2.putText(
        img,
        mode_text,
        (width - 200, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2,
    )

    # Add detection count and parameters
    circle_count = len(circles[0]) if circles is not None else 0
    cv2.putText(
        img,
        f"Circles: {circle_count}",
        (width - 200, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 255),
        2,
    )
    cv2.putText(
        img,
        f"Blur: {blur_kernel}x{blur_kernel}, {blur_sigma}",
        (width - 200, 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 255),
        1,
    )
    cv2.putText(
        img,
        f"dp: {dp:.1f}",
        (width - 200, 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 255),
        1,
    )

    if circles is not None:
        circles = np.uint16(np.around(circles))
        # Find the smallest circle (furthest/priority target)
        smallest_circle = min(circles[0, :], key=lambda c: c[2])
        circle_x, circle_y, circle_radius = smallest_circle

        # Only navigate if circle is large enough
        if circle_radius >= TARGET_RADIUS_MIN:
            # Calculate horizontal offset from center
            offset_x = circle_x - frame_center_x

            # Calculate yaw rotation (negative to turn towards circle)
            yaw_velocity = int(-offset_x * YAW_SENSITIVITY)
            # Clamp yaw velocity
            yaw_velocity = max(-100, min(100, yaw_velocity))

            # Move forward if reasonably centered
            if abs(offset_x) < CENTER_TOLERANCE:
                forward_velocity = FORWARD_SPEED

            # Draw the target circle in green
            cv2.circle(img, (circle_x, circle_y), circle_radius, (0, 255, 0), 3)
            cv2.circle(img, (circle_x, circle_y), 3, (0, 0, 255), 5)

            # Draw line from center to circle center
            cv2.line(
                img,
                (frame_center_x, frame_center_y),
                (circle_x, circle_y),
                (255, 0, 255),
                2,
            )

            # Display offset info
            cv2.putText(
                img,
                f"Offset: {offset_x}px",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                img,
                f"Yaw: {yaw_velocity}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )
            cv2.putText(
                img,
                f"Forward: {forward_velocity}",
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

        # Draw all detected circles
        for i in circles[0, :]:
            # Check if this is the target (smallest) circle
            is_target = i[0] == circle_x and i[1] == circle_y and i[2] == circle_radius
            color = (0, 255, 0) if is_target else (100, 100, 100)
            thickness = 3 if is_target else 1

            # draw the outer circle
            cv2.circle(img, (i[0], i[1]), i[2], color, thickness)
            # draw the center of the circle
            cv2.circle(img, (i[0], i[1]), 2, (0, 0, 255), 3)

            # Show radius value
            cv2.putText(
                img,
                f"r:{i[2]}",
                (i[0] + 5, i[1] - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )
    else:
        # No circles detected - stop
        cv2.putText(
            img,
            "No target detected",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
        )

    # Send RC control commands to drone (only if not in debug mode)
    if not DEBUG_MODE:
        # rc(left_right, forward_backward, up_down, yaw)
        tello.send_rc_control(0, forward_velocity, 0, yaw_velocity)

    cv2.imshow("Circle Detection", img)
    time.sleep(1 / 15)
    # Press 'q' or ESC to quit
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q") or key == 27:
        break

# Clean shutdown
print("\nShutting down...")
emergency_landing()

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
