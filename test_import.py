import sys

sys.path.insert(0, "E:/grid/src")

try:
    print("OK: IntentClassifier imported")
except Exception as e:
    print(f"FAIL: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
