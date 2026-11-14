import hashlib
import re
from typing import List, Dict, Any
from config import CHUNK_SIZE, CHUNK_OVERLAP

def compute_content_hash(text: str) -> str:
    cleaned = re.sub(r'\s+', ' ', text).strip().lower()
    return hashlib.sha256(cleaned.encode('utf-8')).hexdigest()

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Splits text into overlapping chunks respecting sentence or paragraph boundaries where possible.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        if end >= text_len:
            chunks.append(text[start:].strip())
            break

        # Look for natural paragraph or sentence break near the end
        boundary = -1
        # Check for paragraph break
        p_idx = text.rfind("\n\n", start + overlap, end)
        if p_idx != -1:
            boundary = p_idx + 2
        else:
            # Check for sentence ending (. or ! or ?)
            for punct in [". ", "? ", "! ", ".\n"]:
                s_idx = text.rfind(punct, start + overlap, end)
                if s_idx != -1:
                    boundary = s_idx + len(punct)
                    break

        if boundary == -1:
            # Break on whitespace
            space_idx = text.rfind(" ", start + overlap, end)
            if space_idx != -1:
                boundary = space_idx + 1
            else:
                boundary = end

        chunk_str = text[start:boundary].strip()
        if chunk_str:
            chunks.append(chunk_str)

        start = max(boundary - overlap, start + 1)

    return chunks

def create_chunks_from_pages(pages_data: List[Dict[str, Any]], existing_hashes: set = None) -> List[Dict[str, Any]]:
    """
    Creates overlapping chunks with complete metadata:
    - source (filename)
    - page (1-based integer)
    - chunk_id
    - extraction_method
    - content_hash (for duplicate detection)
    """
    if existing_hashes is None:
        existing_hashes = set()

    chunks_result = []

    for page_record in pages_data:
        text = page_record.get("text", "")
        source = page_record.get("source", "Unknown")
        page_num = page_record.get("page", 1)
        method = page_record.get("extraction_method", "native_pdf")

        if not text or len(text) < 15:
            continue

        raw_chunks = chunk_text(text)
        for idx, c_text in enumerate(raw_chunks):
            chash = compute_content_hash(c_text)
            if chash in existing_hashes:
                continue  # duplicate chunk detected
            existing_hashes.add(chash)

            chunk_id = f"{source}_p{page_num}_c{idx+1}"
            chunks_result.append({
                "chunk_id": chunk_id,
                "source": source,
                "page": page_num,
                "text": c_text,
                "extraction_method": method,
                "content_hash": chash
            })

    return chunks_result

