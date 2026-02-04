"""
Cognition Module Usage Examples

Basic examples demonstrating how to use the cognition module components.
"""

import time

# Example 1: Basic Flow Management
from cognition.Flow import FlowEvent, FlowManager

# Create a flow manager
flow_manager = FlowManager()

# Create a cognitive flow
flow = flow_manager.create_flow(flow_id="example_flow", name="Example Cognitive Flow", domain="software_development")

# Add events to the flow
event1 = FlowEvent(
    event_id="perception_1",
    event_type="perception",
    timestamp=time.time(),
    data={"stimulus": "code_review", "complexity": "high"},
)

flow_manager.process_event("example_flow", event1)

# Example 2: Pattern Matching
from cognition.Pattern import PatternManager, PatternType

# Create a pattern manager
pattern_manager = PatternManager()

# Create a semantic pattern
pattern = pattern_manager.create_pattern_from_template(
    pattern_id="bug_pattern",
    name="Bug Detection Pattern",
    pattern_type=PatternType.SEMANTIC,
    template={
        "keywords": ["error", "exception", "bug", "issue"],
        "phrases": ["stack trace", "null pointer", "index out of bounds"],
    },
)

# Match pattern against input
confidence, details = pattern_manager.match_pattern("bug_pattern", "Found a null pointer exception in the code")

# Example 3: Temporal Context
from cognition.Time import TimeManager

# Create a time manager
time_manager = TimeManager()

# Create a temporal context
context = time_manager.create_context(context_id="dev_session", timezone_offset=-5.0, session_type="coding")  # EST

# Add a time window for focused work
window = time_manager.window_manager.create_window(
    window_id="focus_time",
    start_time=time.time(),
    duration=3600,
    activity_type="deep_work",  # 1 hour
)

context.add_window(window)

# Get context statistics
stats = time_manager.get_context_statistics("dev_session")
print(f"Context statistics: {stats}")

# Clean up
time_manager.cleanup()
print("Examples completed successfully!")
