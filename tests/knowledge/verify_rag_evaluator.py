import os
import shutil
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from tools.rag.enhanced.embeddings import EnhancedRAG, RetrievalConfig
from tools.rag.enhanced.evaluator import RAGEvaluator


def verify_rag_evaluator():
    print("--- Verifying RAG Evaluator ---")

    # 1. Setup RAG index
    db_path = ".test_eval_rag_db"
    if os.path.exists(db_path):
        shutil.rmtree(db_path)

    config = RetrievalConfig(similarity_threshold=0.1)
    rag = EnhancedRAG(config, db_path=db_path)

    # Index test documents
    docs = [
        ("The StrategicReasoningLibrary handles planning.", {"doc_id": "doc_1"}),
        ("Grid analytics provides real-time monitoring.", {"doc_id": "doc_2"}),
        ("Coinbase integration handles revenue pipelines.", {"doc_id": "doc_3"}),
    ]

    print("Indexing documents...")
    for text, meta in docs:
        rag.index_document(text, meta)

    # 2. Setup Test Set (Ground Truth)
    test_set = [
        {
            "query": "StrategicReasoningLibrary",
            "expected_doc_ids": ["doc_1_0"],  # ChromaDB IDs add _0 per indexing logic
        },
        {"query": "Grid analytics", "expected_doc_ids": ["doc_2_0"]},
        {"query": "Something else entirely", "expected_doc_ids": ["non_existent"]},
    ]

    # 3. Evaluate
    evaluator = RAGEvaluator(rag)
    print("Running evaluation...")
    metrics = evaluator.evaluate(test_set, top_k=2)

    print(f"Metrics: {metrics}")

    # Expected calculations:
    # Query 1: doc_1_0 should be at rank 1. Hit: Yes, RR: 1.0
    # Query 2: doc_2_0 should be at rank 1. Hit: Yes, RR: 1.0
    # Query 3: No document should match. Hit: No, RR: 0.0

    # Hit Rate: 2/3 = 0.67
    # MRR: (1.0 + 1.0 + 0.0) / 3 = 0.67

    expected_hit_rate = 2 / 3
    expected_mrr = 2 / 3

    if abs(metrics["hit_rate"] - expected_hit_rate) < 0.01 and abs(metrics["mrr"] - expected_mrr) < 0.01:
        print("\nSUCCESS: RAG Evaluator verified! ✅")
        return True
    else:
        print("\nFAILURE: Metrics mismatch! ❌")
        return False


if __name__ == "__main__":
    success = verify_rag_evaluator()
    sys.exit(0 if success else 1)
