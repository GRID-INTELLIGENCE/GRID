"""On-demand (query-time) RAG engine with hooks and recursive scoping."""

from __future__ import annotations

import logging
import os
import re
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import RAGConfig
from .embeddings.factory import get_embedding_provider
from .indexer import chunk_text, read_file_content
from .llm.factory import get_llm_provider
from .llm.llama_cpp import LlamaCppLLM
from .llm.simple import SimpleLLM
from .model_router import ModelRoutingDecision, route_models
from .utils import check_ollama_connection
from .vector_store import InMemoryDenseVectorStore

logger = logging.getLogger(__name__)


@dataclass
class RAGHooks:
    on_route: Callable[[str, ModelRoutingDecision], None] | None = None
    on_seed_files: Callable[[list[Path]], None] | None = None
    on_expand_files: Callable[[int, list[Path]], None] | None = None
    on_chunked: Callable[[int], None] | None = None
    on_embedded: Callable[[int], None] | None = None
    on_retrieved: Callable[[list[dict[str, Any]]], None] | None = None
    on_prompt: Callable[[str], None] | None = None


@dataclass
class OnDemandRAGResult:
    answer: str
    context: str
    sources: list[dict[str, Any]]
    routing: dict[str, Any]
    selected_files: list[dict[str, Any]]
    stats: dict[str, Any]
    degraded: bool = False
    degradation_reasons: list[str] | None = None


class OnDemandRAGEngine:
    def __init__(
        self,
        config: RAGConfig | None = None,
        docs_root: str | Path = "docs",
        repo_root: str | Path = ".",
        hooks: RAGHooks | None = None,
    ) -> None:
        self.config = config or RAGConfig.from_env()
        self.config.ensure_local_only()
        self.docs_root = Path(docs_root)
        self.repo_root = Path(repo_root)
        self.hooks = hooks or RAGHooks()

    def query(
        self,
        query_text: str,
        depth: int = 0,
        top_k: int | None = None,
        max_files: int = 600,
        prefilter_k_files: int = 50,
        max_chunks: int | None = 2000,
        prefilter_scan_bytes: int = 64 * 1024,
        temperature: float = 0.3,
        include_codebase: bool = False,
        gguf_model_path: str | None = None,
    ) -> OnDemandRAGResult:
        top_k = top_k or self.config.top_k

        routing = route_models(query_text, base_config=self.config, prefer_ollama=True)
        if self.hooks.on_route:
            self.hooks.on_route(query_text, routing)

        # Instantiate providers based on routing (strictly local)
        # Reuse self.config as base instead of re-parsing env vars
        routed_config = self.config.copy() if hasattr(self.config, "copy") else RAGConfig.from_env()
        routed_config.ensure_local_only()
        routed_config.embedding_provider = routing.embedding_provider
        routed_config.embedding_model = routing.embedding_model
        routed_config.llm_model_local = routing.llm_model

        embedding_provider = get_embedding_provider(config=routed_config)
        embedding_fallback_provider = None
        try:
            # If Ollama embeddings fail (context/window issues), fall back to HF embeddings locally.
            fallback_cfg = self.config.copy() if hasattr(self.config, "copy") else RAGConfig.from_env()
            fallback_cfg.ensure_local_only()
            fallback_cfg.embedding_provider = "huggingface"
            fallback_cfg.embedding_model = self.config.embedding_model
            embedding_fallback_provider = get_embedding_provider(config=fallback_cfg)
        except Exception:
            embedding_fallback_provider = None

        if gguf_model_path:
            llm_provider = LlamaCppLLM(model_path=gguf_model_path)
        else:
            # If Ollama isn't reachable, gracefully degrade to SimpleLLM
            if not check_ollama_connection(routed_config.ollama_base_url):
                llm_provider = SimpleLLM()
                routing.reason = f"{routing.reason}; ollama_reachable=false; llm=fallback:simple"
            else:
                llm_provider = get_llm_provider(config=routed_config)

        # 1) Seed scope with docs/ using a cheap prefilter so we don't index everything.
        # We first collect candidates (bounded by max_files), then score them and keep top prefilter_k_files.
        candidates = self._collect_files(self.docs_root, limit=max_files)
        scored = self._prefilter_files(
            query_text=query_text,
            files=candidates,
            k=prefilter_k_files,
            scan_bytes=prefilter_scan_bytes,
        )
        seed_files = [p for p, _score in scored]
        if include_codebase:
            # Add a small set of code/entrypoint seeds to help bridging docs->code.
            seed_files.extend(self._collect_files(self.repo_root, limit=max(0, max_files - len(seed_files))))

        seed_files = self._dedupe_paths(seed_files)[:max_files]
        if self.hooks.on_seed_files:
            self.hooks.on_seed_files(seed_files)

        # 2) Recursive scope expansion based on query->retrieved->pattern search
        files = list(seed_files)
        expanded: set[str] = {str(p.resolve()) for p in files}

        # Vector store is ephemeral (built from current file scope)
        store = InMemoryDenseVectorStore()
        index_result = self._index_files_into_store(
            files,
            store,
            embedding_provider,
            embedding_fallback_provider,
            max_chunks=max_chunks,
        )
        chunk_count = index_result["count"]
        embedding_degraded = index_result["degraded"]
        degradation_reasons: list[str] = []
        if index_result["fallback"] > 0:
            degradation_reasons.append(f"{index_result['fallback']} chunks used fallback embedding provider")
        if index_result["simple_fallback"] > 0:
            degradation_reasons.append(f"{index_result['simple_fallback']} chunks used word-frequency embedding (non-semantic)")

        if self.hooks.on_chunked:
            self.hooks.on_chunked(chunk_count)
        if self.hooks.on_embedded:
            self.hooks.on_embedded(chunk_count)

        # Expand loop: retrieve then add more files and re-index incrementally
        for d in range(max(0, depth)):
            retrieved = self._retrieve(query_text, store, embedding_provider, top_k=top_k)
            seeds = self._suggest_patterns(query_text, retrieved)
            new_files = self._expand_scope(seeds, expanded, max_new=200, include_codebase=include_codebase)
            if not new_files:
                break

            if self.hooks.on_expand_files:
                self.hooks.on_expand_files(d + 1, new_files)

            files.extend(new_files)
            for nf in new_files:
                expanded.add(str(nf.resolve()))

            # Index only newly added files
            expand_result = self._index_files_into_store(
                new_files,
                store,
                embedding_provider,
                embedding_fallback_provider,
                max_chunks=max_chunks,
            )
            if expand_result["degraded"]:
                embedding_degraded = True
                if expand_result["fallback"] > 0:
                    degradation_reasons.append(f"expansion round {d+1}: {expand_result['fallback']} fallback")
                if expand_result["simple_fallback"] > 0:
                    degradation_reasons.append(f"expansion round {d+1}: {expand_result['simple_fallback']} simple_fallback")

        # Final retrieval after expansions
        retrieved = self._retrieve(query_text, store, embedding_provider, top_k=top_k)
        if self.hooks.on_retrieved:
            self.hooks.on_retrieved(retrieved)

        context, sources = self._build_context(retrieved)

        prompt = (
            "Based on the following context from the GRID repository, answer the query. "
            "If you cite facts, reference the most relevant sources.\n\n"
            f"Context:\n{context}\n\n"
            f"Query: {query_text}\n\nAnswer:"
        )
        if self.hooks.on_prompt:
            self.hooks.on_prompt(prompt)

        answer = llm_provider.generate(prompt=prompt, temperature=temperature)

        # Detect LLM degradation (SimpleLLM fallback)
        llm_degraded = type(llm_provider).__name__ == "SimpleLLM"
        if llm_degraded:
            degradation_reasons.append("LLM degraded to SimpleLLM (Ollama unreachable)")

        return OnDemandRAGResult(
            answer=answer,
            context=context,
            sources=sources,
            routing={
                "embedding_provider": routing.embedding_provider,
                "embedding_model": routing.embedding_model,
                "llm_provider": routing.llm_provider,
                "llm_model": routing.llm_model,
                "reason": routing.reason,
            },
            selected_files=[
                {"path": self._safe_relpath(p), "score": float(score)} for p, score in scored[:prefilter_k_files]
            ],
            stats={
                "prefilter_candidates": len(candidates),
                "prefilter_selected": min(prefilter_k_files, len(scored)),
                "files_indexed_initial": len(files),
                "chunks_indexed": chunk_count,
                "embedding_primary": index_result["primary"],
                "embedding_fallback": index_result["fallback"],
                "embedding_simple_fallback": index_result["simple_fallback"],
                "depth": depth,
                "top_k": top_k,
                "chunk_size": self.config.chunk_size,
                "chunk_overlap": self.config.chunk_overlap,
            },
            degraded=embedding_degraded or llm_degraded,
            degradation_reasons=degradation_reasons if degradation_reasons else None,
        )

    def _prefilter_files(
        self, query_text: str, files: Sequence[Path], k: int, scan_bytes: int = 64 * 1024
    ) -> list[tuple[Path, float]]:
        """Cheap file scoring to avoid indexing the entire docs corpus.

        Scoring strategy:
        - Filename/path token match (high weight)
        - Bounded content scan for token match (lower weight)
        """
        tokens = self._keywords(query_text)
        if not tokens:
            return [(p, 0.0) for p in list(files)[:k]]

        scored: list[tuple[Path, float]] = []

        # Pass 1: filename/path-only scoring (cheap)
        for p in files:
            score = 0.0
            name = p.as_posix().lower()
            for t in tokens:
                if t in name:
                    score += 3.0
            if score > 0.0:
                scored.append((p, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        if len(scored) >= k:
            return scored[:k]

        # Pass 2: bounded content scan only if needed
        remaining = [p for p in files if all(p != sp for sp, _ in scored)]
        for p in remaining:
            score = 0.0
            content = read_file_content(p, max_size=scan_bytes) or ""
            content_l = content.lower()
            for t in tokens:
                if t in content_l:
                    score += 1.0
            if score > 0.0:
                scored.append((p, score))
            if len(scored) >= k:
                break

        scored.sort(key=lambda x: x[1], reverse=True)
        if not scored:
            return [(p, 0.0) for p in list(files)[:k]]
        return scored[:k]

    def _collect_files(self, root: Path, limit: int) -> list[Path]:
        root = root.resolve()
        if not root.exists():
            return []

        exclude_dirs = {
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "__pycache__",
            ".rag_db",
            ".rag_logs",
            "dist",
            "build",
        }
        allow_ext = {
            ".md",
            ".txt",
            ".rst",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".py",
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
        }

        out: list[Path] = []
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune excluded directories in-place to prevent traversal
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
            for fname in filenames:
                if len(out) >= limit:
                    return out
                try:
                    p = Path(dirpath) / fname
                    if p.suffix.lower() not in allow_ext:
                        continue
                    try:
                        if p.stat().st_size > 1024 * 1024:
                            continue
                    except OSError:
                        continue
                    out.append(p)
                except (OSError, PermissionError):
                    continue
        return out

    @staticmethod
    def _dedupe_paths(paths: Sequence[Path]) -> list[Path]:
        seen: set[str] = set()
        out: list[Path] = []
        for p in paths:
            try:
                key = os.path.normcase(os.path.normpath(str(p.resolve())))
            except Exception:
                key = os.path.normcase(os.path.normpath(str(p)))
            if key in seen:
                continue
            seen.add(key)
            out.append(p)
        return out

    def _index_files_into_store(
        self,
        files: Sequence[Path],
        store: InMemoryDenseVectorStore,
        embedding_provider: Any,
        embedding_fallback_provider: Any = None,
        max_chunks: int | None = None,
    ) -> dict[str, Any]:
        ids: list[str] = []
        docs: list[str] = []
        metas: list[dict[str, Any]] = []

        for file_path in files:
            if max_chunks is not None and len(docs) >= max_chunks:
                break
            content = read_file_content(file_path)
            if content is None or not content.strip():
                continue

            # Chunk
            chunks = chunk_text(
                content,
                chunk_size=self.config.chunk_size,
                overlap=self.config.chunk_overlap,
                max_chunk_size=4000,
            )
            for i, ch in enumerate(chunks):
                if max_chunks is not None and len(docs) >= max_chunks:
                    break
                rel = self._safe_relpath(file_path)
                ids.append(f"{rel}#{i}")
                docs.append(ch)
                metas.append({"path": rel, "chunk_index": i, "type": "chunk"})

        if not docs:
            return {"count": 0, "primary": 0, "fallback": 0, "simple_fallback": 0, "degraded": False}

        # Embed sequentially (keep one-at-a-time behavior) with progress + ETA
        embeddings: list[list[float]] = []
        total = len(docs)
        t0 = time.time()
        last_print = 0.0
        printed_any = False
        primary_count = 0
        fallback_count = 0
        simple_fallback_count = 0
        for text in docs:
            idx = len(embeddings) + 1
            emb = None
            origin = "primary"
            # Aggressive truncation for embedding stability across models
            candidate_texts = [text[:2000], text[:1000], text[:600]]
            _last_err: Exception | None = None
            for ct in candidate_texts:
                try:
                    emb = embedding_provider.embed(ct)
                    break
                except Exception as e:
                    _last_err = e
                    continue

            if emb is None and embedding_fallback_provider is not None:
                origin = "fallback"
                for ct in candidate_texts:
                    try:
                        emb = embedding_fallback_provider.embed(ct)
                        break
                    except Exception as e:
                        _last_err = e
                        continue

            if emb is None:
                from .embeddings.simple import SimpleEmbedding

                origin = "simple_fallback"
                if _last_err is not None:
                    logger.debug("Embedding fallback to simple: %s", _last_err)
                emb = SimpleEmbedding(use_tfidf=False).embed(candidate_texts[-1])

            if origin == "primary":
                primary_count += 1
            elif origin == "fallback":
                fallback_count += 1
            else:
                simple_fallback_count += 1

            embeddings.append(list(emb) if not isinstance(emb, list) else emb)

            # Progress / ETA (print at most once per second)
            now = time.time()
            if now - last_print >= 1.0 or idx == total:
                elapsed = now - t0
                rate = idx / elapsed if elapsed > 0 else 0.0
                remaining = (total - idx) / rate if rate > 0 else 0.0
                pct = (idx / total) * 100.0 if total > 0 else 100.0
                print(f"Embedding progress: {idx}/{total} ({pct:.1f}%) | ETA: {remaining:.1f}s")
                last_print = now
                printed_any = True

        store.add(ids=ids, documents=docs, embeddings=embeddings, metadatas=metas)
        if printed_any:
            total_elapsed = time.time() - t0
            print(f"Embedding complete: {total}/{total} (100.0%) | elapsed: {total_elapsed:.1f}s")

        degraded = (fallback_count + simple_fallback_count) > 0
        if degraded:
            import logging as _logging

            _log = _logging.getLogger(__name__)
            _log.warning(
                "Embedding quality degraded: %d/%d primary, %d fallback, %d simple_fallback",
                primary_count, total, fallback_count, simple_fallback_count,
            )

        return {
            "count": len(docs),
            "primary": primary_count,
            "fallback": fallback_count,
            "simple_fallback": simple_fallback_count,
            "degraded": degraded,
        }

    def _retrieve(
        self, query_text: str, store: InMemoryDenseVectorStore, embedding_provider: Any, top_k: int
    ) -> list[dict[str, Any]]:
        q_emb = embedding_provider.embed(query_text)
        q = list(q_emb) if not isinstance(q_emb, list) else q_emb
        results = store.query(query_embedding=q, n_results=top_k)

        retrieved: list[dict[str, Any]] = []
        for doc, meta, dist, doc_id in zip(
            results.get("documents", []),
            results.get("metadatas", []),
            results.get("distances", []),
            results.get("ids", []),
            strict=False,
        ):
            retrieved.append({"id": doc_id, "document": doc, "metadata": meta, "distance": dist})
        return retrieved

    def _build_context(
        self, retrieved: list[dict[str, Any]], max_chars: int = 12000
    ) -> tuple[str, list[dict[str, Any]]]:
        context_parts: list[str] = []
        sources: list[dict[str, Any]] = []
        used = 0

        for i, r in enumerate(retrieved, 1):
            meta = r.get("metadata") or {}
            path = str(meta.get("path", ""))
            chunk_idx = meta.get("chunk_index")
            header = f"[{i}] {path}#{chunk_idx} (distance={r.get('distance'):.4f})"
            body = str(r.get("document", ""))
            part = f"{header}\n{body}".strip()

            if used + len(part) > max_chars and context_parts:
                break
            context_parts.append(part)
            used += len(part)

            sources.append({"index": i, "distance": r.get("distance"), "metadata": meta, "id": r.get("id")})

        return "\n\n".join(context_parts), sources

    def _suggest_patterns(self, query_text: str, retrieved: list[dict[str, Any]]) -> list[str]:
        # Seed patterns from query tokens + file stems of top results
        tokens = self._keywords(query_text)
        for r in retrieved[:5]:
            meta = r.get("metadata") or {}
            p = str(meta.get("path") or "")
            if p:
                stem = Path(p).stem
                tokens.extend(self._keywords(stem))
        # Keep it small and high signal
        out: list[str] = []
        seen: set[str] = set()
        for t in tokens:
            if t in seen:
                continue
            seen.add(t)
            out.append(t)
            if len(out) >= 20:
                break
        return out

    def _expand_scope(
        self, patterns: Sequence[str], expanded: set[str], max_new: int, include_codebase: bool
    ) -> list[Path]:
        roots = [self.docs_root]
        if include_codebase:
            roots.append(self.repo_root)

        new_files: list[Path] = []
        for root in roots:
            for p in self._search_files_by_patterns(root, patterns, limit=max_new):
                try:
                    key = str(p.resolve())
                except Exception:
                    key = str(p)
                if key in expanded:
                    continue
                expanded.add(key)
                new_files.append(p)
                if len(new_files) >= max_new:
                    return new_files
        return new_files

    def _search_files_by_patterns(self, root: Path, patterns: Sequence[str], limit: int) -> Iterable[Path]:
        root = root.resolve()
        if not root.exists() or not patterns:
            return []

        allow_ext = {".md", ".txt", ".rst", ".json", ".yaml", ".yml", ".toml", ".py", ".ts", ".tsx", ".js", ".jsx"}
        compiled = [re.compile(re.escape(pat), re.IGNORECASE) for pat in patterns if pat and len(pat) >= 3]

        out: list[Path] = []
        for p in root.rglob("*"):
            if len(out) >= limit:
                break
            try:
                if not p.is_file():
                    continue
                if p.suffix.lower() not in allow_ext:
                    continue
                try:
                    if p.stat().st_size > 1024 * 1024:
                        continue
                except OSError:
                    continue

                # Fast path: filename match
                name = p.name
                if any(rx.search(name) for rx in compiled):
                    out.append(p)
                    continue

                # Content match (bounded)
                content = read_file_content(p, max_size=64 * 1024) or ""
                if content is None:
                    continue
                if any(rx.search(content) for rx in compiled):
                    out.append(p)
            except (OSError, PermissionError):
                continue

        return out

    @staticmethod
    def _keywords(text: str) -> list[str]:
        parts = re.findall(r"[a-zA-Z0-9_\-]{3,}", text.lower())
        stop = {
            "the",
            "and",
            "for",
            "with",
            "that",
            "this",
            "from",
            "into",
            "your",
            "grid",
            "docs",
            "file",
            "files",
        }
        return [p for p in parts if p not in stop]

    def _safe_relpath(self, p: Path) -> str:
        try:
            return p.resolve().relative_to(self.repo_root.resolve()).as_posix()
        except Exception:
            try:
                return p.resolve().relative_to(self.docs_root.resolve()).as_posix()
            except Exception:
                return p.as_posix()
