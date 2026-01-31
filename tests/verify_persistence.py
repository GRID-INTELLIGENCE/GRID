import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from grid.intelligence.ai_brain_bridge import KnowledgeGraphBridge
from grid.intelligence.brain import AIBrain

async def verify_persistence():
    print("--- Verifying Knowledge Graph Persistence ---")
    brain = AIBrain()
    
    # Instance 1: Add data
    bridge1 = KnowledgeGraphBridge(brain)
    node_id = await bridge1.add_navigation_node((42.0, 42.0), {"source": "bridge1_test"})
    print(f"Instance 1: Added node {node_id}")
    
    # Ensure bridge1's store is disconnected to flush to disk
    bridge1.store.disconnect()
    
    # Instance 2: Check persistence
    print("Instance 2: Initializing...")
    bridge2 = KnowledgeGraphBridge(brain)
    
    nodes = list(bridge2.graph.nodes)
    print(f"Instance 2: Found nodes: {nodes}")
    
    if node_id in nodes:
        print("\nSUCCESS: Persistence verified! ✅")
        return True
    else:
        print("\nFAILURE: Persistence failed! ❌")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_persistence())
    sys.exit(0 if success else 1)
