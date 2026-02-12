"""Sensory interfaces and processing."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class SensoryInput:
    """Container for sensory payloads."""

    source: str
    data: dict[str, Any]
    timestamp: float
    modality: str


class SensoryProcessor:
    """Processes incoming sensory data for the intelligence pipeline."""

    def _timed(self, fn, *args, **kwargs) -> tuple[Any, float]:
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        end = time.perf_counter()
        return result, (end - start) * 1000.0

    def _process_audio(self, data: dict[str, Any]) -> dict[str, Any]:
        samples = np.array(data.get("samples", []), dtype=float)
        if samples.size == 0:
            energy = 0.0
            spectrum = []
        else:
            spectrum = np.fft.fft(samples).real.tolist()
            energy = float(np.sum(np.square(samples)))
        return {
            "features": {"energy": energy, "spectrum_len": len(spectrum)},
            "coherence": float(data.get("clarity", 0.5)),
        }

    def _process_visual(self, data: dict[str, Any]) -> dict[str, Any]:
        pixels = np.array(data.get("pixels", []), dtype=float)
        if pixels.size == 0:
            hist = [0] * 8
            edges = 0
        else:
            hist, _ = np.histogram(pixels, bins=8, range=(0, 255))
            edges = int(np.sum(np.abs(np.diff(pixels))))
        return {
            "features": {"hist": hist.tolist() if hasattr(hist, "tolist") else list(hist), "edges": edges},
            "spatial_field": data.get("spatial_features", {}),
            "coherence": float(data.get("clarity", 0.5)),
        }

    def _process_text(self, data: dict[str, Any]) -> dict[str, Any]:
        text_val = data.get("text", "")
        tokens = [t for t in re.split(r"\W+", text_val) if t]
        return {
            "features": {"length": len(text_val), "tokens": len(tokens), "unique_tokens": len(set(tokens))},
            "semantic_field": data.get("tokens", {}),
            "coherence": float(data.get("confidence", 0.5)),
        }

    def _process_structured(self, data: dict[str, Any]) -> dict[str, Any]:
        values = [v for v in data.values() if isinstance(v, (int, float))]
        if values:
            stats = {
                "mean": float(np.mean(values)),
                "std": float(np.std(values)),
                "min": float(np.min(values)),
                "max": float(np.max(values)),
            }
        else:
            stats = {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
        return {
            "features": stats,
            "coherence": float(data.get("confidence", 0.8)),
        }

    async def process(self, sensory_input: SensoryInput) -> dict[str, Any]:
        """Modality-specific feature extraction with timing telemetry."""
        payload = sensory_input.data
        modality = sensory_input.modality

        if modality == "visual":
            body, duration_ms = self._timed(self._process_visual, payload)
        elif modality == "audio":
            body, duration_ms = self._timed(self._process_audio, payload)
        elif modality == "text":
            body, duration_ms = self._timed(self._process_text, payload)
        else:
            body, duration_ms = self._timed(self._process_structured, payload)

        # Preserve compatibility fields
        base = {
            "processed": True,
            "modality": modality,
            "valid": True,
            "raw_size": len(str(payload)),
            "duration_ms": duration_ms,
        }
        return {**base, **body}
