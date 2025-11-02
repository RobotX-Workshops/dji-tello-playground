from typing import Literal, Sequence
import face_recognition  # type: ignore

import cv2

try:
    from open_cv_wrapper import OpenCvWrapper
    from face_identifier import AbstractFaceIdentifier
    from image_compression_service import ImageCompressionService

except ModuleNotFoundError:
    from face_tracking.open_cv_wrapper import OpenCvWrapper
    from face_tracking.face_identifier import AbstractFaceIdentifier
    from face_tracking.image_compression_service import ImageCompressionService


class RecognitionFaceIdentifier(AbstractFaceIdentifier):
    def __init__(
        self,
        open_cv: OpenCvWrapper,
        image_compression_service: ImageCompressionService,
        model: Literal["hog", "cnn"] = "hog",
        compression_factor: int = 4,
    ):
        self._face_cascade = open_cv.get_face_classifier()
        self.open_cv = open_cv
        self.model = model
        self.image_compression = image_compression_service
        self.image_compression_factor = compression_factor

    def identify_faces(self, frame: cv2.typing.MatLike) -> Sequence[cv2.typing.Rect]:

        compression_factor = self.image_compression_factor
        compressed_image = self.image_compression.compress_image(
            frame, compression_factor
        )
        face_locations = face_recognition.face_locations(
            compressed_image, model=self.model
        )
        original_face_locations = []
        for top, right, bottom, left in face_locations:
            original_top = top * compression_factor
            original_right = right * compression_factor
            original_bottom = bottom * compression_factor
            original_left = left * compression_factor
            original_face_locations.append(
                (original_top, original_right, original_bottom, original_left)
            )

        return original_face_locations
