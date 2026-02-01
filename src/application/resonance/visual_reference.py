from dataclasses import dataclass


@dataclass
class ADSRParams:
    attack_time: float = 0.1
    decay_time: float = 0.2
    sustain_level: float = 0.7
    release_time: float = 0.3


class LFOParams:
    frequency: float = 1.0
    depth: float = 0.5
    waveform: str = "sine"


class VisualReference:
    def __init__(self, adsr_params: ADSRParams, lfo_params: LFOParams | None = None):
        self.adsr_params = adsr_params
        self.lfo_params = lfo_params

    def render_adsr_shape(self) -> str:
        # Logic to render ADSR shape as SVG or other format
        return "<svg>...</svg>"

    def render_line_graph(self, data: list[float]) -> str:
        # Logic to render line graph
        return "<svg>...</svg>"
