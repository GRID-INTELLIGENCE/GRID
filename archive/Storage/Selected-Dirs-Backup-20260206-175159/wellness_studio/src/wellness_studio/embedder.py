"""
Wellness Studio - Embedding Module
Converts structured medical data into vector embeddings for retrieval and processing.
"""
import json
import numpy as np
from typing import List, Dict, Union, Optional
from dataclasses import asdict

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from .config import model_config, processing_config, path_config, runtime_config
from .scribe import StructuredCase


class MedicalEmbedder:
    """
    Medical data embedder using sentence-transformers.
    Creates vector representations of structured medical cases.
    """

    def __init__(self, device: Optional[str] = None):
        self.device = device or model_config.DEVICE
        self.model_name = model_config.EMBEDDING_MODEL
        self.model = None
        self.dimension = model_config.EMBEDDING_DIMENSION

    def load_model(self):
        """Lazy load the embedding model."""
        if self.model is not None:
            return

        offline_mode = runtime_config.LOCAL_ONLY or runtime_config.OFFLINE_MODELS
        mode_str = " (LOCAL_ONLY mode)" if offline_mode else ""
        print(f"Loading Embedding model: {self.model_name}{mode_str}")

        if SENTENCE_TRANSFORMERS_AVAILABLE:
            # In LOCAL_ONLY mode, require pre-cached models
            load_kwargs = {
                "device": self.device if self.device != 'auto' else None,
                "cache_folder": str(path_config.MODELS_DIR),
            }

            if offline_mode:
                # Force local files only - will fail if model not pre-cached
                load_kwargs["local_files_only"] = True
                print(f"  Using cached model from: {path_config.MODELS_DIR}")

            try:
                self.model = SentenceTransformer(self.model_name, **load_kwargs)
                self.dimension = self.model.get_sentence_embedding_dimension()
            except OSError as e:
                if offline_mode:
                    raise RuntimeError(
                        f"Model '{self.model_name}' not found in cache. "
                        f"In LOCAL_ONLY mode, models must be pre-downloaded to '{path_config.MODELS_DIR}'. "
                        f"Run with WELLNESS_LOCAL_ONLY=false once to download, then switch back."
                    ) from e
                raise
        else:
            raise RuntimeError("sentence-transformers not installed")

    def embed_case(self, case: StructuredCase) -> Dict[str, np.ndarray]:
        """
        Create embeddings for a structured medical case.

        Returns:
            Dictionary with embeddings for different aspects of the case
        """
        self.load_model()

        # Create text representations for each component
        texts_to_embed = []
        keys = []

        # Patient summary
        if case.patient_summary:
            texts_to_embed.append(case.patient_summary)
            keys.append('summary')

        # Medications
        if case.current_medications:
            med_text = "Medications: " + ", ".join([
                f"{m.get('name', '')} {m.get('dosage', '')} {m.get('frequency', '')}".strip()
                for m in case.current_medications
            ])
            texts_to_embed.append(med_text)
            keys.append('medications')

        # Conditions
        if case.conditions:
            cond_text = "Conditions: " + ", ".join(case.conditions)
            texts_to_embed.append(cond_text)
            keys.append('conditions')

        # Symptoms
        if case.symptoms:
            symp_text = "Symptoms: " + ", ".join(case.symptoms)
            texts_to_embed.append(symp_text)
            keys.append('symptoms')

        # Combined representation
        combined_text = self._case_to_text(case)
        texts_to_embed.append(combined_text)
        keys.append('combined')

        # Generate embeddings
        embeddings = self.model.encode(
            texts_to_embed,
            batch_size=processing_config.EMBEDDING_BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        return {key: emb for key, emb in zip(keys, embeddings)}

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single text string."""
        self.load_model()
        return self.model.encode(text, convert_to_numpy=True)

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Embed multiple texts in batch."""
        self.load_model()
        return self.model.encode(
            texts,
            batch_size=processing_config.EMBEDDING_BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True
        )

    def _case_to_text(self, case: StructuredCase) -> str:
        """Convert structured case to comprehensive text representation."""
        parts = []

        if case.patient_summary:
            parts.append(f"Summary: {case.patient_summary}")

        if case.current_medications:
            meds = ", ".join([m.get('name', '') for m in case.current_medications])
            parts.append(f"Medications: {meds}")

        if case.conditions:
            parts.append(f"Conditions: {', '.join(case.conditions)}")

        if case.symptoms:
            parts.append(f"Symptoms: {', '.join(case.symptoms)}")

        if case.goals:
            parts.append(f"Goals: {', '.join(case.goals)}")

        return " | ".join(parts)

    def to_jsonl(self, case: StructuredCase, embeddings: Dict[str, np.ndarray]) -> str:
        """
        Convert case and embeddings to JSONL format.

        Returns:
            JSONL string with structured data and embeddings
        """
        # Convert numpy arrays to lists for JSON serialization
        serializable_embeddings = {
            key: emb.tolist() if isinstance(emb, np.ndarray) else emb
            for key, emb in embeddings.items()
        }

        record = {
            'case_data': case.to_dict(),
            'embeddings': serializable_embeddings,
            'model_info': {
                'embedding_model': self.model_name,
                'dimension': self.dimension
            }
        }

        return json.dumps(record, indent=2)

    def save_embeddings(self, case: StructuredCase, output_path: str):
        """Save embeddings to JSONL file."""
        embeddings = self.embed_case(case)
        jsonl_content = self.to_jsonl(case, embeddings)

        with open(output_path, 'w') as f:
            f.write(jsonl_content)

        return output_path


class EmbeddingRetriever:
    """Simple vector retrieval for similar cases."""

    def __init__(self, embedder: MedicalEmbedder):
        self.embedder = embedder
        self.cases = []
        self.embeddings = []

    def add_case(self, case: StructuredCase):
        """Add a case to the retrieval index."""
        combined_emb = self.embedder.embed_case(case)['combined']
        self.cases.append(case)
        self.embeddings.append(combined_emb)

    def find_similar(self, query_case: StructuredCase, top_k: int = 3) -> List[tuple]:
        """
        Find similar cases using cosine similarity.

        Returns:
            List of (case, similarity_score) tuples
        """
        if not self.cases:
            return []

        query_emb = self.embedder.embed_case(query_case)['combined']

        # Calculate cosine similarities
        similarities = []
        for emb in self.embeddings:
            sim = self._cosine_similarity(query_emb, emb)
            similarities.append(sim)

        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        return [(self.cases[i], similarities[i]) for i in top_indices]

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
