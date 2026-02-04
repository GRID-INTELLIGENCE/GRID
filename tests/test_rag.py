import pytest

pytest.importorskip("chromadb")

import json
import subprocess
from pathlib import Path

from grid.rag import Doc, InMemoryIndex, RagQA
from tools.rag.indexer import index_repository
from tools.rag.store import VectorStore
from tools.rag.vector_store.base import BaseVectorStore

try:
    from tools.rag.retrieval.retriever import Retriever
except ModuleNotFoundError:
    try:
        from tools.rag.retriever import Retriever
    except ModuleNotFoundError:
        pytest.skip("Retriever implementation not available", allow_module_level=True)


class OllamaEmbedding:
    """Wrapper for Ollama's nomic-embed-text embedding model."""

    def __init__(self, model: str = "nomic-embed-text"):
        self.model = model

    def embed(self, text: str) -> dict[str, float]:
        """Get embeddings using Ollama."""
        try:
            result = subprocess.run(
                ["ollama", "run", self.model, text], capture_output=True, text=True, check=True, encoding="utf-8"
            )
            # Convert dense vector to sparse dict for compatibility
            vector = json.loads(result.stdout)
            return {str(i): v for i, v in enumerate(vector) if abs(v) > 0.01}
        except Exception as e:
            print(f"Embedding error: {e}")
            # Fallback to basic word frequency
            words = text.lower().split()
            return {word: words.count(word) for word in set(words)}


class NemotronLLM:
    """Wrapper for Nemotron LLM via Ollama."""

    def __init__(self, model: str = "nemo"):
        self.model = model

    def generate(self, prompt: str) -> str:
        """Generate completion using Nemotron."""
        try:
            result = subprocess.run(
                ["ollama", "run", self.model, prompt], capture_output=True, text=True, check=True, encoding="utf-8"
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"LLM error: {e}")
            return f"Error: Could not generate response using {self.model}"


def test_chunk_embedding_and_query(tmp_path: Path):
    # Create a tiny repo
    p = tmp_path / "repo"
    p.mkdir()
    f = p / "a.py"
    f.write_text("""def add(a,b):\n    return a + b\n\n# logging: use standard library logging module\n""")

    store_path = str(tmp_path / "store.pickle")
    store = index_repository(str(p), store_path=store_path, chunk_size=50, overlap=10, rebuild=True)
    assert isinstance(store, BaseVectorStore), f"Expected BaseVectorStore, got {type(store)}"
    assert store.count() >= 1, f"Expected at least 1 document, got {store.count()}"

    retr = Retriever(store)
    retrieved_docs, retrieved_metas, retrieved_scores = retr.retrieve("How is logging done?", k=3)
    assert retrieved_docs
    # ensure we get some score values
    assert all(isinstance(s, float) for s in retrieved_scores)


def test_ollama_rag_demo(tmp_path: Path):
    """Demonstrate RAG with Ollama models."""
    # Initialize models
    embedder = OllamaEmbedding()
    llm = NemotronLLM()

    # Create store
    store = VectorStore()

    # Sample docs about Grid
    docs = [
        "The Grid system uses RAG (Retrieval Augmented Generation) to enhance LLM responses with relevant context.",
        "Vector stores are used to efficiently search through embedded documents using similarity metrics.",
        "Ollama provides local access to open source language models and embedding models.",
        "NDJSON (Newline Delimited JSON) is used for data exchange between components.",
    ]

    # Add documents with embeddings
    store.add(
        ids=[f"doc{i}" for i in range(len(docs))],
        docs=docs,
        embeddings=[embedder.embed(doc) for doc in docs],
        metadatas=[{"source": "demo"} for _ in docs],
    )

    # Test retrieval
    query = "How does Grid use RAG?"
    query_emb = embedder.embed(query)
    retrieved_docs, metas, scores = store.query(query_emb, k=2)

    assert len(retrieved_docs) == 2
    assert any("Grid" in doc for doc in retrieved_docs)
    assert all(meta["source"] == "demo" for meta in metas)
    assert all(isinstance(score, float) for score in scores)

    # Test LLM integration
    answer = store.query_with_llm(query, llm)
    print(f"\nQuery: {query}")
    print(f"Answer: {answer}")

    assert isinstance(answer, str)
    assert len(answer) > 0

    # Test NDJSON roundtrip
    data = store.to_ndjson()

    # Verify we can load it back
    new_store = VectorStore.from_ndjson(data)
    assert len(new_store.docs) == len(docs), (
        f"Expected {len(docs)} documents after loading from NDJSON, got {len(new_store.docs)}"
    )

    new_docs, _, _ = new_store.query(query_emb, k=1)
    assert new_docs == store.query(query_emb, k=1)[0]


def run_interactive_demo():
    """Run interactive RAG demo."""
    print("Initializing RAG demo...")
    embedder = OllamaEmbedding()
    llm = NemotronLLM()
    store = VectorStore()

    # Add sample documents
    docs = [
        "Grid is a research framework for exploring intelligence and cognition.",
        "The system uses RAG to combine retrieval with generation.",
        "Vector embeddings help find relevant information efficiently.",
        "Local LLMs via Ollama reduce dependency on external services.",
    ]

    print("Adding documents...")
    store.add(
        ids=[f"doc{i}" for i in range(len(docs))],
        docs=docs,
        embeddings=[embedder.embed(doc) for doc in docs],
        metadatas=[{"source": "interactive_demo"} for _ in docs],
    )

    print("\nRAG Demo Ready!")
    print("Ask questions about Grid and the system will use relevant context to answer.")
    print("Enter 'quit' to exit.")

    while True:
        query = input("\nQuestion: ").strip()
        if query.lower() == "quit":
            break

        answer = store.query_with_llm(query, llm)
        print(f"\nAnswer: {answer}")


def test_index_and_retrieve_basic():
    docs = [
        Doc(doc_id="d1", text="Apple pie is delicious and often made with cinnamon.", metadata={"title": "apple"}),
        Doc(doc_id="d2", text="Banana bread can be moist and sweet.", metadata={"title": "banana"}),
    ]
    idx = InMemoryIndex()
    idx.add_documents_chunked(docs, chunk_size=20, overlap=2)
    retr = Retriever(idx)
    results = retr.retrieve_with_scores("cinnamon", top_k=2)
    assert results, "Expected at least one retrieval result for 'cinnamon'"
    # best result should mention apple / cinnamon
    top_doc, score = results[0]
    assert "cinnamon" in top_doc.text.lower() or "apple" in top_doc.text.lower()


def test_ragqa_returns_answer_and_sources():
    docs = [
        Doc(doc_id="d1", text="The Eiffel Tower is in Paris.", metadata={"title": "eiffel"}),
        Doc(doc_id="d2", text="Lyon is a city in France.", metadata={"title": "lyon"}),
    ]
    rag = RagQA(index=InMemoryIndex())
    rag.index_documents(docs, chunked=True, chunk_size=50, overlap=5)
    out = rag.answer("Where is the Eiffel Tower?", top_k=2)
    assert isinstance(out, dict)
    assert "answer" in out and out["answer"], "Expected non-empty answer"
    assert "sources" in out and out["sources"], "Expected non-empty sources list"
    # sources should reference the eiffel document id or metadata
    found = any("eiffel" in (s.get("doc_id") or "") or "d1" in s.get("doc_id", "") for s in out["sources"])
    assert found, f"Expected sources to reference the eiffel doc; got {out['sources']}"


def test_ragqa_with_llm_adapter():
    from grid.rag import Doc, DummyLLMAdapter, InMemoryIndex, RagQA

    docs = [
        Doc(doc_id="d1", text="Mercury is the closest planet to the sun.", metadata={"title": "mercury"}),
        Doc(doc_id="d2", text="Venus is the second planet and has a thick atmosphere.", metadata={"title": "venus"}),
    ]
    idx = InMemoryIndex()
    rag = RagQA(index=idx, generator=DummyLLMAdapter())
    rag.index_documents(docs, chunked=True, chunk_size=50, overlap=5)
    out = rag.answer("Which planet is closest to the sun?", top_k=2)
    assert isinstance(out, dict)
    assert "answer" in out and "DummyLLM" in out["answer"]
    assert "sources" in out and out["sources"], "Expected sources to be present"


if __name__ == "__main__":
    # Run interactive demo
    run_interactive_demo()
