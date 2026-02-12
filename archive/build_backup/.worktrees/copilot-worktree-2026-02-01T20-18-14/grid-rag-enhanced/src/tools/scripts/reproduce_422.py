import sys
import os
import traceback

slots_path = "e:/grid/light_of_the_seven/light_of_the_seven"
sys.path.insert(0, os.path.abspath(slots_path))

from cognitive_layer.navigation.input_processor import NavigationInputProcessor, InputProcessingError

processor = NavigationInputProcessor()

# 1. Success case in test
print("--- Case 1: Success case ---")
raw_input = {
    "goal": "Create a new API endpoint for authentication",
    "context": {"project": "mothership", "framework": "fastapi"},
    "max_alternatives": 3,
    "enable_learning": True,
    "learning_weight": 0.3,
    "adaptation_threshold": 0.7,
    "source": None
}
try:
    req = processor.process(raw_input)
    print("Success!")
    print(f"Goal type: {req.goal.goal_type}")
except Exception:
    traceback.print_exc()

# 2. Minimal case
print("\n--- Case 2: Minimal case ---")
raw_input = {
    "goal": "Implement user login",
    "context": {},
    "max_alternatives": 3,
    "enable_learning": True,
    "learning_weight": 0.3,
    "adaptation_threshold": 0.7,
    "source": None
}
try:
    req = processor.process(raw_input)
    print("Success!")
except Exception:
    traceback.print_exc()
