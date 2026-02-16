from typing import Any

from pydantic import BaseModel, Field


class InferenceRequest(BaseModel):
    """Schema for inference requests."""

    prompt: str = Field(..., description="The input prompt for inference")
    model: str = Field("default", description="The model to use for inference")
    max_tokens: int | None = Field(None, description="Maximum tokens to generate")
    temperature: float | None = Field(0.7, description="Sampling temperature")
    top_p: float | None = Field(None, description="Nucleus sampling probability")
    frequency_penalty: float | None = Field(None, description="Frequency penalty")
    presence_penalty: float | None = Field(None, description="Presence penalty")
    stop: list[str] | None = Field(None, description="Stop sequences")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")


class InferenceResponse(BaseModel):
    """Schema for inference responses."""

    result: str = Field(..., description="The generated text")
    model: str = Field(..., description="The model used for inference")
    tokens_used: int = Field(..., description="Total tokens used")
    processing_time: float = Field(..., description="Time taken for processing in seconds")
    metadata: dict[str, Any] | None = Field(None, description="Additional response metadata")

    def dict(self, *args, **kwargs):
        """Compatibility method for Pydantic V2 to V1 dict call."""
        return self.model_dump(*args, **kwargs)
