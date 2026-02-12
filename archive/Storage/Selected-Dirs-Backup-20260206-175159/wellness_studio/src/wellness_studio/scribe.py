"""
Wellness Studio - Medical Scribe Module
Uses Llama 3.1 to structure unstructured medical data into standardized format.
"""
import json
import re
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from .config import model_config, processing_config, path_config, runtime_config


@dataclass
class StructuredCase:
    """Structured representation of a medical case."""
    patient_summary: str
    current_medications: List[Dict[str, str]]
    conditions: List[str]
    symptoms: List[str]
    treatment_history: List[str]
    goals: List[str]
    raw_text: str

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            'patient_summary': self.patient_summary,
            'current_medications': self.current_medications,
            'conditions': self.conditions,
            'symptoms': self.symptoms,
            'treatment_history': self.treatment_history,
            'goals': self.goals,
            'raw_text': self.raw_text[:500] + '...' if len(self.raw_text) > 500 else self.raw_text
        }, indent=2)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'patient_summary': self.patient_summary,
            'current_medications': self.current_medications,
            'conditions': self.conditions,
            'symptoms': self.symptoms,
            'treatment_history': self.treatment_history,
            'goals': self.goals,
            'raw_text': self.raw_text
        }


class MedicalScribe:
    """
    Medical Scribe powered by Llama 3.1.
    Transforms unstructured medical data into structured, embeddable format.
    """

    def __init__(self, device: Optional[str] = None):
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("transformers library not installed")

        self.device = device or model_config.DEVICE
        self.model_name = model_config.SCRIBE_MODEL
        self.tokenizer = None
        self.model = None
        self.pipeline = None

    def load_model(self):
        """Lazy load the model."""
        if self.pipeline is not None:
            return

        offline_mode = runtime_config.LOCAL_ONLY or runtime_config.OFFLINE_MODELS
        mode_str = " (LOCAL_ONLY mode)" if offline_mode else ""
        print(f"Loading Scribe model: {self.model_name}{mode_str}")

        tokenizer_kwargs = {
            "trust_remote_code": True,
            "cache_dir": str(path_config.MODELS_DIR),
        }

        if offline_mode:
            tokenizer_kwargs["local_files_only"] = True
            print(f"  Using cached model from: {path_config.MODELS_DIR}")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                **tokenizer_kwargs
            )
        except OSError as e:
            if offline_mode:
                raise RuntimeError(
                    f"Model '{self.model_name}' not found in cache. "
                    f"In LOCAL_ONLY mode, models must be pre-downloaded to '{path_config.MODELS_DIR}'. "
                    f"Run with WELLNESS_LOCAL_ONLY=false once to download, then switch back."
                ) from e
            raise

        # Set padding token if not present
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        load_kwargs = {
            'cache_dir': str(path_config.MODELS_DIR),
            'trust_remote_code': True,
            'device_map': self.device if self.device != 'auto' else 'auto'
        }

        # Add quantization if configured
        if model_config.LOAD_IN_8BIT:
            load_kwargs['load_in_8bit'] = True
        elif model_config.LOAD_IN_4BIT:
            load_kwargs['load_in_4bit'] = True

        # Add offline mode
        if offline_mode:
            load_kwargs['local_files_only'] = True

        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **load_kwargs
            )
        except OSError as e:
            if offline_mode:
                raise RuntimeError(
                    f"Model '{self.model_name}' not found in cache. "
                    f"In LOCAL_ONLY mode, models must be pre-downloaded to '{path_config.MODELS_DIR}'. "
                    f"Run with WELLNESS_LOCAL_ONLY=false once to download, then switch back."
                ) from e
            raise

        self.pipeline = pipeline(
            'text-generation',
            model=self.model,
            tokenizer=self.tokenizer,
            device_map='auto' if self.device == 'auto' else None
        )

    def scribe(self, raw_text: str, case_type: str = "general") -> StructuredCase:
        """
        Transform raw medical text into structured format.

        Args:
            raw_text: Unstructured medical text
            case_type: Type of case (general, prescription, symptom, report)

        Returns:
            StructuredCase object
        """
        self.load_model()

        if self.pipeline is None:
            raise RuntimeError("Failed to load scribe model pipeline")

        # Build the extraction prompt
        prompt = self._build_scribe_prompt(raw_text, case_type)

        # Generate structured output
        response = self.pipeline(
            prompt,
            max_new_tokens=model_config.SCRIBE_MAX_TOKENS,
            temperature=model_config.SCRIBE_TEMPERATURE,
            do_sample=True,
            return_full_text=False
        )[0]['generated_text']

        # Parse the structured output
        return self._parse_response(response, raw_text)

    def _build_scribe_prompt(self, raw_text: str, case_type: str) -> str:
        """Build the prompt for the scribe model."""
        prompt_template = f"""You are a precise medical scribe. Your task is to analyze the following {case_type} case and extract structured information.

Extract and organize the following fields:
1. Patient Summary: Brief narrative of the patient's situation
2. Current Medications: List of medications with name, dosage, and frequency if available
3. Conditions: List of diagnosed or suspected conditions
4. Symptoms: List of current symptoms
5. Treatment History: Previous treatments or interventions
6. Goals: Patient's stated or implied health goals

Input Text:
{raw_text[:3000]}

Provide your response in this exact JSON format:
{{
  "patient_summary": "brief summary here",
  "current_medications": [
    {{"name": "medication name", "dosage": "dosage", "frequency": "frequency"}}
  ],
  "conditions": ["condition1", "condition2"],
  "symptoms": ["symptom1", "symptom2"],
  "treatment_history": ["treatment1", "treatment2"],
  "goals": ["goal1", "goal2"]
}}

Response:"""
        return prompt_template

    def _parse_response(self, response: str, raw_text: str) -> StructuredCase:
        """Parse the LLM response into StructuredCase."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                # Fallback: try to parse entire response
                data = json.loads(response)

            return StructuredCase(
                patient_summary=data.get('patient_summary', ''),
                current_medications=data.get('current_medications', []),
                conditions=data.get('conditions', []),
                symptoms=data.get('symptoms', []),
                treatment_history=data.get('treatment_history', []),
                goals=data.get('goals', []),
                raw_text=raw_text
            )
        except json.JSONDecodeError:
            # If JSON parsing fails, create a basic structure
            return StructuredCase(
                patient_summary="Unable to parse structured data",
                current_medications=[],
                conditions=[],
                symptoms=[],
                treatment_history=[],
                goals=[],
                raw_text=raw_text
            )

    def scribe_batch(self, texts: List[str], case_type: str = "general") -> List[StructuredCase]:
        """Process multiple texts in batch."""
        return [self.scribe(text, case_type) for text in texts]
