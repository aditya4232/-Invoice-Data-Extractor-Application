"""
OCR Module for Invoice Data Extractor.

Handles image loading, preprocessing, and text extraction using Tesseract OCR.
Optimized preprocessing pipeline: denoise -> CLAHE -> adaptive threshold -> upscale.
Supports image files (JPG, PNG, BMP, TIFF) and PDF documents.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from PIL import Image

try:
    import pytesseract

    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from pdf2image import convert_from_path

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tiff",
    ".tif",
    ".gif",
    ".pdf",
}

OCR_CONFIG_DEFAULT = r"--oem 3 --psm 6"
OCR_CONFIG_SPARSE = r"--oem 3 --psm 11"


class OCRExtractor:
    """Extracts text from invoice images and PDFs using Tesseract OCR."""

    def __init__(self, tesseract_cmd: Optional[str] = None):
        if not TESSERACT_AVAILABLE:
            raise ImportError(
                "pytesseract is not installed. Run: pip install pytesseract"
            )

        tesseract_path = (
            tesseract_cmd
            or os.getenv("TESSERACT_CMD", "")
            or self._auto_detect_tesseract()
        )
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        self._verify_tesseract()

        self.preprocess_default = (
            os.getenv("PREPROCESS_DEFAULT", "True").lower() == "true"
        )
        self.confidence_threshold = int(os.getenv("CONFIDENCE_THRESHOLD", "50"))

    @staticmethod
    def _auto_detect_tesseract() -> str:
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        if sys.platform == "win32":
            for path in common_paths:
                if os.path.isfile(path):
                    return path
        return ""

    def _verify_tesseract(self):
        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            raise EnvironmentError(
                "\n" + "=" * 60 + "\n"
                "Tesseract OCR is not installed or not in PATH.\n\n"
                "Installation instructions:\n"
                "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki\n"
                "  macOS:   brew install tesseract\n"
                "  Linux:   sudo apt-get install tesseract-ocr\n\n"
                "After installing, either:\n"
                "  1. Add Tesseract to your system PATH, or\n"
                "  2. Set TESSERACT_CMD in your .env file\n" + "=" * 60
            )

    def extract_text(
        self,
        file_path: str,
        preprocess: Optional[bool] = None,
        page: Optional[int] = None,
        config: Optional[str] = None,
    ) -> str:
        if preprocess is None:
            preprocess = self.preprocess_default

        file_path = str(Path(file_path).resolve())
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = Path(file_path).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file format: {ext}. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

        ocr_config = config or OCR_CONFIG_DEFAULT

        if ext == ".pdf":
            images = self.pdf_to_images(file_path)
            if page is not None and 0 <= page < len(images):
                images = [images[page]]
            text_parts = []
            for img in images:
                if preprocess:
                    img = self.preprocess_image(img)
                text_parts.append(pytesseract.image_to_string(img, config=ocr_config))
            return "\n\n".join(text_parts)

        image = self._load_image(file_path)
        if image is None:
            raise ValueError(f"Could not load image: {file_path}")

        if preprocess:
            image = self.preprocess_image(image)

        main_text = pytesseract.image_to_string(image, config=ocr_config)

        sparse_text = ""
        try:
            sparse_text = pytesseract.image_to_string(image, config=OCR_CONFIG_SPARSE)
        except Exception:
            pass

        return self._merge_ocr_results(main_text, sparse_text)

    def extract_text_multi_pass(
        self, file_path: str, preprocess: Optional[bool] = None
    ) -> str:
        if preprocess is None:
            preprocess = self.preprocess_default

        file_path = str(Path(file_path).resolve())
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        image = self._load_image(file_path)
        if image is None:
            raise ValueError(f"Could not load image: {file_path}")

        if preprocess:
            image = self.preprocess_image(image)

        results = []
        for config in [r"--oem 3 --psm 6", r"--oem 3 --psm 4", r"--oem 3 --psm 3"]:
            try:
                text = pytesseract.image_to_string(image, config=config)
                results.append(text)
            except Exception:
                continue

        return self._merge_ocr_results(*results)

    def _merge_ocr_results(self, *texts: str) -> str:
        if not texts:
            return ""

        if len(texts) == 1:
            return texts[0]

        main_lines = texts[0].split("\n")
        merged = list(main_lines)

        for alt_text in texts[1:]:
            for line in alt_text.split("\n"):
                line_stripped = line.strip()
                if line_stripped and line_stripped not in [
                    l.strip() for l in merged if l.strip()
                ]:
                    similarity = False
                    for existing in merged:
                        if (
                            line_stripped in existing.strip()
                            or existing.strip() in line_stripped
                        ):
                            similarity = True
                            break
                    if not similarity:
                        merged.append(line)

        return "\n".join(merged)

    def get_confidence(self, file_path: str) -> float:
        file_path = str(Path(file_path).resolve())
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            images = self.pdf_to_images(file_path)
            image = images[0]
        else:
            image = self._load_image(file_path)
            if image is None:
                return 0.0

        image = self.preprocess_image(image)
        data = pytesseract.image_to_data(
            image, output_type=pytesseract.Output.DICT, config=OCR_CONFIG_DEFAULT
        )

        confidences = [int(c) for c in data["conf"] if int(c) > 0]
        if not confidences:
            return 0.0

        return sum(confidences) / len(confidences)

    def preprocess_image(self, image: np.ndarray, method: str = "advanced") -> np.ndarray:
        """Preprocess image for better OCR accuracy.
        
        Args:
            image: Input image (numpy array)
            method: Preprocessing method - 'basic', 'advanced', or 'aggressive'
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        h, w = gray.shape
        target_min = 1500
        if h < target_min or w < target_min:
            scale = max(target_min / h, target_min / w)
            gray = cv2.resize(
                gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
            )

        if method == "basic":
            # Simple thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            return thresh

        elif method == "advanced":
            # Denoise -> CLAHE -> Adaptive threshold -> Morph close
            try:
                denoised = cv2.fastNlMeansDenoising(
                    gray, None, h=10, templateWindowSize=7, searchWindowSize=21
                )
            except Exception:
                denoised = cv2.bilateralFilter(gray, 9, 75, 75)

            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)

            thresh = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

            return processed

        elif method == "aggressive":
            # For very poor quality images
            # Strong denoising
            denoised = cv2.fastNlMeansDenoising(
                gray, None, h=20, templateWindowSize=10, searchWindowSize=30
            )

            # Strong CLAHE
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
            enhanced = clahe.apply(denoised)

            # Otsu's thresholding
            _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)

            return processed

        else:
            # Default to advanced
            return self.preprocess_image(image, method="advanced")

    def pdf_to_images(self, pdf_path: str) -> List[np.ndarray]:
        if not PDF_AVAILABLE:
            raise ImportError(
                "pdf2image is not installed. Run: pip install pdf2image\n"
                "Also install poppler:\n"
                "  Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases\n"
                "  macOS:   brew install poppler\n"
                "  Linux:   sudo apt-get install poppler-utils"
            )

        pdf_path = str(Path(pdf_path).resolve())
        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            pil_images = convert_from_path(pdf_path, dpi=300)
        except Exception as e:
            raise RuntimeError(
                f"Failed to convert PDF: {e}. Ensure poppler is installed."
            )

        images = []
        for pil_img in pil_images:
            img_array = np.array(pil_img)
            if len(img_array.shape) == 2:
                images.append(img_array)
            elif img_array.shape[2] == 4:
                images.append(cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR))
            else:
                images.append(cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR))

        return images

    def _load_image(self, file_path: str) -> Optional[np.ndarray]:
        try:
            image = cv2.imread(file_path, cv2.IMREAD_COLOR)
            if image is not None:
                return image
        except Exception:
            pass

        try:
            pil_image = Image.open(file_path)
            if pil_image.mode == "RGBA":
                background = Image.new("RGB", pil_image.size, (255, 255, 255))
                background.paste(pil_image, mask=pil_image.split()[3])
                pil_image = background
            elif pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

            img_array = np.array(pil_image)
            return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Failed to load image {file_path}: {e}")
            return None
