"""Sensory processor for extended cognitive senses."""

from typing import Any

from .sensory_input import SensoryInput, SensoryType


class SensoryProcessor:
    """Processes sensory inputs including extended cognitive senses."""

    def __init__(self):
        """Initialize sensory processor."""
        self._processors: dict[SensoryType, Any] = {
            SensoryType.VISUAL: self._process_visual,
            SensoryType.AUDIO: self._process_audio,
            SensoryType.TEXT: self._process_text,
            SensoryType.SMELL: self._process_smell,
            SensoryType.TOUCH: self._process_touch,
            SensoryType.TASTE: self._process_taste,
            SensoryType.TEMPERATURE: self._process_temperature,
            SensoryType.PRESSURE: self._process_pressure,
            SensoryType.VIBRATION: self._process_vibration,
            SensoryType.PROXIMITY: self._process_proximity,
        }

    def process(self, input_data: SensoryInput) -> dict[str, Any]:
        """Process a sensory input.

        Args:
            input_data: Sensory input to process

        Returns:
            Processed data
        """
        processor = self._processors.get(input_data.sensory_type)
        if not processor:
            return {"raw": input_data.data, "type": input_data.sensory_type.value}

        return processor(input_data)

    def _process_visual(self, input_data: SensoryInput) -> dict[str, Any]:
        """Process visual input."""
        return {
            "type": "visual",
            "data": input_data.data,
            "intensity": input_data.intensity,
            "location": input_data.location,
        }

    def _process_audio(self, input_data: SensoryInput) -> dict[str, Any]:
        """Process audio input."""
        return {
            "type": "audio",
            "data": input_data.data,
            "intensity": input_data.intensity,
            "frequency": input_data.data.get("frequency", 0.0),
        }

    def _process_text(self, input_data: SensoryInput) -> dict[str, Any]:
        """Process text input."""
        return {
            "type": "text",
            "content": input_data.data.get("text", ""),
            "language": input_data.data.get("language", "en"),
        }

    def _process_smell(self, input_data: SensoryInput) -> dict[str, Any]:
        """Process smell input."""
        return {
            "type": "smell",
            "scent": input_data.data.get("scent", "unknown"),
            "intensity": input_data.intensity,
            "quality": input_data.quality,
            "notes": input_data.data.get("notes", ""),
        }

    def _process_touch(self, input_data: SensoryInput) -> dict[str, Any]:
        """Process touch input."""
        return {
            "type": "touch",
            "texture": input_data.data.get("texture", "unknown"),
            "temperature": input_data.data.get("temperature", 0.0),
            "pressure": input_data.data.get("pressure", 0.0),
            "intensity": input_data.intensity,
            "location": input_data.location,
        }

    def _process_taste(self, input_data: SensoryInput) -> dict[str, Any]:
        """Process taste input."""
        return {
            "type": "taste",
            "flavor": input_data.data.get("flavor", "unknown"),
            "intensity": input_data.intensity,
            "quality": input_data.quality,
            "notes": input_data.data.get("notes", ""),
        }

    def _process_temperature(self, input_data: SensoryInput) -> dict[str, Any]:
        """Process temperature input."""
        return {
            "type": "temperature",
            "value": input_data.data.get("value", 0.0),
            "unit": input_data.data.get("unit", "celsius"),
            "location": input_data.location,
        }

    def _process_pressure(self, input_data: SensoryInput) -> dict[str, Any]:
        """Process pressure input."""
        return {
            "type": "pressure",
            "value": input_data.data.get("value", 0.0),
            "unit": input_data.data.get("unit", "pascal"),
            "location": input_data.location,
        }

    def _process_vibration(self, input_data: SensoryInput) -> dict[str, Any]:
        """Process vibration input."""
        return {
            "type": "vibration",
            "frequency": input_data.data.get("frequency", 0.0),
            "amplitude": input_data.data.get("amplitude", 0.0),
            "location": input_data.location,
        }

    def _process_proximity(self, input_data: SensoryInput) -> dict[str, Any]:
        """Process proximity input."""
        return {
            "type": "proximity",
            "distance": input_data.data.get("distance", 0.0),
            "unit": input_data.data.get("unit", "meters"),
            "location": input_data.location,
        }

    def process_batch(self, inputs: list[SensoryInput]) -> list[dict[str, Any]]:
        """Process multiple sensory inputs.

        Args:
            inputs: List of sensory inputs

        Returns:
            List of processed data
        """
        return [self.process(input_data) for input_data in inputs]
