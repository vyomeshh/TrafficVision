"""
TrafficVision AI - License Plate Reader
========================================
End-to-end pipeline for detecting, enhancing, and reading license plates
from vehicle detections using PaddleOCR and OpenCV.
"""

import re
import logging
import numpy as np
import cv2

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PlateReader:
    """License plate recognition pipeline.

    Uses PaddleOCR for text extraction and OpenCV for plate region
    detection and image enhancement.  Falls back gracefully when
    PaddleOCR is not installed.
    """

    # Regex for standard Indian vehicle registration plates.
    # Matches formats like: DL 4C AB 1234, MH12LK9021, KA03MD4392
    INDIAN_PLATE_PATTERN = re.compile(
        r'^[A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,3}\s?\d{4}$'
    )

    # -----------------------------------------------------------------
    # Initialisation
    # -----------------------------------------------------------------
    def __init__(self):
        """Initialise PaddleOCR with English language and angle classification."""
        if PADDLEOCR_AVAILABLE:
            logger.info("Initialising PaddleOCR engine (lang=en, angle_cls=True)…")
            self.ocr = PaddleOCR(
                lang='en',
                use_angle_cls=True,
                show_log=False,          # suppress PaddleOCR internal logs
            )
            logger.info("PaddleOCR engine ready.")
        else:
            logger.warning(
                "PaddleOCR is not installed. PlateReader will return empty "
                "results. Install with: pip install paddlepaddle paddleocr"
            )
            self.ocr = None

    # -----------------------------------------------------------------
    # 1. Plate Region Detection
    # -----------------------------------------------------------------
    def detect_plate_region(self, image: np.ndarray, detections: list) -> list:
        """Locate candidate license-plate crops inside each vehicle bbox.

        For every vehicle detection the method examines the **lower 40 %**
        of the bounding box (where plates are most likely to appear) and
        uses contour analysis to find rectangular sub-regions.

        Parameters
        ----------
        image : np.ndarray
            Full frame (BGR, as returned by ``cv2.imread``).
        detections : list[dict]
            Each dict must contain a ``'bbox'`` key whose value is
            ``[x1, y1, x2, y2]`` (pixel coordinates).

        Returns
        -------
        list[dict]
            Each entry: ``{'plate_crop': np.ndarray, 'plate_bbox': [...],
            'vehicle_bbox': [...]}``
        """
        results = []

        if image is None or len(image) == 0:
            logger.error("detect_plate_region received an empty image.")
            return results

        img_h, img_w = image.shape[:2]

        for det in detections:
            bbox = det.get('bbox')
            if bbox is None or len(bbox) != 4:
                logger.warning("Skipping detection with invalid bbox: %s", det)
                continue

            x1, y1, x2, y2 = [int(c) for c in bbox]

            # Clamp to image boundaries
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(img_w, x2)
            y2 = min(img_h, y2)

            veh_h = y2 - y1
            veh_w = x2 - x1

            if veh_h <= 0 or veh_w <= 0:
                logger.warning("Degenerate vehicle bbox after clamping: %s", bbox)
                continue

            # Focus on the lower 40 % of the vehicle bbox
            lower_y1 = y1 + int(veh_h * 0.6)
            roi = image[lower_y1:y2, x1:x2]

            if roi.size == 0:
                logger.debug("Empty ROI for bbox %s – skipping.", bbox)
                continue

            # Convert to grey and apply edge detection
            grey = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(grey, (5, 5), 0)
            edges = cv2.Canny(blurred, 100, 200)

            # Morphological close to join nearby edges
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3))
            closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(
                closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            plate_found = False
            for cnt in sorted(contours, key=cv2.contourArea, reverse=True):
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

                # A plate is roughly rectangular (4 vertices)
                if len(approx) < 4 or len(approx) > 6:
                    continue

                cx, cy, cw, ch = cv2.boundingRect(approx)
                aspect_ratio = cw / max(ch, 1)

                # Indian plates have aspect ratios roughly between 2 and 6
                if not (1.5 <= aspect_ratio <= 7.0):
                    continue

                # Minimum area check (ignore tiny artefacts)
                if cw * ch < 300:
                    continue

                plate_crop = roi[cy:cy + ch, cx:cx + cw]
                plate_bbox_abs = [
                    x1 + cx,
                    lower_y1 + cy,
                    x1 + cx + cw,
                    lower_y1 + cy + ch,
                ]

                logger.debug(
                    "Plate candidate found – aspect=%.2f, area=%d, bbox=%s",
                    aspect_ratio, cw * ch, plate_bbox_abs,
                )

                results.append({
                    'plate_crop': plate_crop,
                    'plate_bbox': plate_bbox_abs,
                    'vehicle_bbox': [x1, y1, x2, y2],
                })
                plate_found = True
                break  # take the best (largest) candidate per vehicle

            if not plate_found:
                # Fallback: use entire lower-40 % ROI as the plate crop
                logger.debug(
                    "No rectangular contour found for bbox %s – "
                    "using full lower ROI as fallback.", bbox,
                )
                results.append({
                    'plate_crop': roi,
                    'plate_bbox': [x1, lower_y1, x2, y2],
                    'vehicle_bbox': [x1, y1, x2, y2],
                })

        logger.info(
            "detect_plate_region: %d plate region(s) from %d detection(s).",
            len(results), len(detections),
        )
        return results

    # -----------------------------------------------------------------
    # 2. Image Enhancement
    # -----------------------------------------------------------------
    @staticmethod
    def enhance_plate(plate_crop: np.ndarray) -> np.ndarray:
        """Enhance a plate crop for optimal OCR accuracy.

        Pipeline: greyscale → bilateral filter → adaptive threshold →
        morphological opening (noise removal).

        Parameters
        ----------
        plate_crop : np.ndarray
            BGR image of the plate region.

        Returns
        -------
        np.ndarray
            Binary (thresholded) image ready for OCR.
        """
        if plate_crop is None or plate_crop.size == 0:
            logger.warning("enhance_plate received empty crop – returning as-is.")
            return plate_crop

        # Greyscale conversion
        if len(plate_crop.shape) == 3:
            grey = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        else:
            grey = plate_crop.copy()

        # Resize to a reasonable width for consistent OCR quality
        target_width = 300
        h, w = grey.shape[:2]
        if w > 0 and h > 0:
            scale = target_width / w
            grey = cv2.resize(
                grey, (target_width, int(h * scale)),
                interpolation=cv2.INTER_CUBIC,
            )

        # Bilateral filter – removes noise while keeping edges sharp
        filtered = cv2.bilateralFilter(grey, d=11, sigmaColor=17, sigmaSpace=17)

        # Adaptive threshold – handles uneven lighting on plates
        thresh = cv2.adaptiveThreshold(
            filtered, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=11,
            C=2,
        )

        # Morphological opening – remove small noise blobs
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

        logger.debug(
            "enhance_plate: output shape=%s, dtype=%s",
            opened.shape, opened.dtype,
        )
        return opened

    # -----------------------------------------------------------------
    # 3. OCR Text Extraction
    # -----------------------------------------------------------------
    def read_plate(self, plate_crop: np.ndarray) -> tuple:
        """Run PaddleOCR on an (optionally enhanced) plate crop.

        Parameters
        ----------
        plate_crop : np.ndarray
            Image of the plate (colour or binary).

        Returns
        -------
        tuple[str, float]
            ``(extracted_text, confidence)``  where *text* is the
            concatenated OCR output uppercased and *confidence* is the
            average confidence across all detected text lines.
        """
        if self.ocr is None:
            logger.warning("OCR engine unavailable – returning empty text.")
            return ('', 0.0)

        if plate_crop is None or plate_crop.size == 0:
            logger.warning("read_plate received empty image.")
            return ('', 0.0)

        # PaddleOCR expects a BGR or greyscale numpy array
        try:
            result = self.ocr.ocr(plate_crop, cls=True)
        except Exception as exc:
            logger.error("PaddleOCR inference failed: %s", exc)
            return ('', 0.0)

        texts = []
        confidences = []

        if result and result[0]:
            for line in result[0]:
                # Each line: [box_coords, (text, confidence)]
                if line and len(line) >= 2:
                    text_part = line[1]
                    if isinstance(text_part, (list, tuple)) and len(text_part) >= 2:
                        texts.append(str(text_part[0]))
                        confidences.append(float(text_part[1]))

        raw_text = ' '.join(texts).upper().strip()
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        logger.debug("read_plate raw OCR: '%s' (conf=%.3f)", raw_text, avg_conf)
        return (raw_text, avg_conf)

    # -----------------------------------------------------------------
    # 4. Indian Plate Validation
    # -----------------------------------------------------------------
    def validate_indian_plate(self, text: str) -> bool:
        """Check whether *text* matches a standard Indian registration format.

        Supported patterns (with or without spaces):
        - ``DL 4C AB 1234``
        - ``MH12LK9021``
        - ``KA03MD4392``

        Parameters
        ----------
        text : str
            Candidate plate string (should already be uppercased).

        Returns
        -------
        bool
        """
        if not text:
            return False

        # Remove extraneous characters that OCR sometimes introduces
        cleaned = re.sub(r'[^A-Z0-9\s]', '', text.upper().strip())
        is_valid = bool(self.INDIAN_PLATE_PATTERN.match(cleaned))

        logger.debug(
            "validate_indian_plate: '%s' → cleaned='%s' → valid=%s",
            text, cleaned, is_valid,
        )
        return is_valid

    # -----------------------------------------------------------------
    # 5. Full Processing Pipeline
    # -----------------------------------------------------------------
    def process(self, image: np.ndarray, detections: list) -> list:
        """End-to-end license plate recognition.

        Steps:
        1. Detect plate regions within each vehicle bounding box.
        2. Enhance each plate crop for OCR.
        3. Run PaddleOCR to extract text.
        4. Validate against Indian plate format.

        Parameters
        ----------
        image : np.ndarray
            Full frame (BGR).
        detections : list[dict]
            Vehicle detections, each with at least a ``'bbox'`` key.

        Returns
        -------
        list[dict]
            Each entry::

                {
                    'plate_text': str,
                    'confidence': float,
                    'bbox': [x1, y1, x2, y2],        # plate bbox
                    'vehicle_bbox': [x1, y1, x2, y2], # vehicle bbox
                    'is_valid': bool,
                }
        """
        logger.info(
            "PlateReader.process: starting pipeline for %d detection(s).",
            len(detections),
        )

        # Step 1 – locate plate regions
        plate_regions = self.detect_plate_region(image, detections)
        logger.info("Step 1 complete: %d plate region(s) found.", len(plate_regions))

        results = []

        for idx, region in enumerate(plate_regions):
            plate_crop = region['plate_crop']
            plate_bbox = region['plate_bbox']
            vehicle_bbox = region['vehicle_bbox']

            # Step 2 – enhance
            logger.debug("Step 2: enhancing plate crop #%d…", idx)
            enhanced = self.enhance_plate(plate_crop)

            # Step 3 – OCR
            logger.debug("Step 3: running OCR on plate crop #%d…", idx)
            # Try enhanced first; if confidence is low, retry on original crop
            plate_text, confidence = self.read_plate(enhanced)

            if confidence < 0.4 and plate_crop is not None and plate_crop.size > 0:
                logger.debug(
                    "Low confidence (%.3f) on enhanced crop – "
                    "retrying with original crop #%d.",
                    confidence, idx,
                )
                alt_text, alt_conf = self.read_plate(plate_crop)
                if alt_conf > confidence:
                    plate_text, confidence = alt_text, alt_conf

            # Step 4 – validate
            is_valid = self.validate_indian_plate(plate_text)
            logger.debug(
                "Step 4: plate #%d – text='%s', conf=%.3f, valid=%s",
                idx, plate_text, confidence, is_valid,
            )

            results.append({
                'plate_text': plate_text,
                'confidence': round(confidence, 4),
                'bbox': plate_bbox,
                'vehicle_bbox': vehicle_bbox,
                'is_valid': is_valid,
            })

        logger.info(
            "PlateReader.process: pipeline complete – %d result(s), "
            "%d valid plate(s).",
            len(results),
            sum(1 for r in results if r['is_valid']),
        )
        return results
