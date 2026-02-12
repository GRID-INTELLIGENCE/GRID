"""
Wellness Studio - Health & Wellness Transformation System

A HuggingFace-centric pipeline that transforms medical data into natural wellness plans.

Pipeline:
    Input → Scribe → Embed → Medical Model → Report

Modules:
    - config: Configuration management
    - input_processor: PDF, text, audio processing
    - scribe: Llama 3.1 medical data structuring
    - embedder: Sentence transformer embeddings
    - medical_model: HuatuoGPT wellness plan generation
    - report_generator: User-friendly report creation
    - pipeline: Main orchestration
    - cli: Command-line interface
"""

__version__ = "1.0.0"
__author__ = "Wellness Studio"

# Lazy imports to avoid torch dependency for security-only usage
try:
    from .pipeline import WellnessPipeline, run_pipeline, PipelineResult
    from .scribe import MedicalScribe, StructuredCase
    from .embedder import MedicalEmbedder, EmbeddingRetriever
    from .medical_model import MedicalDocumentModel, WellnessPlan, NaturalAlternative
    from .report_generator import ReportGenerator
    from .input_processor import InputProcessor
    
    __all__ = [
        'WellnessPipeline',
        'run_pipeline',
        'PipelineResult',
        'MedicalScribe',
        'StructuredCase',
        'MedicalEmbedder',
        'EmbeddingRetriever',
        'MedicalDocumentModel',
        'WellnessPlan',
        'NaturalAlternative',
        'ReportGenerator',
        'InputProcessor',
    ]
except ImportError:
    # torch/transformers not available - security modules only
    __all__ = []
