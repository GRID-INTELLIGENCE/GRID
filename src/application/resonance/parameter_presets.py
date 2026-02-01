from dataclasses import dataclass, field

from .visual_reference import ADSRParams, LFOParams


@dataclass
class ParameterPreset:
    name: str
    adsr_params: ADSRParams
    lfo_params: LFOParams = field(default_factory=LFOParams)


class ParameterPresetSystem:
    def __init__(self) -> None:
        self.presets: dict[str, ParameterPreset] = {}
        self._initialize_default_presets()

    def _initialize_default_presets(self) -> None:
        self.presets["balanced"] = ParameterPreset(name="balanced", adsr_params=ADSRParams(0.1, 0.2, 0.7, 0.3))
        self.presets["aggressive"] = ParameterPreset(name="aggressive", adsr_params=ADSRParams(0.05, 0.1, 0.8, 0.15))
        self.presets["gentle"] = ParameterPreset(name="gentle", adsr_params=ADSRParams(0.5, 0.8, 0.5, 1.0))
        self.presets["arena_champion"] = ParameterPreset(
            name="arena_champion", adsr_params=ADSRParams(0.08, 0.15, 0.75, 0.2)
        )

    def get_preset(self, name: str) -> ParameterPreset | None:
        return self.presets.get(name)

    def add_preset(self, preset: ParameterPreset) -> None:
        self.presets[preset.name] = preset
