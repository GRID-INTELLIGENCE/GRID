import sys
import os
import shutil

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from grid.knowledge import PersistentJSONKnowledgeStore
from grid.knowledge.graph_store import Entity
from grid.knowledge.graph_schema import EntityType
from tools.rag.enhanced.embeddings import EnhancedRAG, RetrievalConfig
from datetime import datetime

def verify_rag_enrichment():
    print("--- Verifying RAG Metadata Enrichment ---")
    
    # 1. Setup Knowledge Base
    kg_path = "dev/test_kg.json"
    if os.path.exists(kg_path):
        os.remove(kg_path)
        
    store = PersistentJSONKnowledgeStore(kg_path)
    entity_id = "strategic_reasoning_lib"
    now = datetime.now()
    entity = Entity(
        entity_id=entity_id,
        entity_type=EntityType.SKILL,
        properties={
            "id": entity_id,
            "name": "StrategicReasoningLibrary",
            "description": "Handles high-level strategic planning.",
            "created_at": now.isoformat()
        },
        created_at=now,
        updated_at=now
    )
    store.store_entity(entity)
    store.disconnect() # Flush to disk
    print(f"Added entity: StrategicReasoningLibrary ({entity_id})")

    # 2. Setup RAG
    db_path = ".test_rag_db"
    if os.path.exists(db_path):
        shutil.rmtree(db_path)
        
    config = RetrievalConfig(enable_kg_enrichment=True, similarity_threshold=0.1)
    rag = EnhancedRAG(config, db_path=db_path)
    
    # Force enricher to use our test KG path
    rag.enricher.store = PersistentJSONKnowledgeStore(kg_path)
    rag.enricher._initialized = False # Force re-initialization with new store
    
    # 3. Index document mentioning the entity
    text = "The StrategicReasoningLibrary is essential for cross-project alignment."
    metadata = {"doc_id": "test_doc", "source": "test_script"}
    
    print("Indexing document...")
    rag.index_document(text, metadata)
    
    # Print stats
    print(f"RAG Stats: {rag.get_retrieval_stats()}")
    
    # 4. Verify in ChromaDB
    print("Performing hybrid search...")
    results = rag.hybrid_search("StrategicReasoningLibrary", top_k=5)
    
    if not results:
        # Check if collection has documents at all
        all_docs = rag.collection.get()
        print(f"Collection documents: {all_docs['documents']}")
        print("FAILURE: No results found in RAG! ❌")
        return False
        
    result = results[0]
    res_metadata = result.get("metadata", {})
    
    print(f"Stored Metadata: {res_metadata}")
    
    if "kg_entities" in res_metadata:
        entities = res_metadata["kg_entities"]
        print(f"Found enriched entities: {entities}")
        
        # Check if our specific entity is there
        # Note: ChromaDB might return nested dicts as strings depending on version, 
        # but our enrichment.py adds it as a list of dicts.
        
        found = False
        import json
        
        # If it's a string (common in some Chroma versions/wrappers), parse it
        if isinstance(entities, str):
            entities = json.loads(entities)
            
        for ent in entities:
            if ent.get("entity_id") == entity_id:
                found = True
                break
        
        if found:
            print("\nSUCCESS: RAG Metadata Enrichment verified! ✅")
            return True
        else:
            print(f"\nFAILURE: Entity {entity_id} not found in enriched metadata! ❌")
            return False
    else:
        print("\nFAILURE: No kg_entities field found in metadata! ❌")
        return False

if __name__ == "__main__":
    success = verify_rag_enrichment()
    sys.exit(0 if success else 1)
