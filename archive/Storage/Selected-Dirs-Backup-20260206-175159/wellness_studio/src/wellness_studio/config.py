"""
Wellness Studio - Configuration Module
Central configuration for models, paths, and settings.
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RuntimeConfig:
    """Runtime configuration for local-only vs networked operation."""
    # LOCAL_ONLY mode: When True, disables all network-dependent features
    # - Model loading requires pre-cached models (local_files_only=True)
    # - Network monitoring is disabled
    # - No external API calls or web fetches
    LOCAL_ONLY: bool = os.environ.get("WELLNESS_LOCAL_ONLY", "true").lower() == "true"

    # OFFLINE_MODELS: Force models to load from cache only (no HuggingFace Hub downloads)
    OFFLINE_MODELS: bool = os.environ.get("WELLNESS_OFFLINE_MODELS", "true").lower() == "true"

    # DISABLE_NETWORK_MONITORING: Explicitly disable network monitoring components
    DISABLE_NETWORK_MONITORING: bool = os.environ.get("WELLNESS_DISABLE_NETWORK_MONITORING", "true").lower() == "true"


@dataclass
class ModelConfig:
    """Configuration for HuggingFace models used in the pipeline."""
    # Scribe Model (Llama 3.1 for structuring medical text)
    SCRIBE_MODEL: str = "meta-llama/Llama-3.1-8B-Instruct"
    SCRIBE_MAX_TOKENS: int = 2048
    SCRIBE_TEMPERATURE: float = 0.3
    
    # Embedding Model (Best available sentence transformer)
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    
    # Medical Document Model (MedLlama or similar medical-trained model)
    MEDICAL_MODEL: str = "FreedomIntelligence/HuatuoGPT2-O1-7B"
    MEDICAL_MAX_TOKENS: int = 4096
    MEDICAL_TEMPERATURE: float = 0.5
    
    # Device configuration
    DEVICE: str = "auto"  # auto, cpu, cuda, mps
    
    # Quantization for offline/larger model efficiency
    LOAD_IN_8BIT: bool = False
    LOAD_IN_4BIT: bool = False


@dataclass
class PathConfig:
    """Directory and file path configurations."""
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    MODELS_DIR: Path = field(init=False)
    REPORTS_DIR: Path = field(init=False)
    INPUT_DIR: Path = field(init=False)
    
    def __post_init__(self):
        self.MODELS_DIR = self.BASE_DIR / "models"
        self.REPORTS_DIR = self.BASE_DIR / "reports"
        self.INPUT_DIR = self.BASE_DIR / "input"
        
        # Ensure directories exist
        for dir_path in [self.MODELS_DIR, self.REPORTS_DIR, self.INPUT_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)


@dataclass
class ProcessingConfig:
    """Configuration for text and document processing."""
    # Chunking settings for long documents
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 128
    
    # Embedding batch size
    EMBEDDING_BATCH_SIZE: int = 32
    
    # Audio processing
    WHISPER_MODEL: str = "base"
    SUPPORTED_AUDIO_FORMATS: tuple = ('.wav', '.mp3', '.m4a', '.flac', '.ogg')
    
    # Document formats
    SUPPORTED_DOC_FORMATS: tuple = ('.pdf', '.txt', '.docx', '.md')


# Global configuration instances
runtime_config = RuntimeConfig()
model_config = ModelConfig()
path_config = PathConfig()
processing_config = ProcessingConfig()


def is_local_only() -> bool:
    """Check if running in local-only mode."""
    return runtime_config.LOCAL_ONLY


def require_network(feature_name: str) -> None:
    """Raise error if network is required but local-only mode is enabled."""
    if runtime_config.LOCAL_ONLY:
        raise RuntimeError(
            f"Feature '{feature_name}' requires network access, but LOCAL_ONLY mode is enabled. "
            f"Set WELLNESS_LOCAL_ONLY=false to enable network features."
        )
