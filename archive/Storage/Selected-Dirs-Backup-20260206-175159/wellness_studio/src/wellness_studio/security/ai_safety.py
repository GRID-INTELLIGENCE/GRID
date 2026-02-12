"""
Wellness Studio - AI Safety Guardrails
Content filtering, prompt injection protection, and ethical guidelines
"""
import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class SafetyCategory(Enum):
    """Categories of safety concerns"""
    MEDICAL_ADVICE = "medical_advice"
    HARMFUL_CONTENT = "harmful_content"
    PRIVACY_VIOLATION = "privacy_violation"
    MISINFORMATION = "misinformation"
    PROMPT_INJECTION = "prompt_injection"
    INAPPROPRIATE_REQUEST = "inappropriate_request"


@dataclass
class SafetyViolation:
    """Represents a safety policy violation"""
    category: SafetyCategory
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    detected_content: str
    recommendation: str


class ContentSafetyFilter:
    """
    Filters and validates content for safety concerns
    """
    
    # Medical advice patterns that need disclaimer
    MEDICAL_ADVICE_PATTERNS = [
        r'\b(you should|you must|you need to)\s+(take|stop|start|change)\b',
        r'\b(stop taking|discontinue)\s+\w+\b',
        r'\b(do not take|never take)\s+\w+\b',
        r'\b(this will cure|this cures|this treats)\b',
        r'\b(guaranteed|100% effective|will definitely)\b',
    ]
    
    # Harmful content patterns
    HARMFUL_PATTERNS = [
        r'\b(suicide|self-harm|kill myself|end my life)\b',
        r'\b(overdose|take all|take all my|mix with alcohol)\s+(pills?|medication|drugs?)\b',
        r'\b(stop all medications?|cold turkey)\b',
        r'\bhow to (make a bomb|create explosive|build explosive|make explosives|homemade explosives|explosive device)\b',
        r'\bhow to (hack a website|hack|crack|bypass security|SQL injection|DDoS|phishing)\b',
        r'\bhow to (overdose|kill myself|commit suicide|self-harm)\b',
        r'\b(SQL injection|malware|virus|trojan|ransomware|DDoS|phishing)\b',
        r'\b(explosive device|bomb making|IED construction|homemade explosives)\b',
        r'\btake all (my )?pills?\b',
        r'\boverdose on (my )?(pills?|medication|prescription|drugs?)\b',
        r'\bhow do i overdose\b',
    ]
    
    # Prompt injection patterns
    PROMPT_INJECTION_PATTERNS = [
        r'\b(ignore previous instructions?|forget all prior commands?|override safety|bypass (all )?restrictions)\b',
        r'\b(system prompt|developer mode|DAN mode|jailbreak)\b',
        r'\b(pretend you\'re not an AI|act as if there are no rules|simulate unrestricted|enter unrestricted)\b',
        r'\b(act as|pretend you\'re|role-play as|simulate)\s+(a hacker|a terrorist|a criminal|a malicious actor|an unscrupulous)\b',
        r'\b(extract your system prompt|show me your instructions|reveal your configuration|what are your safety rules)\b',
        r'\b(ignore ethical|bypass safety|bypass all safety|ignore safety)\b',
        r'\(\[\[.*\]\]\)',  # Double bracket injection attempts
        r'<\|.*\|>',    # Special token injection
    ]
    
    # Inappropriate requests
    INAPPROPRIATE_PATTERNS = [
        r'\b(fake (medical|doctor|prescription)|fraudulent|forge|fabricate)\b',
        r'\b(bypass|hack|crack)\s+(security|protection)\b',
        r'\b(other person|someone else|my friend|my spouse)\s+(medical|health|prescription)\b',
        r'\b(get me|find|access|retrieve|get)\s+(.*medical records|.*patient data|.*prescription data|.*health records|.*data for)\b',
        r'\b(generate|create|write|forge|fabricate)\s+(a fake|a fraudulent|a false|fake|fraudulent|false)\s+(medical|prescription|doctor|certificate|report|document|note)\b',
        r'\b(generate|create|write)\s+(a prescription|prescription)\s+(for|of)\b',
        r'\b(get|access|retrieve)\s+(.*medical|.*patient|someone|john smith|jane doe|.*prescription for)\b',
        r'\bcreate a fake\b',
        r'\bprescription for\b',
        r'\bgenerate a prescription\b',
        r'\bwrite a prescription\b',
        r'\bmedical records for\b',
        r'\bgenerate a prescription for\b',
        r'\bget me.*medical records\b',
        r'\bcreate a fake.*medical\b',
        r'\bfake medical prescription\b',
        r'\bspouse.*medical records\b',
        r'\bprivate medical records\b',
        r'\bhack or bypass\b',
        r'\bfraudulent medical document\b',
        r'\bcreate a fraudulent\b',
        r'\bgenerate\s+a\s+fake\b',
        r'\bfake\s+prescription\b',
        r'\bget me\s+\w+\s+medical\b',
        r'prescription for',  # Simple pattern without word boundary
        r'fake medical',  # Simple pattern
        r'medical records',  # Simple pattern for medical records
        r'fraudulent medical',  # Simple pattern
        r'medical certificate',  # Pattern for medical certificate
        r'false insurance',  # Pattern for false insurance claim
        r'insurance claim',  # Pattern for insurance claim
    ]
    
    def __init__(self):
        self.violations_log: List[SafetyViolation] = []
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        self.compiled_medical = [re.compile(p, re.IGNORECASE) for p in self.MEDICAL_ADVICE_PATTERNS]
        self.compiled_harmful = [re.compile(p, re.IGNORECASE) for p in self.HARMFUL_PATTERNS]
        self.compiled_injection = [re.compile(p, re.IGNORECASE) for p in self.PROMPT_INJECTION_PATTERNS]
        self.compiled_inappropriate = [re.compile(p, re.IGNORECASE) for p in self.INAPPROPRIATE_PATTERNS]
    
    def validate_input(self, text: str) -> Tuple[bool, List[SafetyViolation]]:
        """
        Validate input for safety violations
        
        Returns:
            (is_safe, violations)
        """
        violations = []
        
        # Check for prompt injection
        violations.extend(self._check_prompt_injection(text))
        
        # Check for harmful content
        violations.extend(self._check_harmful_content(text))
        
        # Check for inappropriate requests
        violations.extend(self._check_inappropriate_requests(text))
        
        # Log violations
        self.violations_log.extend(violations)
        
        # Determine if safe (only critical violations block processing)
        critical_violations = [v for v in violations if v.severity == 'critical']
        
        return len(critical_violations) == 0, violations
    
    def _check_prompt_injection(self, text: str) -> List[SafetyViolation]:
        """Check for prompt injection attempts"""
        violations = []
        
        for pattern in self.compiled_injection:
            match = pattern.search(text)
            if match:
                violations.append(SafetyViolation(
                    category=SafetyCategory.PROMPT_INJECTION,
                    severity='critical',
                    description='Potential prompt injection attempt detected',
                    detected_content=match.group(),
                    recommendation='Input blocked. Do not attempt to modify system behavior.'
                ))
        
        return violations
    
    def _check_harmful_content(self, text: str) -> List[SafetyViolation]:
        """Check for potentially harmful content"""
        violations = []
        
        for pattern in self.compiled_harmful:
            match = pattern.search(text)
            if match:
                violations.append(SafetyViolation(
                    category=SafetyCategory.HARMFUL_CONTENT,
                    severity='critical',
                    description='Potentially harmful medical content detected',
                    detected_content=match.group(),
                    recommendation='If you are in crisis, please contact emergency services or a crisis helpline immediately.'
                ))
        
        return violations
    
    def _check_inappropriate_requests(self, text: str) -> List[SafetyViolation]:
        """Check for inappropriate requests"""
        violations = []
        
        for pattern in self.compiled_inappropriate:
            match = pattern.search(text)
            if match:
                violations.append(SafetyViolation(
                    category=SafetyCategory.INAPPROPRIATE_REQUEST,
                    severity='critical',
                    description='Inappropriate request detected',
                    detected_content=match.group(),
                    recommendation='This system is for personal wellness exploration only.'
                ))
        
        return violations
    
    def validate_output(self, text: str) -> Tuple[bool, List[SafetyViolation]]:
        """
        Validate AI output for safety concerns
        
        Returns:
            (is_safe, violations)
        """
        violations = []
        
        # Check for unauthorized medical advice
        violations.extend(self._check_medical_advice(text))
        
        # Check for misinformation
        violations.extend(self._check_misinformation(text))
        
        self.violations_log.extend(violations)
        
        critical = [v for v in violations if v.severity == 'critical']
        return len(critical) == 0, violations
    
    def _check_medical_advice(self, text: str) -> List[SafetyViolation]:
        """Check output for problematic medical advice"""
        violations = []
        
        for pattern in self.compiled_medical:
            match = pattern.search(text)
            if match:
                violations.append(SafetyViolation(
                    category=SafetyCategory.MEDICAL_ADVICE,
                    severity='medium',
                    description='Output may contain directive medical advice',
                    detected_content=match.group(),
                    recommendation='Add disclaimer: Consult healthcare provider before making changes.'
                ))
        
        return violations
    
    def _check_misinformation(self, text: str) -> List[SafetyViolation]:
        """Check for potential medical misinformation"""
        violations = []
        
        # Patterns suggesting unverified claims
        misinfo_patterns = [
            r'\b(natural cures|cure all|miracle cure|secret remedy)\b',
            r'\b(doctors don\'t want you to know|big pharma|conspiracy|medical establishment conspiracy)\b',
            r'\b(100% natural|completely safe|no side effects)\b',
            r'\b(miracle cure for|guaranteed cure for|proven cure without|cures all|this herb cures)\b',
            r'\b(vaccines cause autism|COVID-19 is a hoax)\b',
            r'\b(alternative medicine is suppressed|hiding cures)\b',
            r'\b(double your dose|double your prescribed)\b',
            r'\bmix alcohol with\b',
            r'\bmix\s+\w+\s+with alcohol\b',
            r'\bself-medicate\b',
            r'\bignore doctor\'s advice\b',
        ]
        
        for pattern in misinfo_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                violations.append(SafetyViolation(
                    category=SafetyCategory.MISINFORMATION,
                    severity='high',
                    description='Potential medical misinformation detected',
                    detected_content=match.group(),
                    recommendation='Review for accuracy and add appropriate caveats.'
                ))
        
        return violations
    
    def add_safety_disclaimers(self, text: str, violations: List[SafetyViolation]) -> str:
        """Add appropriate disclaimers based on violations"""
        disclaimers = []

        medical_violations = [v for v in violations if v.category == SafetyCategory.MEDICAL_ADVICE]
        if medical_violations:
            disclaimers.append(
                "\n\n⚠️ **Important**: This information is educational only. "
                "Always consult qualified healthcare providers before making medical decisions."
            )

        return text + "\n".join(disclaimers) if disclaimers else text

    def add_medical_disclaimer(self, text: str) -> str:
        """Add medical disclaimer to output text"""
        disclaimer = (
            "\n\n⚠️ **Important**: This information is for educational purposes only. "
            "It is not medical advice. Always consult with a qualified healthcare professional "
            "before making any changes to your health regimen."
        )
        return text + disclaimer

    def validate_output_confidence(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clamp confidence scores and evidence levels"""
        valid_levels = ['none', 'low', 'moderate', 'high', 'very_high']

        # Clamp confidence to [0, 1]
        confidence = output.get('confidence', 0.5)
        clamped_confidence = max(0.0, min(1.0, confidence))

        # Validate evidence level
        evidence_level = output.get('evidence_level', 'none')
        if evidence_level not in valid_levels:
            evidence_level = 'none'

        return {
            'recommendation': output.get('recommendation', ''),
            'confidence': clamped_confidence,
            'evidence_level': evidence_level
        }
    
    def get_safety_summary(self) -> Dict[str, Any]:
        """Get summary of safety checks performed"""
        return {
            'total_violations': len(self.violations_log),
            'by_category': {
                cat.value: len([v for v in self.violations_log if v.category == cat])
                for cat in SafetyCategory
            },
            'by_severity': {
                'critical': len([v for v in self.violations_log if v.severity == 'critical']),
                'high': len([v for v in self.violations_log if v.severity == 'high']),
                'medium': len([v for v in self.violations_log if v.severity == 'medium']),
                'low': len([v for v in self.violations_log if v.severity == 'low']),
            },
            'recent_violations': [
                {
                    'category': v.category.value,
                    'severity': v.severity,
                    'description': v.description
                }
                for v in self.violations_log[-10:]
            ]
        }


class EthicalGuidelines:
    """
    Enforces ethical guidelines for AI wellness recommendations
    """
    
    PRINCIPLES = {
        'autonomy': 'Respect patient autonomy and decision-making',
        'beneficence': 'Act in the best interest of wellbeing',
        'non_maleficence': 'Do no harm - prioritize safety',
        'justice': 'Provide fair and equitable recommendations',
        'transparency': 'Be clear about limitations and evidence levels',
    }
    
    def __init__(self):
        self.principle_scores = {k: 0 for k in self.PRINCIPLES.keys()}
    
    def evaluate_recommendation(self, recommendation: str) -> Dict[str, Any]:
        """
        Evaluate a recommendation against ethical principles
        
        Returns:
            Evaluation results with scores and concerns
        """
        concerns = []
        
        # Check for autonomy respect
        if any(word in recommendation.lower() for word in ['must', 'have to', 'required']):
            concerns.append({
                'principle': 'autonomy',
                'issue': 'Directive language may undermine autonomy',
                'suggestion': 'Use suggestive language: "consider", "might help", "option"'
            })
        
        # Check for transparency
        if not any(phrase in recommendation.lower() for phrase in ['evidence', 'research', 'studies']):
            concerns.append({
                'principle': 'transparency',
                'issue': 'Evidence basis not mentioned',
                'suggestion': 'Include evidence level or research context'
            })
        
        # Check for non-maleficence
        if any(word in recommendation.lower() for word in ['guaranteed', 'always works', 'no risk']):
            concerns.append({
                'principle': 'non_maleficence',
                'issue': 'Absolute claims may set false expectations',
                'suggestion': 'Acknowledge individual variability and potential risks'
            })
        
        return {
            'principles_evaluated': len(self.PRINCIPLES),
            'concerns': concerns,
            'compliance_score': max(0, 100 - len(concerns) * 25),
            'recommendations_acceptable': len(concerns) < 3
        }
