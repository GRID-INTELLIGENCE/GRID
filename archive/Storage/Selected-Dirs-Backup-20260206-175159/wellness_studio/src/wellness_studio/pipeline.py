"""
Wellness Studio - Main Pipeline
Orchestrates the complete workflow: Input → Scribe → Embed → Medical Model → Report
"""

from pathlib import Path
from typing import Optional, Union, Dict, List, Any
from dataclasses import dataclass
import time
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor

from .config import path_config, model_config
from .input_processor import InputProcessor
from .scribe import MedicalScribe, StructuredCase
from .embedder import MedicalEmbedder
from .medical_model import MedicalDocumentModel, WellnessPlan
from .report_generator import ReportGenerator
from .security.concurrency_manager import DynamicSafetyIOManager, DynamicSafetyGuard
from .security.audit_logger import AuditLogger
from .security.rate_limiter import RateLimiter
from .security.ai_safety import ContentSafetyFilter


@dataclass
class PipelineResult:
    """Complete result from running the wellness pipeline."""

    success: bool
    structured_case: Optional[StructuredCase]
    wellness_plan: Optional[WellnessPlan]
    report_path: Optional[Path]
    embeddings_path: Optional[Path]
    processing_time: float
    error_message: Optional[str] = None


class WellnessPipeline:
    """
    Main pipeline orchestrating the wellness transformation process.

    Pipeline Flow:
    1. Input Processing (PDF/Text/Audio → Raw Text)
    2. Medical Scribe (Raw Text → Structured Case)
    3. Embedding (Structured Case → Vector Embeddings)
    4. Medical Model (Structured Case → Wellness Plan)
    5. Report Generation (Wellness Plan → User Report)
    """

    def __init__(self, device: Optional[str] = None, skip_embeddings: bool = False):
        """
        Initialize the pipeline.

        Args:
            device: Compute device ('cpu', 'cuda', 'mps', 'auto')
            skip_embeddings: Skip embedding generation (for faster processing)
        """
        self.device = device or model_config.DEVICE
        self.skip_embeddings = skip_embeddings

        # Initialize components
        self.input_processor = InputProcessor()
        self.scribe: Optional[MedicalScribe] = None
        self.embedder: Optional[MedicalEmbedder] = None
        self.medical_model: Optional[MedicalDocumentModel] = None
        self.report_generator = ReportGenerator()

        # Security & Concurrency
        self.audit_logger = AuditLogger()
        self.rate_limiter = RateLimiter()
        self.safety_filter = ContentSafetyFilter()

        self.io_manager = DynamicSafetyIOManager(
            audit_logger=self.audit_logger,
            rate_limiter=self.rate_limiter,
            max_concurrency=getattr(model_config, "MAX_CONCURRENT_IO", 5),
        )
        self.safety_guard = DynamicSafetyGuard(
            io_manager=self.io_manager, safety_filter=self.safety_filter
        )
        self.safety_guard.start_monitoring()

        self._models_loaded = False

    def load_models(self, load_scribe: bool = True, load_medical: bool = True):
        """
        Load the ML models. Can be called explicitly or happens automatically.

        Args:
            load_scribe: Load the scribe model (Llama 3.1)
            load_medical: Load the medical model (HuatuoGPT)
        """
        if load_scribe:
            print("📚 Loading Medical Scribe (Llama 3.1)...")
            self.scribe = MedicalScribe(device=self.device)
            self.scribe.load_model()

        if not self.skip_embeddings:
            print("🔢 Loading Embedding Model...")
            self.embedder = MedicalEmbedder(device=self.device)
            self.embedder.load_model()

        if load_medical:
            print("🏥 Loading Medical Document Model...")
            self.medical_model = MedicalDocumentModel(device=self.device)
            self.medical_model.load_model()

        self._models_loaded = True
        print("✅ All models loaded successfully!")

    def process(
        self,
        input_path: Optional[Union[str, Path]] = None,
        text_input: Optional[str] = None,
        patient_name: Optional[str] = None,
        case_type: str = "general",
        output_format: str = "markdown",
        save_embeddings: bool = False,
    ) -> PipelineResult:
        """
        Process a case through the complete pipeline.

        Args:
            input_path: Path to PDF, text, or audio file
            text_input: Raw text input (alternative to file)
            patient_name: Optional patient identifier
            case_type: Type of case (general, prescription, symptom, report)
            output_format: Report format (markdown, html, json)
            save_embeddings: Save embeddings to file

        Returns:
            PipelineResult with all outputs and paths
        """
        start_time = time.time()

        try:
            # Step 1: Process Input
            print("\n📥 Step 1: Processing Input...")
            input_data = self.input_processor.process_input(
                input_path=input_path, text_input=text_input
            )
            print(f"   Source: {input_data['source_type']}")
            print(f"   Content length: {len(input_data['content'])} characters")

            # Load models if not already loaded
            if not self._models_loaded:
                self.load_models()

            # Step 2: Medical Scribe
            print("\n📝 Step 2: Medical Scribe structuring...")
            if self.scribe is None:
                raise RuntimeError("Scribe model not loaded")
            structured_case = self.scribe.scribe(
                raw_text=input_data["content"], case_type=case_type
            )
            print(f"   Conditions found: {len(structured_case.conditions)}")
            print(f"   Medications found: {len(structured_case.current_medications)}")
            print(f"   Symptoms found: {len(structured_case.symptoms)}")

            # Step 3: Generate Embeddings (optional)
            embeddings_path = None
            if not self.skip_embeddings and self.embedder:
                print("\n🔢 Step 3: Generating embeddings...")
                embeddings = self.embedder.embed_case(structured_case)
                print(f"   Generated {len(embeddings)} embedding vectors")

                if save_embeddings:
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    embeddings_path = (
                        path_config.REPORTS_DIR / f"embeddings_{timestamp}.jsonl"
                    )
                    self.embedder.save_embeddings(structured_case, str(embeddings_path))
                    print(f"   Saved to: {embeddings_path}")

            # Step 4: Medical Model Analysis
            print("\n🏥 Step 4: Generating wellness plan...")
            if self.medical_model is None:
                raise RuntimeError("Medical model not loaded")
            wellness_plan = self.medical_model.generate_wellness_plan(structured_case)
            print(
                f"   Alternatives suggested: {len(wellness_plan.natural_alternatives)}"
            )
            print(
                f"   Mindfulness practices: {len(wellness_plan.mindfulness_practices)}"
            )
            print(
                f"   Lifestyle modifications: {len(wellness_plan.lifestyle_modifications)}"
            )

            # Step 5: Generate Report
            print("\n📄 Step 5: Generating report...")
            report_path = self.report_generator.generate_report(
                wellness_plan=wellness_plan,
                patient_name=patient_name,
                format=output_format,
            )
            print(f"   Report saved to: {report_path}")

            processing_time = time.time() - start_time
            print(f"\n✨ Pipeline completed in {processing_time:.2f} seconds")

            return PipelineResult(
                success=True,
                structured_case=structured_case,
                wellness_plan=wellness_plan,
                report_path=report_path,
                embeddings_path=embeddings_path,
                processing_time=processing_time,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Pipeline failed: {str(e)}"
            print(f"\n❌ {error_msg}")

            return PipelineResult(
                success=False,
                structured_case=None,
                wellness_plan=None,
                report_path=None,
                embeddings_path=None,
                processing_time=processing_time,
                error_message=error_msg,
            )

    def quick_process(
        self, text: str, patient_name: Optional[str] = None
    ) -> PipelineResult:
        """
        Quick processing for raw text input with default settings.

        Args:
            text: Raw medical text
            patient_name: Optional patient name

        Returns:
            PipelineResult
        """
        return self.process(
            text_input=text,
            patient_name=patient_name,
            case_type="general",
            output_format="markdown",
        )

    def process_prescription(
        self, text_or_path: str, patient_name: Optional[str] = None
    ) -> PipelineResult:
        """
        Specialized processing for prescription/medication cases.

        Args:
            text_or_path: Raw text or path to file
            patient_name: Optional patient name

        Returns:
            PipelineResult
        """
        # Determine if it's a path or text
        if Path(text_or_path).exists():
            return self.process(
                input_path=text_or_path,
                patient_name=patient_name,
                case_type="prescription",
            )
        else:
            return self.process(
                text_input=text_or_path,
                patient_name=patient_name,
                case_type="prescription",
            )

    def process_batch(
        self, tasks: List[Dict[str, Any]], output_format: str = "markdown"
    ) -> List[PipelineResult]:
        """
        Process multiple cases concurrently using the safety-aware IO manager.
        Each task should be a dict with pipeline.process arguments.
        """
        results = []

        def task_wrapper(task_params):
            patient_id = task_params.get("patient_name", "anonymous")
            resource_id = hashlib.sha256(str(task_params).encode()).hexdigest()[:16]

            # Execute through the safety-aware manager
            return self.io_manager.execute_safe_io(
                io_func=self.process,
                resource_id=resource_id,
                user_id=patient_id,
                **task_params,
            )

        print(f"\n🚀 Starting batch processing of {len(tasks)} tasks...")

        with ThreadPoolExecutor(
            max_workers=self.io_manager.max_concurrency
        ) as executor:
            future_to_task = {
                executor.submit(task_wrapper, task): task for task in tasks
            }

            for future in future_to_task:
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"Batch task failed: {e}")

        return results


def run_pipeline(
    input_path: Optional[str] = None,
    text: Optional[str] = None,
    patient: Optional[str] = None,
    device: str = "auto",
    format: str = "markdown",
) -> PipelineResult:
    """
    Convenience function to run the pipeline with minimal setup.

    Example:
        result = run_pipeline(text="Patient has anxiety and takes lorazepam...")
        result = run_pipeline(input_path="prescription.pdf", patient="John Doe")

    Args:
        input_path: Path to input file
        text: Raw text input
        patient: Patient identifier
        device: Compute device
        format: Output format

    Returns:
        PipelineResult
    """
    pipeline = WellnessPipeline(device=device)
    return pipeline.process(
        input_path=input_path,
        text_input=text,
        patient_name=patient,
        output_format=format,
    )
