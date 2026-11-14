import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Generator, Tuple
from PIL import Image
import io

from src.ocr import is_tesseract_available, ocr_page_image
from config import BOOKS_DIR, PROCESSED_DIR

logger = logging.getLogger(__name__)

class PDFProcessor:
    def __init__(self, books_dir: Path = BOOKS_DIR, processed_dir: Path = PROCESSED_DIR):
        self.books_dir = books_dir
        self.processed_dir = processed_dir
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def discover_books(self) -> List[Dict[str, Any]]:
        """
        Discovers all PDF books in data/books/ with exact file sizes.
        """
        pdfs = list(self.books_dir.glob("*.pdf")) + list(self.books_dir.glob("*.PDF"))
        books_info = []
        # Remove duplicates if filesystem case-insensitive
        seen = set()
        for p in pdfs:
            resolved = str(p.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            size_mb = p.stat().st_size / (1024 * 1024)
            books_info.append({
                "filename": p.name,
                "filepath": str(p),
                "size_mb": round(size_mb, 2),
                "size_bytes": p.stat().st_size
            })
        return books_info

    def get_processed_cache_path(self, filename: str) -> Path:
        safe_name = "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in filename)
        return self.processed_dir / f"{safe_name}.json"

    def process_pdf(self, pdf_path: str, force_reprocess: bool = False, progress_callback = None) -> List[Dict[str, Any]]:
        """
        Extracts text from PDF page by page (1-based index).
        Handles memory efficiently. Uses OCR fallback if native text is sparse.
        Saves extracted pages to disk so reprocessing is not needed on every restart.
        """
        import fitz  # PyMuPDF
        
        pdf_file = Path(pdf_path)
        filename = pdf_file.name
        cache_file = self.get_processed_cache_path(filename)

        if not force_reprocess and cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    if progress_callback:
                        progress_callback(1.0, f"Loaded {filename} from cache ({len(cached_data)} pages).")
                    return cached_data
            except Exception as e:
                logger.warning(f"Failed to read cache for {filename}, re-processing: {e}")

        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        pages_data = []
        failed_pages = []

        tesseract_ready = is_tesseract_available()

        for page_idx in range(total_pages):
            page_num = page_idx + 1  # 1-based exact page number
            page = doc[page_idx]
            
            # Extract standard digital text
            text = page.get_text("text").strip()
            extraction_method = "native_pdf"

            # Check if page is scanned or sparse (less than 30 chars) and OCR is available
            if len(text) < 30 and tesseract_ready:
                try:
                    pix = page.get_pixmap(dpi=150)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    ocr_text = ocr_page_image(img)
                    if len(ocr_text) > len(text):
                        text = ocr_text
                        extraction_method = "tesseract_ocr"
                except Exception as ex:
                    logger.warning(f"OCR failed for page {page_num} of {filename}: {ex}")
                    failed_pages.append(page_num)

            if not text:
                failed_pages.append(page_num)
                extraction_method = "empty_or_failed"

            page_record = {
                "source": filename,
                "page": page_num,
                "text": text,
                "extraction_method": extraction_method,
                "char_count": len(text)
            }
            pages_data.append(page_record)

            if progress_callback and (page_num % 10 == 0 or page_num == total_pages):
                progress_callback(page_num / total_pages, f"Extracted page {page_num}/{total_pages} from {filename}")

        doc.close()

        # Save to disk cache
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(pages_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save extracted pages cache: {e}")

        return pages_data

