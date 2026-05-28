"""
LLM Integration for Generation
==============================

Handles question-answering and text generation using retrieved context.
Supports OpenAI and Mistral providers for conversational AI capabilities.
"""

import logging
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

from ..core.config import KnowledgeBaseConfig
from ..search.retriever import RankedResult

logger = logging.getLogger(__name__)


def _make_llm_client(config: KnowledgeBaseConfig) -> Any:
    """Return the LLM client for the configured provider."""
    provider = config.llm.provider
    if provider == "mistral":
        from mistralai import Mistral

        return Mistral(api_key=config.llm.api_key)
    from openai import OpenAI

    return OpenAI(api_key=config.llm.api_key)


@dataclass
class GenerationRequest:
    """Request for text generation."""

    query: str
    context: list[RankedResult]
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    streaming: bool = False


@dataclass
class GenerationResult:
    """Result of text generation."""

    answer: str
    sources: list[dict[str, Any]]
    confidence_score: float
    token_usage: dict[str, int]
    processing_time: float
    model: str


class PromptBuilder:
    """Builds prompts for LLM generation."""

    @staticmethod
    def build_qa_prompt(query: str, context: list[RankedResult], system_prompt: str | None = None) -> str:
        """Build question-answering prompt."""

        # Default system prompt
        if not system_prompt:
            system_prompt = """You are a helpful AI assistant with access to a knowledge base.
            Answer questions based on the provided context. If the context doesn't contain
            relevant information, say so clearly. Be concise but comprehensive."""

        # Build context from retrieved results
        context_text = PromptBuilder._format_context(context)

        prompt = f"""{system_prompt}

Context:
{context_text}

Question: {query}

Answer:"""

        return prompt

    @staticmethod
    def build_summary_prompt(text: str, max_length: int = 200) -> str:
        """Build summarization prompt."""
        return f"""Summarize the following text in {max_length} words or less:

{text}

Summary:"""

    @staticmethod
    def build_chat_prompt(messages: list[dict[str, str]], context: list[RankedResult]) -> str:
        """Build conversational prompt with context."""
        context_text = PromptBuilder._format_context(context)

        conversation = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            conversation += f"{role.title()}: {content}\n"

        prompt = f"""You are a helpful AI assistant with access to a knowledge base.

Knowledge Base Context:
{context_text}

Conversation:
{conversation}

Assistant:"""

        return prompt

    @staticmethod
    def _format_context(context: list[RankedResult]) -> str:
        """Format retrieved results into context text."""
        if not context:
            return "No relevant context found."

        formatted_parts = []
        for i, result in enumerate(context, 1):
            # Include document title if available
            title = result.document_title or f"Document {result.document_id}"
            source = f"[{title}]"

            # Add relevance score
            score_info = ".2f"

            # Format the chunk
            formatted_parts.append(f"{i}. {source} {score_info}\n{result.content}")

        return "\n\n".join(formatted_parts)


class LLMGenerator:
    """LLM integration for text generation."""

    def __init__(self, config: KnowledgeBaseConfig):
        self.config = config
        self.client = _make_llm_client(config)

        # Generation statistics
        self.generation_stats = {"total_generations": 0, "total_tokens_used": 0, "avg_response_time": 0.0, "errors": 0}

    def generate_answer(self, request: GenerationRequest) -> GenerationResult:
        """Generate answer for a question using retrieved context."""
        start_time = time.time()

        try:
            # Build prompt
            prompt = PromptBuilder.build_qa_prompt(request.query, request.context, request.system_prompt)

            # Set parameters
            temperature = request.temperature or self.config.llm.temperature
            max_tokens = request.max_tokens or self.config.llm.max_tokens

            messages = [{"role": "user", "content": prompt}]
            provider = self.config.llm.provider
            if provider == "mistral":
                response = self.client.chat.complete(
                    model=self.config.llm.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.config.llm.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

            answer = response.choices[0].message.content.strip()
            token_usage = {
                "prompt_tokens": getattr(getattr(response, "usage", None), "prompt_tokens", 0) or 0,
                "completion_tokens": getattr(getattr(response, "usage", None), "completion_tokens", 0) or 0,
                "total_tokens": getattr(getattr(response, "usage", None), "total_tokens", 0) or 0,
            }

            # Calculate confidence (simplified - based on response length and context)
            confidence = self._calculate_confidence(answer, request.context)

            # Format sources
            sources = self._format_sources(request.context)

            processing_time = time.time() - start_time

            # Update statistics
            self._update_stats(token_usage["total_tokens"], processing_time)

            logger.info(f"Generated answer in {processing_time:.2f}s using {token_usage['total_tokens']} tokens")

            return GenerationResult(
                answer=answer,
                sources=sources,
                confidence_score=confidence,
                token_usage=token_usage,
                processing_time=processing_time,
                model=self.config.llm.model,
            )

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            self.generation_stats["errors"] += 1

            # Return error result
            return GenerationResult(
                answer=f"I apologize, but I encountered an error while generating a response: {str(e)}",
                sources=[],
                confidence_score=0.0,
                token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                processing_time=time.time() - start_time,
                model=self.config.llm.model,
            )

    async def generate_answer_stream(self, request: GenerationRequest) -> AsyncGenerator[str]:
        """Generate answer with streaming."""
        if not self.config.llm.streaming:
            # Fall back to non-streaming
            result = self.generate_answer(request)
            yield result.answer
            return

        try:
            prompt = PromptBuilder.build_qa_prompt(request.query, request.context, request.system_prompt)
            messages = [{"role": "user", "content": prompt}]
            temperature = request.temperature or self.config.llm.temperature
            max_tokens = request.max_tokens or self.config.llm.max_tokens
            provider = self.config.llm.provider

            full_response = ""
            if provider == "mistral":
                stream = self.client.chat.stream(
                    model=self.config.llm.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                for chunk in stream:
                    content = chunk.data.choices[0].delta.content or ""
                    if content:
                        full_response += content
                        yield content
            else:
                with self.client.chat.completions.stream(
                    model=self.config.llm.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ) as stream:
                    for chunk in stream:
                        content = chunk.choices[0].delta.content or ""
                        if content:
                            full_response += content
                            yield content

            logger.info(f"Streamed response completed, length: {len(full_response)}")

        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            yield f"I apologize, but I encountered an error: {str(e)}"

    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """Summarize text using LLM."""
        try:
            prompt = PromptBuilder.build_summary_prompt(text, max_length)
            messages = [{"role": "user", "content": prompt}]
            provider = self.config.llm.provider

            if provider == "mistral":
                response = self.client.chat.complete(
                    model=self.config.llm.model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=max_length // 4,
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.config.llm.model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=max_length // 4,
                )

            summary = response.choices[0].message.content.strip()
            return summary

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return f"Error summarizing text: {str(e)}"

    def _calculate_confidence(self, answer: str, context: list[RankedResult]) -> float:
        """Calculate confidence score for the answer."""
        if not context:
            return 0.1  # Low confidence with no context

        # Simple confidence calculation based on:
        # - Answer length (longer answers tend to be more confident)
        # - Context relevance scores
        # - Number of sources used

        # Average context score
        avg_context_score = sum(result.score for result in context) / len(context)

        # Answer quality indicators
        answer_length = len(answer.split())
        has_specific_info = any(
            term in answer.lower() for term in ["according to", "the document", "source", "context"]
        )

        # Calculate confidence
        confidence = min(
            1.0,
            (
                avg_context_score * 0.4  # Context relevance
                + min(answer_length / 100, 1.0) * 0.3  # Answer length
                + (0.3 if has_specific_info else 0.0)  # Specific references
            ),
        )

        return round(confidence, 2)

    def _format_sources(self, context: list[RankedResult]) -> list[dict[str, Any]]:
        """Format context results as sources."""
        sources = []
        for result in context:
            source = {
                "title": result.document_title or "Untitled Document",
                "content": result.content[:200] + "..." if len(result.content) > 200 else result.content,
                "score": result.score,
                "document_id": result.document_id,
                "chunk_id": result.chunk_id,
                "source_type": result.source_type,
                "rank": result.rank,
            }
            sources.append(source)

        return sources

    def _update_stats(self, tokens_used: int, processing_time: float) -> None:
        """Update generation statistics."""
        self.generation_stats["total_generations"] += 1
        self.generation_stats["total_tokens_used"] += tokens_used

        # Update average response time
        prev_avg = self.generation_stats["avg_response_time"]
        count = self.generation_stats["total_generations"]
        self.generation_stats["avg_response_time"] = ((prev_avg * (count - 1)) + processing_time) / count

    def get_generation_stats(self) -> dict[str, Any]:
        """Get generation statistics."""
        return {
            **self.generation_stats,
            "config": {
                "model": self.config.llm.model,
                "temperature": self.config.llm.temperature,
                "max_tokens": self.config.llm.max_tokens,
                "streaming": self.config.llm.streaming,
            },
        }

    def clear_stats(self) -> None:
        """Clear generation statistics."""
        self.generation_stats = {"total_generations": 0, "total_tokens_used": 0, "avg_response_time": 0.0, "errors": 0}
        logger.info("Generation statistics cleared")
