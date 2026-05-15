"""
EduFlow — FAISS vector store for semantic similarity checks.
Used by the Integrity Agent (plagiarism) and Ghost School Agent (mass-copying).
"""

import logging
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import faiss
    from sentence_transformers import SentenceTransformer
    FAISS_AVAILABLE = True
except (ImportError, OSError, Exception) as _e:
    FAISS_AVAILABLE = False
    logger.warning(f"FAISS/sentence-transformers unavailable ({_e}). Similarity checks disabled.")

EMBEDDING_DIM = 384   # all-MiniLM-L6-v2 output size


class FAISSStore:
    """
    In-process FAISS index. One instance lives for the lifetime of the server.
    Submissions are indexed by submission_id string; results return (id, score) tuples.
    """

    def __init__(self):
        if not FAISS_AVAILABLE:
            self.enabled = False
            return
        self.enabled = True
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.IndexFlatIP(EMBEDDING_DIM)   # inner-product = cosine on normalised vecs
        self._ids: list[str] = []     # parallel list of submission IDs
        self._class_ids: list[str] = []  # school/class IDs for filtering

    def _encode(self, text: str) -> np.ndarray:
        vec = self.encoder.encode([text], normalize_embeddings=True)
        return vec.astype("float32")

    def add(self, submission_id: str, class_id: str, text: str) -> None:
        if not self.enabled:
            return
        vec = self._encode(text)
        self.index.add(vec)
        self._ids.append(submission_id)
        self._class_ids.append(class_id)

    def search(
        self,
        text: str,
        class_id: str,
        top_k: int = 5,
        exclude_id: Optional[str] = None,
    ) -> list[tuple[str, float]]:
        """
        Returns list of (submission_id, similarity_score) for the same class,
        sorted by similarity descending.
        """
        if not self.enabled or self.index.ntotal == 0:
            return []

        vec = self._encode(text)
        k = min(top_k + 1, self.index.ntotal)
        scores, indices = self.index.search(vec, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            sid = self._ids[idx]
            cid = self._class_ids[idx]
            if cid != class_id:
                continue
            if sid == exclude_id:
                continue
            results.append((sid, float(score)))

        return sorted(results, key=lambda x: x[1], reverse=True)[:top_k]


# Singleton — initialised once on startup
faiss_store = FAISSStore()
