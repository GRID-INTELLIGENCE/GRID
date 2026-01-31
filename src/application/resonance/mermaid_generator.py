from typing import List, Dict

class MermaidDiagramGenerator:

    def generate_xychart(self, title: str, x_axis: List[str], y_axis: str, data: List[float]) -> str:
        return f"""
xychart-beta
    title "{title}"
    x-axis {x_axis}
    y-axis "{y_axis}" 0 --> 1
    line {data}
"""

    def generate_flowchart(self, title: str, nodes: Dict[str, str], edges: List[str]) -> str:
        node_definitions = "\n".join([f"    {id}[{text}]" for id, text in nodes.items()])
        edge_definitions = "\n".join([f"    {edge}" for edge in edges])
        return f"""
flowchart TB
    subgraph {title}
{node_definitions}
{edge_definitions}
    end
"""

    def generate_timeline(self, title: str, events: Dict[str, str]) -> str:
        event_definitions = "\n".join([f"        {time} : {event}" for time, event in events.items()])
        return f"""
timeline
    title {title}
{event_definitions}
"""
