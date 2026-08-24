"""Shared per-frame face-tracking logic used by follow_face.py and mock_follow_face.py."""

import logging

import cv2

from face_tracking.utils.positioning_utils import (
    get_box_center_xyz,
    get_distance_xyz,
    get_frame_center_xy,
    get_vector_xyz,
)


def locate_and_draw_closest_face(
    frame,
    faces_trbl,
    image_drawer,
    depth_target: int,
    label_each_face: bool = False,
):
    """Draws every candidate face and picks the one closest to frame center.

    Returns `(frame, closest_box, closest_distance, closest_center, frame_center_xyz)`.
    `faces_trbl` must be non-empty.
    """
    frame_center_xyz = (*get_frame_center_xy(frame), depth_target)

    closest = None
    for face_trbl in faces_trbl:
        box_center = get_box_center_xyz(face_trbl, depth_target)
        distance = get_distance_xyz(frame_center_xyz, box_center)
        if closest is None or distance < closest[1]:
            closest = (face_trbl, distance, box_center)
        frame = image_drawer.draw_box(
            frame,
            face_trbl,
            "green",
            f"{box_center}" if label_each_face else "",
        )
        frame = image_drawer.draw_cross_hair_in_box(frame, face_trbl, 4, "green")

    assert (
        closest is not None
    ), "locate_and_draw_closest_face() requires at least one face"
    closest_box, closest_distance, closest_center = closest

    frame = image_drawer.draw_box(frame, closest_box, "red")
    frame = image_drawer.draw_frame_center_cross_hair(frame, 2, 20, "red")

    return frame, closest_box, closest_distance, closest_center, frame_center_xyz


def process_tracking_frame(
    frame,
    face_identifier,
    image_drawer,
    controller,
    open_cv,
    depth_target: int,
    logger: logging.Logger,
):
    """Identify faces in `frame`, draw the tracking overlays, and return the
    controller's control state for the closest face, or None if no face was found.
    """
    faces_trbl = face_identifier.identify_faces(frame)
    if not faces_trbl:
        logger.debug("No faces")
        # Keep the preview alive even with no face in frame so the window
        # refreshes and the caller's quit-key handling still runs.
        open_cv.write_text(
            frame,
            "No face detected",
            (10, frame.shape[0] - 10),
            cv2.FONT_HERSHEY_DUPLEX,
            0.5,
            (255, 255, 255),
            1,
        )
        open_cv.show_image("frame", frame)
        return None

    (
        frame,
        closest_box,
        closest_distance,
        closest_center,
        frame_center_xyz,
    ) = locate_and_draw_closest_face(frame, faces_trbl, image_drawer, depth_target)

    vector_to_center = get_vector_xyz(frame_center_xyz, closest_center)

    logger.debug(
        "Closest face at %s with distance %s",
        (frame_center_xyz, closest_center),
        closest_distance,
    )

    control_state = controller.get_state(vector_to_center)
    height = frame.shape[0]
    bottom = height - 10
    left = 10

    # Write the control state information on the frame
    open_cv.write_text(
        frame,
        f"Forward: {control_state.forward_velocity}, "
        f"Move Right: {control_state.right_velocity}, "
        f"Up: {control_state.up_velocity}, "
        f"Yaw Right: {control_state.yaw_right_velocity}",
        (left, bottom),
        cv2.FONT_HERSHEY_DUPLEX,
        0.5,  # Adjust the font scale as needed
        (255, 255, 255),
        1,
    )
    open_cv.show_image("frame", frame)

    return control_state
