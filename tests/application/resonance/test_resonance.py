import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.application.resonance import (
    ADSRParams,
    ArenaIntegration,
    AttractionForce,
    GravitationalPoint,
    GravitationalSystem,
    MermaidDiagramGenerator,
    Parameterization,
    ParameterPresetSystem,
    VectorIndex,
    VisualReference,
)


def test_visual_reference_creation():
    adsr = ADSRParams()
    vr = VisualReference(adsr)
    assert vr.adsr_params.attack_time == 0.1

def test_mermaid_generator():
    gen = MermaidDiagramGenerator()
    chart = gen.generate_xychart("Test", ["a"], "y", [0.5])
    assert "xychart-beta" in chart

def test_arena_integration():
    arena = ArenaIntegration([], {"name": "g", "target_score": 1})
    assert arena.goal_tracker.goal["name"] == "g"

def test_parameter_preset_system():
    pps = ParameterPresetSystem()
    preset = pps.get_preset('balanced')
    assert preset.name == 'balanced'

def test_vector_index():
    vi = VectorIndex()
    vi.add_vector("test", [0.1, 0.2, 0.3])
    assert len(vi.get_vector("test")) == 3

def test_gravitational_system():
    gp = GravitationalPoint(position=np.array([0,0,0]))
    af = AttractionForce()
    gs = GravitationalSystem(gp, af)
    vec = np.array([1,1,1])
    new_vec = gs.apply_gravity(vec)
    assert not np.array_equal(vec, new_vec)

def test_parameterization():
    p = Parameterization()
    assert p.parameters == {}

# RAG test is more complex, skipping for initial test
