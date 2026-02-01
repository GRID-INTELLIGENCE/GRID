import sys

sys.path.insert(0, "E:/grid/src")

import os

os.environ["GRID_QUIET"] = "1"
os.environ["USE_DATABRICKS"] = "false"

try:
    from tools.rag.config import RAGConfig
    print("1. RAGConfig OK")

    config = RAGConfig.from_env()
    config.ensure_local_only()
    print("2. Config loaded OK")

    from tools.rag.rag_engine import RAGEngine
    print("3. RAGEngine import OK")

    engine = RAGEngine(config=config)
    print("4. RAGEngine init OK")

    stats = engine.get_stats()
    print(f"5. Stats: {stats}")

except Exception as e:
    print(f"FAIL at step: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
