import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / "src"))

from mycelium import Instrument

def run_demo():
    print("\n" + "="*60)
    print(" MYCELIUM DEMONSTRATION")
    print("="*60 + "\n")

    m = Instrument()

    complex_text = """
    Quantum entanglement is a physical phenomenon that occurs when a group of particles 
    are generated, interact, or share spatial proximity in a way such that the quantum state 
    of each particle of the group cannot be described independently of the state of the others, 
    including when the particles are separated by a large distance. The topic of quantum 
    entanglement is at the heart of the disparity between classical and quantum physics: 
    entanglement is a primary feature of quantum mechanics lacking in classical mechanics.
    """

    print("1. Default Synthesis (Americano depth):")
    print("-" * 40)
    result = m.synthesize(complex_text)
    print(f"Gist:       {result.gist}")
    print(f"Highlights: {[h.text for h in result.highlights[:3]]}")
    print(f"Summary:    {result.summary}")
    print(f"Explanation:{result.explanation}\n")

    print("2. Concept Exploration ('cache'):")
    print("-" * 40)
    nav = m.explore("cache")
    if nav:
        print(f"Lens Pattern: {nav.lens.pattern.upper()}")
        print(f"ELI5:         {nav.lens.eli5}")
        print(f"Analogy:      {nav.lens.analogy}\n")

    print("3. Changing Persona to 'Child':")
    print("-" * 40)
    m.set_user(expertise="child", tone="playful")
    child_result = m.synthesize(complex_text)
    print(f"Child Gist: {child_result.gist}")
    print(f"Child Explanation: {child_result.explanation}\n")

    print("4. Applying Feedback ('Too Complex'):")
    print("-" * 40)
    m.feedback(too_complex=True)
    feedback_result = m.synthesize(complex_text)
    print(f"New Depth: {feedback_result.depth_used.upper()}")
    print(f"Adjusted Explanation: {feedback_result.explanation}\n")

    print("5. Sensory Profile 'Cognitive' (Simplifies Punctuation & Tone):")
    print("-" * 40)
    m.set_sensory("cognitive")
    cognitive_result = m.synthesize(complex_text)
    print(f"Sensory Gist: {cognitive_result.gist}")

    print("\n" + "="*60)

if __name__ == "__main__":
    run_demo()
