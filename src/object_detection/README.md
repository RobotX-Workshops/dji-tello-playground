# Object Detection Module

This module implements basic object detection algorithms. It provides functionality for detecting circular objects (via the Hough Circle Transform) and straight lines (via Canny edge detection + the Hough Line Transform) in images using computer vision techniques.

## Files

- `circles_detection.py` — `CircleDetector.detect_circles(img)` finds circles with `cv2.HoughCircles` and displays them. Run: `python src/object_detection/circles_detection.py` (uses the bundled `circles.jpg`).
- `canny_line_detection.py` — `LineDetector.detect_lines(img)` finds straight lines with Canny edge detection + `cv2.HoughLines` and displays them. Run: `python src/object_detection/canny_line_detection.py` (uses the bundled `lines.png`).
- `utils.py` — shared drawing/geometry helpers (`draw_object_mask`, `draw_object_box`, `get_frame_box_dimensions_delta`) used to render detector output; not a standalone script.

Both demo scripts open a window and block on a keypress (`cv2.waitKey(0)`) — press any key to close it.
