import json
from typing import TypeVar

import httpx
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class StructuredLLM:
    """Wrapper for gpt-oss-safeguard:20b to enforce structured outputs."""

    def __init__(self, model_name: str = "gpt-oss-safeguard:20b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    async def generate_structured(self, prompt: str, output_schema: type[T]) -> T:
        """
        Generates a response following the Pydantic schema.
        """
        schema_json = output_schema.model_json_schema()

        system_prompt = f"""You are a precise data extraction engine.
You MUST respond with valid JSON only.
No preamble, no markdown formatting (like ```json), no explanations.
Your output must strictly adhere to this JSON Schema:
{json.dumps(schema_json, indent=2)}
"""

        payload = {
            "model": self.model_name,
            "prompt": f"{system_prompt}\n\nUSER: {prompt}\n\nJSON:",
            "stream": False,
            "options": {"temperature": 0.1, "num_ctx": 4096},  # Low temp for structure
            "format": "json",  # Enforce JSON mode in Ollama if supported, or rely on prompt
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.base_url}/api/generate", json=payload, timeout=60.0)
                response.raise_for_status()
                result = response.model_dump_json()
                text = result.get("response", "").strip()

                # Clean up if markdown blocks leaked
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]

                data = json.loads(text)
                return output_schema.model_validate(data)
            except Exception as e:
                print(f"Error generating structured output: {e} | Raw text: {text}")
                raise


# Example Usage
if __name__ == "__main__":
    import asyncio

    class ProjectStatus(BaseModel):
        status: str
        health_score: int
        active_modules: list[str]

    async def test():
        llm = StructuredLLM()
        try:
            result = await llm.generate_structured(
                "Summarize the current GRID project status based on hypothetical data: It's all good, running at 90% capacity, with sales and core active.",
                ProjectStatus,
            )
            print("Structured Output:", result.model_dump_json(indent=2))
        except Exception as e:
            print(f"Test failed: {e}")

    asyncio.run(test())
