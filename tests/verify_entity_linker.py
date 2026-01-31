import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from grid.knowledge.graph_store import Entity
from grid.knowledge.graph_schema import EntityType
from grid.knowledge.persistent_store import PersistentJSONKnowledgeStore
from grid.knowledge.entity_linker import EntityLinker

def verify_entity_linking():
    print("--- Verifying Cross-Project Entity Linking ---")
    
    # 1. Setup Store
    kg_path = "dev/test_linker_kg.json"
    if os.path.exists(kg_path):
        os.remove(kg_path)
    
    store = PersistentJSONKnowledgeStore(kg_path)
    linker = EntityLinker(store)
    
    # 2. Create Entity A (Project: GRID)
    now = datetime.now()
    entity_a = Entity(
        entity_id="grid_agent_x",
        entity_type=EntityType.AGENT,
        properties={
            "id": "grid_agent_x",
            "name": "Mothership-Sentinel-Prime",
            "project": "grid",
            "created_at": now.isoformat()
        },
        created_at=now,
        updated_at=now
    )
    store.store_entity(entity_a)
    
    # 3. Create Entity B (Project: Coinbase - Similar Name)
    entity_b = Entity(
        entity_id="cb_agent_y",
        entity_type=EntityType.AGENT,
        properties={
            "id": "cb_agent_y",
            "name": "Mothership Sentinel Prime", # Different format, same normalized
            "project": "coinbase",
            "created_at": now.isoformat()
        },
        created_at=now,
        updated_at=now
    )
    store.store_entity(entity_b)
    
    print(f"Entities created: {entity_a.entity_id} (GRID), {entity_b.entity_id} (Coinbase)")
    
    # 4. Run Linker
    print("Running EntityLinker.process_new_entity on Entity B...")
    linker.process_new_entity(entity_b)
    
    # 5. Check for relationships
    store.disconnect() # Flush
    store = PersistentJSONKnowledgeStore(kg_path) # Reload
    store.connect() # Load from disk
    
    print(f"Relationships in store: {len(store.relationships)}")
    rels = store.relationships
    found_link = False
    for rel_id, rel in rels.items():
        print(f"  - {rel.from_entity_id} -> {rel.to_entity_id}: {rel.properties}")
        # Check both directions
        is_link = (rel.from_entity_id == entity_b.entity_id and rel.to_entity_id == entity_a.entity_id) or \
                  (rel.from_entity_id == entity_a.entity_id and rel.to_entity_id == entity_b.entity_id)
        if is_link and rel.properties.get("link_type") == "SAME_AS":
            found_link = True
            print(f"Success: Found link between {entity_b.entity_id} and {entity_a.entity_id}! ✅")
            break
    
    if found_link:
        print("\nSUCCESS: Cross-Project Entity Linking verified! ✅")
        return True
    else:
        print("\nFAILURE: No link created between identical entities! ❌")
        return False

if __name__ == "__main__":
    success = verify_entity_linking()
    sys.exit(0 if success else 1)
