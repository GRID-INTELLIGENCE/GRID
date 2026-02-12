import json
from typing import Any

import httpx


class FunctionLLM:
    """Wrapper for functiongemma to handle tool calling."""

    def __init__(self, model_name: str = "functiongemma:latest", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    def format_tools_for_prompt(self, tools: list[dict[str, Any]]) -> str:
        """Formats tools description for the model context."""
        return json.dumps(tools, indent=2)

    async def select_tool(self, query: str, tools: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Asks the model to select a tool/function based on the query.
        """
        tools_desc = self.format_tools_for_prompt(tools)

        prompt = f"""<start_of_turn>user
You are a helpful assistant with access to the following functions:
{tools_desc}

To use a function, respond with a JSON object containing "function" (name) and "parameters" (dict).
If no function is applicable, respond with a normal text message in "message".

Query: {query}<end_of_turn>
<start_of_turn>model
"""

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0, "stop": ["<end_of_turn>"]},
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.base_url}/api/generate", json=payload, timeout=30.0)
                response.raise_for_status()
                result = response.model_dump_json()
                text = result.get("response", "").strip()

                # Attempt to parse JSON from the response
                try:
                    # Sometimes models wrap in markdown
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0].strip()
                    elif "```" in text:
                        text = text.split("```")[1].split("```")[0].strip()

                    data = json.loads(text)
                    return data
                except json.JSONDecodeError:
                    return {"message": text}

            except Exception as e:
                print(f"Error selecting tool: {e}")
                return {"error": str(e)}


if __name__ == "__main__":
    import asyncio

    async def test():
        llm = FunctionLLM()
        tools = [
            {
                "name": "calculate_sum",
                "description": "Calculates the sum of two numbers",
                "parameters": {
                    "type": "object",
                    "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                    "required": ["a", "b"],
                },
            }
        ]

        print("Testing calculation query...")
        result = await llm.select_tool("What is 55 plus 10?", tools)
        print("Result:", result)

    asyncio.run(test())
