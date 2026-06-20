# core/vision/preprocessor.py
"""Image Preprocessing Pipeline for TrafficVision AI.

Provides a multi-stage image preprocessing pipeline optimized for
traffic surveillance footage, including low-light enhancement,
denoising, and motion blur correction.
"""

from typing import List, Tuple

import cv2
import numpy as np


def preprocess_image(image_path: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Run the full preprocessing pipeline on a traffic surveillance image.

    The pipeline applies the following stages in order:
        1. CLAHE (Contrast Limited Adaptive Histogram Equalization) for
           low-light / uneven-illumination enhancement.
        2. Non-local means denoising (``cv2.fastNlMeansDenoisingColored``)
           to suppress sensor noise while preserving edges.
        3. Sharpening via an unsharp-mask kernel to counteract motion blur
           commonly present in traffic camera feeds.

    Args:
        image_path: Absolute or relative path to the input image file.

    Returns:
        A tuple of ``(original_image, processed_image, logs)`` where:
            - ``original_image`` is the unmodified BGR image read from disk.
            - ``processed_image`` is the fully preprocessed BGR image.
            - ``logs`` is a list of terminal-style log strings describing
              each pipeline stage and its outcome.

    Raises:
        FileNotFoundError: If the image cannot be read from ``image_path``.
    """
    logs: List[str] = []

    # ------------------------------------------------------------------
    # Stage 0: Read image from disk
    # ------------------------------------------------------------------
    logs.append(f"[PREPROCESS] Reading image from '{image_path}'...")
    original_image: np.ndarray = cv2.imread(image_path)

    if original_image is None:
        error_msg = f"[PREPROCESS] ERROR: Unable to read image at '{image_path}'."
        logs.append(error_msg)
        raise FileNotFoundError(error_msg)

    height, width = original_image.shape[:2]
    logs.append(
        f"[PREPROCESS] Image loaded successfully — "
        f"{width}×{height} px, {original_image.shape[2]} channels. Done."
    )

    # Work on a copy so the original stays untouched.
    processed: np.ndarray = original_image.copy()

    # ------------------------------------------------------------------
    # Stage 1: CLAHE — Contrast Limited Adaptive Histogram Equalization
    # ------------------------------------------------------------------
    logs.append("[PREPROCESS] Applying CLAHE enhancement...")

    lab_image: np.ndarray = cv2.cvtColor(processed, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab_image)

    clahe: cv2.CLAHE = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l_enhanced: np.ndarray = clahe.apply(l_channel)

    lab_enhanced: np.ndarray = cv2.merge([l_enhanced, a_channel, b_channel])
    processed = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

    logs.append("[PREPROCESS] Applying CLAHE enhancement... Done.")

    # ------------------------------------------------------------------
    # Stage 2: Non-local means denoising (colour-aware)
    # ------------------------------------------------------------------
    logs.append("[PREPROCESS] Applying Gaussian denoising (fastNlMeansDenoisingColored)...")

    processed = cv2.fastNlMeansDenoisingColored(
        processed,
        None,
        h=6,                 # Filter strength for luminance
        hForColorComponents=6,  # Filter strength for colour components
        templateWindowSize=7,
        searchWindowSize=21,
    )

    logs.append(
        "[PREPROCESS] Applying Gaussian denoising (fastNlMeansDenoisingColored)... Done."
    )

    # ------------------------------------------------------------------
    # Stage 3: Motion-blur correction via sharpening kernel
    # ------------------------------------------------------------------
    logs.append("[PREPROCESS] Applying motion blur correction (sharpening kernel)...")

    sharpening_kernel: np.ndarray = np.array(
        [
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0],
        ],
        dtype=np.float32,
    )
    processed = cv2.filter2D(processed, ddepth=-1, kernel=sharpening_kernel)

    logs.append(
        "[PREPROCESS] Applying motion blur correction (sharpening kernel)... Done."
    )

    # ------------------------------------------------------------------
    # Pipeline complete
    # ------------------------------------------------------------------
    logs.append("[PREPROCESS] ✔ Preprocessing pipeline complete.")

    return original_image, processed, logs
