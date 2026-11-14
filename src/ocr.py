import os
import shutil
import logging
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)

# Check if tesseract binary is available on system
def is_tesseract_available() -> bool:
    try:
        import pytesseract
        # On Windows, commonly installed in Program Files
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
        ]
        if shutil.which("tesseract"):
            return True
        for p in common_paths:
            if os.path.exists(p):
                pytesseract.pytesseract.tesseract_cmd = p
                return True
        return False
    except Exception:
        return False

def ocr_page_image(pil_image: Image.Image) -> str:
    """
    Run OCR on a page image using pytesseract if available.
    Returns extracted text or empty string.
    """
    try:
        import pytesseract
        if is_tesseract_available():
            text = pytesseract.image_to_string(pil_image)
            return text.strip()
    except Exception as e:
        logger.warning(f"OCR execution failed: {e}")
    return ""

