from typing import Tuple, Union
import cv2
import numpy as np


def get_frame_center_xy(frame: np.ndarray) -> Tuple[int, int]:
    """
    Calculates the center coordinates of a frame.

    Args:
        frame (np.ndarray): The input frame.

    Returns:
        Tuple[int, int]: The x and y coordinates of the center of the frame.
    """
    height, width = frame.shape[:2]
    return width // 2, height // 2


def get_box_center_xy(
    box: Union[cv2.typing.Rect, Tuple[int, int, int, int]]
) -> Tuple[int, int]:
    """
    Calculates the center coordinates of a bounding box.

    Args:
        box (Tuple[int, int, int, int]): A tuple representing the coordinates of the bounding box in the format
            (top, right, bottom, left).

    Returns:
        Tuple[int, int]: A tuple representing the center coordinates of the bounding box in the format (x, y).
    """
    top, right, bottom, left = box
    return (left + right) // 2, (top + bottom) // 2


def get_box_center_xyz(
    box: Union[cv2.typing.Rect, Tuple[int, int, int, int]], depth_target: int
) -> Tuple[int, int, int]:
    """
    Calculates the center coordinates and depth of a bounding box.

    Args:
        box (Union[Tuple[int, int, int, int], cv2.typing.Rect]):
            A tuple representing the coordinates of the bounding box in the format (top, right, bottom, left).
        depth_target (int):
            The target depth value used to calculate the depth of the bounding box.

    Returns:
        Tuple[int, int, int]: A tuple representing the center coordinates of the bounding box in the format (x, y, z),
        where z is the estimated depth based on the box size and the target depth value.
    """
    top, right, bottom, left = box

    center_x = (left + right) // 2
    center_y = (top + bottom) // 2

    # Simple depth estimation based on the average of width and height
    width = right - left
    height = bottom - top
    box_size = (width + height) // 2

    return center_x, center_y, depth_target - box_size


def get_distance_xy(point1: Tuple[int, int], point2: Tuple[int, int]) -> float:
    """
    Calculates the Euclidean distance between two points in a 2D plane.

    Args:
        point1 (Tuple[int, int]): The coordinates of the first point.
        point2 (Tuple[int, int]): The coordinates of the second point.

    Returns:
        float: The Euclidean distance between the two points.
    """
    x1, y1 = point1
    x2, y2 = point2
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def get_distance_xyz(
    point1: Tuple[int, int, int], point2: Tuple[int, int, int]
) -> float:
    """
    Calculates the Euclidean distance between two points in a 3D space.

    Args:
        point1 (Tuple[int, int, int]): The coordinates of the first point in the format (x, y, z).
        point2 (Tuple[int, int, int]): The coordinates of the second point in the format (x, y, z).

    Returns:
        float: The Euclidean distance between the two points.
    """
    x1, y1, z1 = point1
    x2, y2, z2 = point2
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2) ** 0.5


def get_vector_xy(point1: Tuple[int, int], point2: Tuple[int, int]) -> Tuple[int, int]:
    """
    Calculates the vector between two points.

    Args:
        point1 (Tuple[int, int]): The coordinates of the first point.
        point2 (Tuple[int, int]): The coordinates of the second point.

    Returns:
        Tuple[int, int]: The vector representing the difference between the two points.
    """
    x1, y1 = point1
    x2, y2 = point2
    return x2 - x1, y2 - y1


def get_vector_xyz(
    point1: Tuple[int, int, int], point2: Tuple[int, int, int]
) -> Tuple[int, int, int]:
    """
    Calculates the vector between two points in 3D space.

    Args:
        point1 (Tuple[int, int, int]): The coordinates of the first point in the format (x, y, z).
        point2 (Tuple[int, int, int]): The coordinates of the second point in the format (x, y, z).

    Returns:
        Tuple[int, int, int]: The vector representing the difference between the two points in the format (dx, dy, dz).
    """
    x1, y1, z1 = point1
    x2, y2, z2 = point2
    return x2 - x1, y2 - y1, z2 - z1


def get_box_size(box: Tuple[int, int, int, int]) -> Tuple[int, int]:
    """
    Calculate the size of a bounding box.

    Args:
        box (Tuple[int, int, int, int]): The coordinates of the bounding box in the format (top, right, bottom, left).

    Returns:
        Tuple[int, int]: The width and height of the bounding box.

    """
    top, right, bottom, left = box
    return right - left, bottom - top
