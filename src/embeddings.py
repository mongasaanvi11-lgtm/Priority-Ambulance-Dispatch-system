import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from config import VECTOR_STORE_DIR, EMBEDDING_MODEL_NAME

logger = logging.getLogger(__name__)

class EmbeddingManager:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME, store_dir: Path = VECTOR_STORE_DIR):
        self.model_name = model_name
        self.store_dir = store_dir
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.model = None

    def _load_model(self):
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
        return self.model

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        model = self._load_model()
        # Returns normalized float32 embeddings for inner product / cosine similarity
        embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(embeddings, dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        return self.embed_texts([query])

