"""
Wellness Studio - Medical Document Model
Uses medical-trained LLM (HuatuoGPT or similar) to analyze cases and suggest natural alternatives.
"""
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from .config import model_config, path_config, runtime_config
from .scribe import StructuredCase


@dataclass
class NaturalAlternative:
    """Represents a natural alternative to a conventional treatment."""
    original: str
    alternative: str
    category: str  # e.g., 'herbal', 'mindfulness', 'nutrition', 'lifestyle'
    evidence_level: str  # 'high', 'moderate', 'preliminary'
    description: str
    benefits: List[str]
    considerations: List[str]


@dataclass
class WellnessPlan:
    """Complete wellness transformation plan."""
    case_summary: str
    natural_alternatives: List[NaturalAlternative]
    mindfulness_practices: List[str]
    nutritional_suggestions: List[str]
    lifestyle_modifications: List[str]
    combined_approach: str
    disclaimer: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'case_summary': self.case_summary,
            'natural_alternatives': [
                {
                    'original': alt.original,
                    'alternative': alt.alternative,
                    'category': alt.category,
                    'evidence_level': alt.evidence_level,
                    'description': alt.description,
                    'benefits': alt.benefits,
                    'considerations': alt.considerations
                }
                for alt in self.natural_alternatives
            ],
            'mindfulness_practices': self.mindfulness_practices,
            'nutritional_suggestions': self.nutritional_suggestions,
            'lifestyle_modifications': self.lifestyle_modifications,
            'combined_approach': self.combined_approach,
            'disclaimer': self.disclaimer
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class MedicalDocumentModel:
    """
    Medical Document Model using a medical-trained LLM.
    Analyzes structured cases and generates natural wellness alternatives.
    """

    # Knowledge base of common natural alternatives
    NATURAL_ALTERNATIVES_KB = {
        'pain relief': {
            'alternatives': ['Turmeric/Curcumin', 'Ginger', 'Willow Bark', 'Mindfulness Meditation', 'Acupuncture'],
            'category': 'herbal/mindfulness'
        },
        'anxiety': {
            'alternatives': ['Ashwagandha', 'Lavender', 'Chamomile', 'Meditation', 'Breathing Exercises'],
            'category': 'herbal/mindfulness'
        },
        'sleep issues': {
            'alternatives': ['Valerian Root', 'Melatonin (natural)', 'Sleep Hygiene', 'Yoga Nidra', 'Magnesium'],
            'category': 'herbal/lifestyle'
        },
        'inflammation': {
            'alternatives': ['Omega-3 Fatty Acids', 'Green Tea', 'Boswellia', 'Anti-inflammatory Diet', 'Turmeric'],
            'category': 'nutrition/herbal'
        },
        'high blood pressure': {
            'alternatives': ['Hibiscus Tea', 'Garlic', 'CoQ10', 'Meditation', 'DASH Diet', 'Exercise'],
            'category': 'nutrition/herbal/lifestyle'
        },
        'digestive issues': {
            'alternatives': ['Probiotics', 'Peppermint', 'Ginger', 'Fermented Foods', 'Mindful Eating'],
            'category': 'nutrition/herbal'
        },
        'depression': {
            'alternatives': ['St. Johns Wort', 'SAM-e', 'Exercise', 'Light Therapy', 'Mindfulness'],
            'category': 'herbal/lifestyle'
        },
        'cholesterol': {
            'alternatives': ['Red Yeast Rice', 'Plant Sterols', 'Oats', 'Mediterranean Diet', 'Exercise'],
            'category': 'nutrition/herbal'
        }
    }

    def __init__(self, device: Optional[str] = None):
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("transformers library not installed")

        self.device = device or model_config.DEVICE
        self.model_name = model_config.MEDICAL_MODEL
        self.tokenizer = None
        self.model = None
        self.pipeline = None

    def load_model(self):
        """Lazy load the medical model."""
        if self.pipeline is not None:
            return

        offline_mode = runtime_config.LOCAL_ONLY or runtime_config.OFFLINE_MODELS
        mode_str = " (LOCAL_ONLY mode)" if offline_mode else ""
        print(f"Loading Medical Document Model: {self.model_name}{mode_str}")

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

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        load_kwargs = {
            'cache_dir': str(path_config.MODELS_DIR),
            'trust_remote_code': True,
            'device_map': self.device if self.device != 'auto' else 'auto'
        }

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

    def generate_wellness_plan(self, case: StructuredCase) -> WellnessPlan:
        """
        Generate a comprehensive wellness plan from a structured case.

        Args:
            case: Structured medical case from the scribe

        Returns:
            WellnessPlan with natural alternatives and recommendations
        """
        self.load_model()

        if self.pipeline is None:
            raise RuntimeError("Failed to load medical model pipeline")

        # Build comprehensive prompt
        prompt = self._build_wellness_prompt(case)

        # Generate response
        response = self.pipeline(
            prompt,
            max_new_tokens=model_config.MEDICAL_MAX_TOKENS,
            temperature=model_config.MEDICAL_TEMPERATURE,
            do_sample=True,
            return_full_text=False
        )[0]['generated_text']

        # Parse and structure the response
        return self._parse_wellness_response(response, case)

    def _build_wellness_prompt(self, case: StructuredCase) -> str:
        """Build the prompt for generating wellness alternatives."""
        medications_text = "\n".join([
            f"- {m.get('name', '')} ({m.get('dosage', 'unknown dosage')}, {m.get('frequency', 'as needed')})"
            for m in case.current_medications
        ]) if case.current_medications else "None reported"

        prompt = f"""You are a holistic health and wellness consultant. Your role is to suggest evidence-informed natural alternatives and complementary approaches to conventional medical treatments. You are NOT a medical doctor and your suggestions should be considered educational, not prescriptive.

PATIENT CASE:

Summary: {case.patient_summary}

Current Medications:
{medications_text}

Conditions: {', '.join(case.conditions) if case.conditions else 'None specified'}

Symptoms: {', '.join(case.symptoms) if case.symptoms else 'None specified'}

Patient Goals: {', '.join(case.goals) if case.goals else 'General wellness improvement'}

Your Task:
1. For each medication or condition, suggest natural alternatives (herbal, nutritional, lifestyle, mindfulness-based)
2. Include evidence levels for each suggestion
3. Recommend mindfulness practices suitable for this case
4. Suggest nutritional approaches
5. Propose lifestyle modifications
6. Explain how conventional and natural approaches can work together

IMPORTANT DISCLAIMERS TO INCLUDE:
- These are complementary suggestions, not replacements for medical treatment
- Patient should consult healthcare provider before making changes
- Natural doesn't always mean safe or without interactions

Format your response as:
ALTERNATIVES:
[medication/condition] -> [natural alternative]: [description with evidence level]

MINDFULNESS:
[List practices]

NUTRITION:
[List suggestions]

LIFESTYLE:
[List modifications]

COMBINED APPROACH:
[How to integrate conventional and natural approaches]

Response:"""
        return prompt

    def _parse_wellness_response(self, response: str, case: StructuredCase) -> WellnessPlan:
        """Parse the model response into structured WellnessPlan."""
        lines = response.split('\n')

        alternatives = []
        mindfulness = []
        nutrition = []
        lifestyle = []
        combined = []

        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if 'ALTERNATIVES:' in line.upper():
                current_section = 'alternatives'
                continue
            elif 'MINDFULNESS:' in line.upper():
                current_section = 'mindfulness'
                continue
            elif 'NUTRITION:' in line.upper():
                current_section = 'nutrition'
                continue
            elif 'LIFESTYLE:' in line.upper():
                current_section = 'lifestyle'
                continue
            elif 'COMBINED APPROACH:' in line.upper() or 'COMBINED:' in line.upper():
                current_section = 'combined'
                continue

            if current_section == 'alternatives' and '->' in line:
                alt = self._parse_alternative_line(line)
                if alt:
                    alternatives.append(alt)
            elif current_section == 'mindfulness' and line.startswith('-'):
                mindfulness.append(line.lstrip('- ').strip())
            elif current_section == 'nutrition' and line.startswith('-'):
                nutrition.append(line.lstrip('- ').strip())
            elif current_section == 'lifestyle' and line.startswith('-'):
                lifestyle.append(line.lstrip('- ').strip())
            elif current_section == 'combined':
                combined.append(line)

        # If no alternatives parsed, use knowledge base as fallback
        if not alternatives:
            alternatives = self._get_kb_alternatives(case)

        return WellnessPlan(
            case_summary=case.patient_summary,
            natural_alternatives=alternatives,
            mindfulness_practices=mindfulness or self._default_mindfulness(case),
            nutritional_suggestions=nutrition or self._default_nutrition(case),
            lifestyle_modifications=lifestyle or self._default_lifestyle(case),
            combined_approach=' '.join(combined) if combined else self._default_combined_approach(),
            disclaimer=self._generate_disclaimer()
        )

    def _parse_alternative_line(self, line: str) -> Optional[NaturalAlternative]:
        """Parse a single alternative line."""
        try:
            parts = line.split('->')
            if len(parts) != 2:
                return None

            original = parts[0].strip().rstrip(':')
            rest = parts[1].strip()

            # Extract alternative and description
            desc_parts = rest.split(':', 1)
            alternative = desc_parts[0].strip()
            description = desc_parts[1].strip() if len(desc_parts) > 1 else rest

            # Detect evidence level
            evidence = 'preliminary'
            if any(x in description.lower() for x in ['strong evidence', 'well-studied', 'clinical trials']):
                evidence = 'high'
            elif any(x in description.lower() for x in ['moderate evidence', 'some studies', 'promising']):
                evidence = 'moderate'

            # Detect category
            category = 'herbal'
            if any(x in alternative.lower() for x in ['meditation', 'yoga', 'mindfulness', 'breathing']):
                category = 'mindfulness'
            elif any(x in alternative.lower() for x in ['diet', 'food', 'nutrition', 'eat']):
                category = 'nutrition'
            elif any(x in alternative.lower() for x in ['exercise', 'sleep', 'activity', 'routine']):
                category = 'lifestyle'

            return NaturalAlternative(
                original=original,
                alternative=alternative,
                category=category,
                evidence_level=evidence,
                description=description,
                benefits=[],
                considerations=[]
            )
        except Exception:
            return None

    def _get_kb_alternatives(self, case: StructuredCase) -> List[NaturalAlternative]:
        """Get alternatives from knowledge base as fallback."""
        alternatives = []

        # Check conditions against KB
        for condition in case.conditions:
            condition_lower = condition.lower()
            for kb_condition, data in self.NATURAL_ALTERNATIVES_KB.items():
                if kb_condition in condition_lower or condition_lower in kb_condition:
                    for alt in data['alternatives']:
                        alternatives.append(NaturalAlternative(
                            original=condition,
                            alternative=alt,
                            category=data['category'],
                            evidence_level='moderate',
                            description=f"Traditional knowledge base suggestion for {condition}",
                            benefits=[],
                            considerations=[]
                        ))

        # Check medications against KB
        for med in case.current_medications:
            med_name = med.get('name', '').lower()
            # Add medication-specific logic here

        return alternatives

    def _default_mindfulness(self, case: StructuredCase) -> List[str]:
        """Default mindfulness practices."""
        return [
            "Daily 10-minute breathing meditation",
            "Body scan practice for stress awareness",
            "Mindful walking in nature",
            "Gratitude journaling"
        ]

    def _default_nutrition(self, case: StructuredCase) -> List[str]:
        """Default nutritional suggestions."""
        return [
            "Emphasize whole foods and colorful vegetables",
            "Include anti-inflammatory foods (fatty fish, nuts, berries)",
            "Stay hydrated with water and herbal teas",
            "Consider fermented foods for gut health"
        ]

    def _default_lifestyle(self, case: StructuredCase) -> List[str]:
        """Default lifestyle modifications."""
        return [
            "Establish consistent sleep schedule",
            "Regular gentle movement or walking",
            "Digital sunset 1 hour before bed",
            "Connect with nature daily"
        ]

    def _default_combined_approach(self) -> str:
        """Default combined approach text."""
        return """Natural wellness approaches work best as complements to conventional medical care.
        Start with one change at a time, track your response, and maintain open communication with your healthcare team.
        Natural approaches often take time to show benefits and may interact with medications, so professional guidance is essential."""

    def _generate_disclaimer(self) -> str:
        """Generate medical disclaimer."""
        return """IMPORTANT: This wellness plan is for educational purposes only.
        It is not medical advice, diagnosis, or treatment.
        Always consult qualified healthcare professionals before making changes to your health regimen,
        especially if you have existing medical conditions or take prescription medications.
        Natural products can interact with medications and may not be appropriate for everyone."""
