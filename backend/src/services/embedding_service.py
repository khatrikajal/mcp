"""
Embedding Service for Vector-based Memory

Generates embeddings using sentence-transformers for semantic search.
Supports local model (all-MiniLM-L6-v2) for free, offline operation.
"""
import logging
import numpy as np
from typing import List, Tuple, Optional, Union
import pickle

logger = logging.getLogger(__name__)

# Model singleton to avoid reloading
_model = None
_model_name = "all-MiniLM-L6-v2"

# Embedding dimension for the model
EMBEDDING_DIMENSION = 384


def get_embedding_model():
    """
    Get or create the embedding model singleton.
    Uses sentence-transformers all-MiniLM-L6-v2 model.
    """
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {_model_name}")
            _model = SentenceTransformer(_model_name)
            logger.info("Embedding model loaded successfully")
        except ImportError:
            logger.warning("sentence-transformers not installed. Embeddings will be disabled.")
            return None
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return None
    return _model


class EmbeddingService:
    """
    Service for generating and managing text embeddings.
    """

    def __init__(self):
        self.model = get_embedding_model()
        self.dimension = EMBEDDING_DIMENSION

    def is_available(self) -> bool:
        """Check if embedding service is available."""
        return self.model is not None

    def generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            numpy array of shape (384,) or None if failed
        """
        if not self.model:
            logger.warning("Embedding model not available")
            return None

        try:
            # Clean and truncate text if needed
            text = self._preprocess_text(text)
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    def generate_embeddings(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """
        Generate embeddings for multiple texts (batch operation).

        Args:
            texts: List of texts to embed

        Returns:
            List of numpy arrays or None values
        """
        if not self.model:
            return [None] * len(texts)

        try:
            # Preprocess all texts
            processed_texts = [self._preprocess_text(t) for t in texts]
            embeddings = self.model.encode(processed_texts, convert_to_numpy=True)
            return [e.astype(np.float32) for e in embeddings]
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [None] * len(texts)

    def _preprocess_text(self, text: str, max_length: int = 8192) -> str:
        """
        Preprocess text for embedding.

        Args:
            text: Raw text
            max_length: Maximum character length

        Returns:
            Cleaned and truncated text
        """
        # Basic cleaning
        text = text.strip()

        # Truncate if too long (model has token limits)
        if len(text) > max_length:
            text = text[:max_length]

        return text

    def cosine_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score between -1 and 1
        """
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def find_similar(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: List[np.ndarray],
        top_k: int = 5,
        threshold: float = 0.0
    ) -> List[Tuple[int, float]]:
        """
        Find most similar embeddings to query.

        Args:
            query_embedding: Query embedding
            candidate_embeddings: List of candidate embeddings
            top_k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of (index, similarity) tuples, sorted by similarity descending
        """
        if not candidate_embeddings:
            return []

        similarities = []
        for i, candidate in enumerate(candidate_embeddings):
            if candidate is not None:
                sim = self.cosine_similarity(query_embedding, candidate)
                if sim >= threshold:
                    similarities.append((i, sim))

        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_k]

    @staticmethod
    def serialize_embedding(embedding: np.ndarray) -> bytes:
        """
        Serialize embedding to bytes for database storage.

        Args:
            embedding: Numpy array embedding

        Returns:
            Pickled bytes
        """
        if embedding is None:
            return None
        return pickle.dumps(embedding.astype(np.float32))

    @staticmethod
    def deserialize_embedding(data: bytes) -> Optional[np.ndarray]:
        """
        Deserialize embedding from database bytes.

        Args:
            data: Pickled bytes

        Returns:
            Numpy array embedding
        """
        if data is None:
            return None
        try:
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Failed to deserialize embedding: {e}")
            return None

    def get_embedding_for_search(self, query: str) -> Optional[np.ndarray]:
        """
        Generate embedding optimized for search queries.
        May apply different preprocessing for queries.

        Args:
            query: Search query text

        Returns:
            Query embedding
        """
        # For now, same as regular embedding
        # Could be extended to apply query-specific preprocessing
        return self.generate_embedding(query)


# Singleton instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
