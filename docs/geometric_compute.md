# Geometric Compute Module Documentation

> **Definition**: A bidirectional translation layer between **Visual Forms** (images, diagrams) and **Abstract Logic** (structured data, code).

## Key Components

### 1. The Interface (`IGeometricCompute`)
**Definition**: The contract that any geometric compute backend must satisfy. It ensures that the rest of the system (The Grid) can interact with vision capabilities without knowing the implementation details (e.g., Tesseract vs. Cloud Vision).

**Highlight**: Decouples "what we want to do" (interpret image) from "how we do it" (OCR library).

**Example**:
```python
# In src/core/interfaces.py
class IGeometricCompute(Protocol):
    def interpret_image(self, image_path: str) -> LogicState: ...
```

### 2. The Schema (`LogicState`, `VisualNode`)
**Definition**: The "grammar" of the visual world. It breaks down any image into a graph of **Nodes** (things) and **Edges** (relationships).

**Highlight**: Universal format. A business chart, a tech diagram, and a science plot all become `LogicState` objects, just with different node types.

**Example**:
```python
# A extracted "Submit" button
node = VisualNode(
    id="btn_1",
    type="ui_component",
    text="Submit",
    geometry={"x": 100, "y": 200, "width": 80, "height": 30}
)
```

### 3. The Interpreter (`GeometricInterpreter`)
**Definition**: The engine that reads an image and populates the Schema. It currently uses OCR to find text and spatial heuristics to infer relationships.

**Highlight**: The "Eyes" of the system. It turns pixels into data.

**Example**:
```python
interpreter = GeometricInterpreter()
state = interpreter.interpret_image("dashboard.png")
print(f"Found {len(state.nodes)} elements")
```

### 4. Use Cases (`Business`, `Tech`, `Science`)
**Definition**: Domain-specific wrappers that add meaning to the raw `LogicState`.

**Highlight**: Where the value is realized. A "node with text '$500'" becomes "Revenue Metric".

**Example**:
```python
# Business
analyzer = BusinessAnalyzer(interpreter)
metrics = analyzer.extract_sales_metrics("report.jpg")

# Tech
extractor = TechPipelineExtractor(interpreter)
steps = extractor.extract_pipeline_steps("architecture.png")
```

## Trend Analysis & "Currency of Situations"
**Concept**: The system doesn't just read data; it contextualizes it.
- **Data Possibilities**: Identifying what *could* be analyzed (e.g., "This chart has time-series data, we can forecast it").
- **Surge Detection**: Comparing extracted values against historical or external baselines (e.g., "Revenue $1.2M is 20% higher than industry avg").

*(Implementation in progress - see Phase 3)*
