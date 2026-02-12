# Quick Start - Activity Resonance Tool

## What It Does

The Activity Resonance Tool provides **left-to-right communication**:

- **LEFT (application/)**: Fast, concise context when decision/attention metrics are tense
- **RIGHT (light_of_the_seven/)**: Path visualization showing 3-4 options with input/output scenarios
- **ADSR Envelope**: Haptic-like feedback (attack, decay, sustain, release) like a pluck in a string

## Quick Examples

### Basic Usage
```powershell
python -m application.resonance.cli "create a new service"
```

### Code Activity
```powershell
python -m application.resonance.cli "add authentication endpoint" --type code
```

### PowerShell Wrapper
```powershell
.\application\resonance\resonance.ps1 "implement feature" -Type code
```

### JSON Output
```powershell
python -m application.resonance.cli "configure database" --json
```

## Understanding the Output

### Left Side (Context)
- **Sparsity**: How much context is missing (80% = high sparsity)
- **Attention Tension**: Urgency level (8% = low)
- **Decision Pressure**: Choice complexity (30% = moderate)
- **Clarity**: Query clarity (100% = very clear)
- **Confidence**: System confidence (30% = low due to sparsity)
- **Flavor Density**: Context richness (🍒 Rich vs 🦴 Bland)
- **Stickiness**: Context coherence (🍯 Sticky vs 🧊 Slippery)

### Right Side (Paths)
- **4 Options**: Direct, Incremental, Pattern-Based, Comprehensive
- **Recommended**: Highlighted with ⭐
- **Metrics**: Complexity, time, confidence for each path
- **Scenarios**: Input/output for each path

### ADSR Envelope
- **Attack**: Initial response (0.1s)
- **Decay**: Settle to sustain (0.2s)
- **Sustain**: Maintained feedback (0.7 amplitude)
- **Release**: Fade out (0.3s)

## Use Cases

1. **Quick Context**: When you need fast context about a task
   ```powershell
   python -m application.resonance.cli "what is the service pattern?"
   ```

2. **Path Triage**: When you have multiple ways to achieve a goal
   ```powershell
   python -m application.resonance.cli "implement authentication" --type code
   ```

3. **Decision Support**: When decision pressure is high
   ```powershell
   python -m application.resonance.cli "choose between approaches" --type general
   ```

4. **Real-time Feedback**: Monitor activity with ADSR envelope
   - Watch the envelope phases in real-time
   - See amplitude and velocity metrics
   - Understand activity resonance

## Tips

- Use `--type code` for code-related queries
- Use `--type config` for configuration queries
- Use `--json` for programmatic consumption
- Use `--no-context` to see only paths
- Use `--no-paths` to see only context

## Integration

The tool integrates seamlessly with:
- PowerShell terminal
- Python scripts
- Event/activity tracking
- Cognitive layer (light_of_the_seven/)

See `README.md` for full documentation.

