import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np

from config import VECTOR_STORE_DIR, TOP_K_RETRIEVAL, SIMILARITY_THRESHOLD
from src.embeddings import EmbeddingManager

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, store_dir: Path = VECTOR_STORE_DIR):
        self.store_dir = store_dir
        self.index_file = self.store_dir / "faiss_index.bin"
        self.metadata_file = self.store_dir / "chunks_metadata.json"
        self.embedding_mgr = EmbeddingManager()
        self.index = None
        self.chunks: List[Dict[str, Any]] = []
        self.load()

    def load(self) -> bool:
        """
        Loads persisted FAISS index and chunk metadata from disk.
        """
        import faiss
        if self.index_file.exists() and self.metadata_file.exists():
            try:
                self.index = faiss.read_index(str(self.index_file))
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors and {len(self.chunks)} metadata items.")
                return True
            except Exception as e:
                logger.error(f"Error loading FAISS index: {e}")
        return False

    def save(self):
        """
        Persists FAISS index and chunk metadata to disk.
        """
        import faiss
        if self.index is not None:
            faiss.write_index(self.index, str(self.index_file))
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, indent=2, ensure_ascii=False)
            logger.info("Vector store persisted successfully.")

    def build_index(self, chunks: List[Dict[str, Any]], progress_callback = None) -> int:
        """
        Builds a fresh FAISS index using cosine similarity (Inner Product on normalized vectors).
        """
        import faiss
        if not chunks:
            return 0

        texts = [c["text"] for c in chunks]
        if progress_callback:
            progress_callback(0.2, f"Computing embeddings for {len(texts)} chunks...")

        embeddings = self.embedding_mgr.embed_texts(texts)
        dimension = embeddings.shape[1]

        # Use IndexFlatIP for cosine similarity on normalized vectors
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)
        self.chunks = chunks
        self.save()

        if progress_callback:
            progress_callback(1.0, f"FAISS index built and saved with {len(chunks)} chunks.")
        return len(chunks)

    def search(self, query: str, top_k: int = TOP_K_RETRIEVAL) -> List[Dict[str, Any]]:
        """
        Performs multilingual semantic search.
        Returns top matches with score, source, page, text, chunk_id.
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        query_vec = self.embedding_mgr.embed_query(query)
        scores, indices = self.index.search(query_vec, min(top_k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            chunk = dict(self.chunks[idx])
            chunk["score"] = float(score)
            results.append(chunk)

        return results

    def is_indexed(self) -> bool:
        return self.index is not None and self.index.ntotal > 0 and len(self.chunks) > 0

