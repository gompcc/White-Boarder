"""Webcam capture using OpenCV."""

import os
import time
import cv2


def capture_photo(output_dir: str) -> str | None:
    """Capture a single frame from the Mac front camera and save it.

    Returns the file path of the saved photo, or None on failure.
    """
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return None

    # Allow camera to auto-adjust exposure/white balance
    for _ in range(10):
        cap.read()

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        return None

    filename = f"whiteboard_{int(time.time())}.jpg"
    filepath = os.path.join(output_dir, filename)
    cv2.imwrite(filepath, frame)
    return filepath
