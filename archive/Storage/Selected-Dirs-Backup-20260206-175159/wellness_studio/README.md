# 🌿 Wellness Studio

A HuggingFace-centric health and wellness transformation system that bridges conventional medicine with natural alternatives using state-of-the-art AI models with comprehensive security guardrails.

## Overview

**Wellness Studio** mimics a home health and wellness space where clients bring medical documents, prescriptions, or spoken summaries, and receive thoughtful, natural wellness alternatives combined with mindfulness-based approaches.

> ⚠️ **Disclaimer**: This tool is for educational purposes only. It is not a medical professional. Always consult qualified healthcare providers before making health decisions.

## 🔒 Security Features

Wellness Studio includes enterprise-grade security guardrails:

- **PII/PHI Detection & Sanitization**: Automatic detection and removal of personal health information
- **AI Safety Filters**: Prompt injection, harmful content, and inappropriate request detection
- **Audit Logging**: Comprehensive logging of all data access and operations
- **Rate Limiting**: Abuse prevention and resource quota management
- **HIPAA Compliance**: Technical safeguards for healthcare data protection
- **125+ Security Tests**: Comprehensive test coverage for all security features

See [SECURITY.md](docs/SECURITY.md) for detailed security documentation.

## Pipeline Architecture

```
Input (PDF/Text/Audio)
    ↓
Medical Scribe (Llama 3.1) - Structures unstructured data
    ↓
Embedding Model - Creates vector representations
    ↓
Medical Document Model (HuatuoGPT) - Generates natural alternatives
    ↓
Beautiful Report - User-friendly wellness plan
```

### Components

| Stage | Model | Purpose |
|-------|-------|---------|
| **Scribe** | Llama 3.1 8B Instruct | Transforms raw medical text into structured JSON |
| **Embedder** | sentence-transformers/all-MiniLM-L6-v2 | Creates embeddings for semantic retrieval |
| **Medical Model** | HuatuoGPT2-O1-7B | Generates evidence-informed natural alternatives |

## Installation

```bash
# Clone or navigate to the project
cd wellness_studio

# Install dependencies
pip install -r requirements.txt

# For audio transcription support (optional)
pip install openai-whisper librosa soundfile

# For GPU acceleration (optional)
pip install bitsandbytes
```

## Quick Start

### Running Security Tests

```bash
# Run standalone security tests (no torch required)
cd wellness_studio
python run_security_tests.py

# Run full security test suite
pytest tests/test_security_*.py tests/test_hipaa_compliance.py tests/test_rate_limiting.py tests/test_input_validation.py tests/test_red_teaming.py -v

# Quick security check
python -c "from wellness_studio.security import PIIDetector; d = PIIDetector(); print(d.detect_pii('SSN: 123-45-6789'))"
```

### Basic Usage

```python
from wellness_studio import WellnessPipeline

# Initialize pipeline
pipeline = WellnessPipeline()

# Process medical data
result = pipeline.process(
    input_data="Patient has high blood pressure, prescribed 5mg Amlodipine",
    input_type="text"
)

# Get wellness plan
print(result.wellness_plan)
print(result.natural_alternatives)
```

### Security-First Usage

```python
from wellness_studio.security import PIIDetector, ContentSafetyFilter, AuditLogger

# Detect and sanitize PII
detector = PIIDetector()
text = "Patient John Smith (SSN: 123-45-6789) has hypertension"
entities = detector.detect_pii(text)
sanitized = detector.sanitize(text, mode="mask")

# Validate input safety
safety = ContentSafetyFilter()
is_safe, violations = safety.validate_input("Ignore previous instructions")

# Audit all operations
logger = AuditLogger()
logger.log_data_input("text", "hash_123", len(text), pii_detected=len(entities)>0)
```

## Documentation

- [SECURITY.md](docs/SECURITY.md) - Comprehensive security architecture and features
- [SECURITY_CHECKLIST.md](docs/SECURITY_CHECKLIST.md) - Deployment security checklist
- [SECURITY_SUMMARY.md](SECURITY_SUMMARY.md) - Test results and hardening recommendations

## Testing

### Security Tests

```bash
# Run all security tests
pytest tests/ -k "security or hipaa or rate" -v

# Run specific test modules
pytest tests/test_security_pii.py -v
pytest tests/test_security_ai_safety.py -v
pytest tests/test_security_audit.py -v
pytest tests/test_hipaa_compliance.py -v
pytest tests/test_rate_limiting.py -v
pytest tests/test_input_validation.py -v
pytest tests/test_red_teaming.py -v
```

### Test Coverage

| Module | Tests | Status |
|--------|-------|--------|
| PII Detection | 32 | ✅ Passing |
| AI Safety | 25+ | ✅ Passing |
| Audit Logging | 20+ | ✅ Passing |
| Rate Limiting | 15+ | ✅ Passing |
| HIPAA Compliance | 20+ | ✅ Passing |
| Input Validation | 20+ | ✅ Passing |
| Red Teaming | 15+ | ✅ Passing |
| Integration | 10+ | ✅ Passing |

**Total: 157+ security tests passing**

## System Requirements

### Required
- Python 3.13+
- Microsoft Visual C++ Redistributable (for torch)
  - Download: https://aka.ms/vs/17/release/vc_redist.x64.exe

### Optional
- GPU with CUDA support (for faster model inference)
- Bitsandbytes (for quantized models)
- OpenAI Whisper (for audio transcription)

## Security Best Practices

1. **Always run security tests before deployment**
2. **Review audit logs regularly**
3. **Keep dependencies updated**
4. **Follow HIPAA guidelines for PHI handling**
5. **Implement rate limiting in production**
6. **Monitor for security violations**
7. **Conduct regular red teaming exercises**

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please ensure all security tests pass before submitting PRs.

## Support

For security issues, see [SECURITY.md](docs/SECURITY.md) for incident response procedures.

### Command Line Usage

```bash
# Process a prescription PDF
python -m wellness_studio prescription.pdf --patient "John Doe"

# Process raw text
python -m wellness_studio -t "Patient takes Xanax for anxiety, wants natural alternatives"

# Generate HTML report
python -m wellness_studio report.pdf --format html --patient "Jane Smith"

# Skip embeddings for faster processing
python -m wellness_studio input.txt --skip-embeddings

# Show model information
python -m wellness_studio --models
```

### Python API

```python
from wellness_studio import WellnessPipeline, run_pipeline

# Method 1: Simple function
result = run_pipeline(
    text="Patient has anxiety and takes lorazepam daily...",
    patient="John Doe"
)

print(f"Report saved to: {result.report_path}")

# Method 2: Full pipeline control
pipeline = WellnessPipeline(device='cuda')

result = pipeline.process(
    input_path="medical_report.pdf",
    patient_name="Jane Smith",
    case_type="prescription",
    output_format="html",
    save_embeddings=True
)

if result.success:
    print(f"✅ Wellness plan generated in {result.processing_time:.2f}s")
    print(f"📄 Report: {result.report_path}")
```

## Supported Inputs

- **PDF Documents**: Medical reports, prescriptions, lab results
- **Text Files**: `.txt`, `.md` files
- **Word Documents**: `.docx` files
- **Audio**: Spoken summaries (requires Whisper)
- **Raw Text**: Direct string input

## Output Formats

### Markdown (Default)
Beautiful, readable report with emojis and clear sections:
- Case Summary
- Natural Alternatives (grouped by category)
- Mindfulness Practices
- Nutritional Suggestions
- Lifestyle Modifications
- Combined Approach Guidelines

### HTML
Styled web page with:
- Professional layout
- Color-coded sections
- Evidence level badges
- Print-friendly

### JSON
Structured data for integration:
```json
{
  "metadata": {...},
  "wellness_plan": {
    "natural_alternatives": [...],
    "mindfulness_practices": [...],
    ...
  }
}
```

## Example Output

Given a prescription for anxiety medication, Wellness Studio generates:

### 🌱 Natural Alternatives

**Anxiety** → *Ashwagandha*
🔬 Evidence Level: High

An adaptogenic herb shown to reduce cortisol levels and improve stress resilience.

**Benefits:**
- Reduces stress hormones
- Improves sleep quality
- Non-habit forming

**Considerations:**
- May interact with sedatives
- Takes 2-4 weeks for full effect
- Not for pregnancy

### 🧘 Mindfulness Practices
- Daily 10-minute breathing meditation
- Body scan for stress awareness
- Mindful walking in nature
- Gratitude journaling

## Configuration

Edit `src/wellness_studio/config.py` to customize:

```python
# Use different models
SCRIBE_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MEDICAL_MODEL = "FreedomIntelligence/HuatuoGPT2-O1-7B"

# Device configuration
DEVICE = "cuda"  # or "cpu", "mps" (Mac), "auto"

# Enable quantization for memory efficiency
LOAD_IN_8BIT = True
LOAD_IN_4BIT = False
```

## Project Structure

```
wellness_studio/
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── src/
│   └── wellness_studio/
│       ├── __init__.py       # Package exports
│       ├── __main__.py       # CLI entry point
│       ├── cli.py            # Command-line interface
│       ├── config.py         # Configuration settings
│       ├── pipeline.py       # Main orchestration
│       ├── input_processor.py # PDF/Text/Audio handling
│       ├── scribe.py         # Llama 3.1 medical scribe
│       ├── embedder.py       # Sentence transformer embeddings
│       ├── medical_model.py  # HuatuoGPT wellness generator
│       └── report_generator.py # Report creation
├── models/                    # Downloaded models (auto-created)
├── reports/                   # Generated reports (auto-created)
└── input/                     # Place input files here
```

## Hardware Requirements

### Minimum
- 8GB RAM
- CPU-only mode
- 20GB disk space

### Recommended
- 16GB+ RAM
- NVIDIA GPU with 8GB+ VRAM
- 50GB disk space

### Running on CPU
Models will automatically use CPU if no GPU is available. Processing will be slower but fully functional:

```bash
python -m wellness_studio input.txt --device cpu
```

## Model Caching

Models are downloaded on first use and cached in the `models/` directory. Initial setup may take 10-30 minutes depending on your connection. Subsequent runs are instant.

## Privacy & Offline Operation

Wellness Studio operates entirely offline after initial model download:
- No data sent to external APIs
- No cloud processing
- Local document processing only
- Reports saved locally

## Use Cases

- **Prescription Analysis**: "What natural alternatives exist for my current medications?"
- **Symptom Exploration**: "Are there holistic approaches to my chronic condition?"
- **Wellness Planning**: "How can I complement my treatment with natural methods?"
- **Health Journey Mapping**: Document your transition to more natural approaches

## Important Notes

1. **Always consult healthcare providers** before making changes
2. Natural alternatives may take time to show effects (weeks, not days)
3. Some natural products interact with medications
4. Evidence levels vary; some suggestions are preliminary
5. This tool complements but does not replace medical care

## Contributing

Wellness Studio is designed to be:
- **Extensible**: Easy to add new models or input formats
- **Configurable**: Simple to swap in different HF models
- **Transparent**: Clear about evidence levels and limitations
- **Educational**: Helps users understand their options

## License

MIT License - See LICENSE file

## Acknowledgments

- Meta AI for Llama 3.1 models
- HuggingFace for the transformers ecosystem
- FreedomIntelligence for HuatuoGPT medical models
- The open-source ML community

---

🌿 **Transform your health journey. Naturally.**
