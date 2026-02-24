"""Shared fixtures for Mycelium test suite.

Test domains grounded in physics and mathematics:
  - Electromagnetic spectrum (signal transport: microwaves, radio waves, visible light)
  - Phase transitions (matter state transformations: solid/liquid/gas/plasma)
  - Polar thermodynamics (Arctic/Antarctic weather patterns, thermostate morphing)
  - Ecosystem energy flow (photosynthesis, trophic levels, nutrient cycles)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure src/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from mycelium.core import (
    CognitiveStyle,
    Depth,
    EngagementTone,
    ExpertiseLevel,
    Highlight,
    HighlightPriority,
    PersonaProfile,
    ResonanceLevel,
    Spore,
    SynthesisResult,
)
from mycelium.instrument import Instrument
from mycelium.navigator import PatternNavigator
from mycelium.persona import InteractionSignal, PersonaEngine
from mycelium.scaffolding import AdaptiveScaffold, ScaffoldDepth
from mycelium.sensory import SensoryMode, SensoryProfile
from mycelium.synthesizer import Synthesizer

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DOMAIN TEXTS — Real physics, grounded in measurable facts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ELECTROMAGNETIC_SPECTRUM_TEXT = (
    "The electromagnetic spectrum encompasses all frequencies of electromagnetic radiation. "
    "Radio waves have frequencies between 3 Hz and 300 GHz with wavelengths from 1 millimeter "
    "to 100 kilometers. Microwaves occupy the 300 MHz to 300 GHz range with wavelengths from "
    "1 millimeter to 1 meter. Infrared radiation spans 300 GHz to 400 THz. Visible light, "
    "the only portion detectable by human eyes, ranges from 400 to 700 nanometers in wavelength, "
    "corresponding to frequencies of 430 to 750 THz. Ultraviolet radiation extends from 750 THz "
    "to 30 PHz. X-rays occupy 30 PHz to 30 EHz. Gamma rays have frequencies above 30 EHz. "
    "All electromagnetic waves travel at the speed of light in vacuum, approximately 299,792,458 "
    "meters per second. The energy of a photon is directly proportional to its frequency, "
    "described by the equation E = hf, where h is Planck's constant (6.626 x 10^-34 J·s). "
    "Higher frequency radiation carries more energy per photon, which is why gamma rays are "
    "ionizing while radio waves are not. The relationship between wavelength and frequency "
    "is given by c = λf, where c is the speed of light and λ is the wavelength."
)

PHASE_TRANSITIONS_TEXT = (
    "Matter exists in four fundamental states: solid, liquid, gas, and plasma. Phase transitions "
    "occur when energy is added or removed from a substance. At 0 degrees Celsius and standard "
    "atmospheric pressure of 101.325 kPa, water transitions from solid ice to liquid water "
    "through melting, absorbing 334 joules per gram as latent heat of fusion. At 100 degrees "
    "Celsius, liquid water transitions to steam through vaporization, absorbing 2,260 joules "
    "per gram as latent heat of vaporization. During phase transitions, temperature remains "
    "constant despite continuous energy input, because the energy is used to break intermolecular "
    "bonds rather than increase kinetic energy. Sublimation occurs when a solid transforms "
    "directly to gas, bypassing the liquid phase, as seen with dry ice (solid CO2) at -78.5 "
    "degrees Celsius. Deposition is the reverse process. Plasma, the fourth state, forms when "
    "gas is heated to extreme temperatures (typically above 10,000 Kelvin), ionizing atoms by "
    "stripping electrons. The Sun's core operates at approximately 15 million Kelvin, where "
    "hydrogen exists as plasma undergoing nuclear fusion."
)

POLAR_THERMODYNAMICS_TEXT = (
    "The Arctic and Antarctic exhibit fundamentally different thermodynamic patterns. The Arctic "
    "is an ocean surrounded by land, while Antarctica is a continent surrounded by ocean. "
    "Antarctica holds the record for the lowest temperature ever recorded on Earth: -89.2 degrees "
    "Celsius at Vostok Station on July 21, 1983. The Arctic's minimum temperature is approximately "
    "-68 degrees Celsius, recorded in Verkhoyansk, Siberia. The Antarctic ice sheet contains "
    "approximately 26.5 million cubic kilometers of ice, representing about 61 percent of all "
    "fresh water on Earth. If fully melted, global sea levels would rise approximately 58 meters. "
    "The albedo effect plays a critical role: fresh snow reflects up to 90 percent of incoming "
    "solar radiation, while open ocean absorbs approximately 94 percent. This creates a positive "
    "feedback loop where ice loss reduces albedo, increasing absorption, accelerating warming, "
    "and causing further ice loss. The Antarctic Circumpolar Current, flowing at approximately "
    "130 million cubic meters per second, thermally isolates Antarctica from warmer ocean waters. "
    "Seasonal temperature variations at the South Pole range from -28 degrees Celsius in summer "
    "to -60 degrees Celsius in winter. The polar vortex, a persistent large-scale cyclone near "
    "both poles, significantly influences mid-latitude weather patterns when it weakens or shifts."
)

ECOSYSTEM_ENERGY_TEXT = (
    "Ecosystem energy flow follows the laws of thermodynamics. The first law states that energy "
    "cannot be created or destroyed, only transformed. Photosynthesis converts solar radiation "
    "into chemical energy with an efficiency of approximately 1 to 2 percent of total incident "
    "sunlight. Plants capture photons in the 400 to 700 nanometer range using chlorophyll. "
    "The net equation is 6CO2 + 6H2O + light energy → C6H12O6 + 6O2. At each trophic level, "
    "approximately 90 percent of energy is lost as heat through cellular respiration, following "
    "the second law of thermodynamics which states that entropy in an isolated system always "
    "increases. A typical food chain transfers only 10 percent of energy between trophic levels: "
    "producers capture 1000 kcal, primary consumers retain 100 kcal, secondary consumers retain "
    "10 kcal, and tertiary consumers retain 1 kcal. Decomposers recycle nutrients but not energy "
    "back into the ecosystem. The carbon cycle involves atmospheric CO2 at approximately 420 ppm, "
    "oceanic dissolved carbon of about 38,000 gigatons, and terrestrial biomass of about 2,000 "
    "gigatons. Mycorrhizal fungal networks facilitate nutrient transfer between plants, moving "
    "carbon, nitrogen, and phosphorus through underground hyphae spanning kilometers per cubic "
    "meter of soil."
)

# Short texts for edge-case testing
EMPTY_TEXT = ""
ONE_SENTENCE = "The speed of light is 299,792,458 meters per second."
TWO_SENTENCES = (
    "Water boils at 100 degrees Celsius at sea level. The latent heat of vaporization is 2,260 joules per gram."
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  KNOWN FACTS — Quantifiable ground truth for assertions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SPEED_OF_LIGHT_MPS = 299_792_458  # meters per second
PLANCK_CONSTANT_JS = 6.626e-34  # joule-seconds
WATER_MELTING_POINT_C = 0.0  # degrees Celsius
WATER_BOILING_POINT_C = 100.0  # degrees Celsius
LATENT_HEAT_FUSION_J_PER_G = 334  # joules per gram
LATENT_HEAT_VAPORIZATION_J_PER_G = 2260  # joules per gram
VOSTOK_RECORD_TEMP_C = -89.2  # degrees Celsius
ANTARCTIC_ICE_VOLUME_KM3 = 26_500_000  # cubic kilometers
SEA_LEVEL_RISE_IF_MELTED_M = 58  # meters
FRESH_SNOW_ALBEDO = 0.90  # fraction reflected
OCEAN_ABSORPTION = 0.94  # fraction absorbed
TROPHIC_TRANSFER_EFFICIENCY = 0.10  # 10% rule
PHOTOSYNTHESIS_EFFICIENCY_MAX = 0.02  # ~2%
ATMOSPHERIC_CO2_PPM = 420  # parts per million (approximate)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  EXPECTED KEYWORDS — What the synthesizer MUST find in each domain
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EM_EXPECTED_KEYWORDS = {"electromagnetic", "frequency", "wavelength", "radiation", "light", "energy"}
PHASE_EXPECTED_KEYWORDS = {"phase", "transitions", "temperature", "energy", "liquid", "solid"}
POLAR_EXPECTED_KEYWORDS = {"arctic", "antarctic", "temperature", "ice", "albedo"}
ECOSYSTEM_EXPECTED_KEYWORDS = {"energy", "trophic", "photosynthesis", "carbon"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  FIXTURES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@pytest.fixture
def instrument() -> Instrument:
    return Instrument()


@pytest.fixture
def child_instrument() -> Instrument:
    m = Instrument()
    m.set_user(expertise="child", tone="playful")
    return m


@pytest.fixture
def expert_instrument() -> Instrument:
    m = Instrument()
    m.set_user(expertise="expert", tone="direct", depth="cold_brew")
    return m


@pytest.fixture
def synthesizer() -> Synthesizer:
    return Synthesizer()


@pytest.fixture
def navigator() -> PatternNavigator:
    return PatternNavigator()


@pytest.fixture
def persona_engine() -> PersonaEngine:
    return PersonaEngine()


@pytest.fixture
def scaffold() -> AdaptiveScaffold:
    return AdaptiveScaffold()


@pytest.fixture
def sensory() -> SensoryMode:
    return SensoryMode()
