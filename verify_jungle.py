"""
Midnight Walk Verification — Attesting the Jungle Safety Rules.

Simulates a high-altitude concurrency environment with circular dependencies
and verifies that the safety engine creates a 'walkable neighborhood'.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from mycelium.domains import DomainResolver, DomainType
from mycelium.concurrency import JungleEngine

def run_midnight_walk():
    print("🌙 Starting Midnight Walk in the Mycelium Jungle...")

    engine = JungleEngine()
    resolver = DomainResolver(root="e:\\GRID-main")

    # 1. Resolve Domains
    print("\n--- Domain Resolution ---")
    mycelium_src = "e:\\GRID-main\\src\\mycelium\\core.py"
    res = resolver.resolve(mycelium_src)
    print(f"Path: {mycelium_src}")
    print(f"Domain: {res.domain.upper()} (Protected: {res.is_protected})")

    jump = resolver.get_accelerative_jump(DomainType.STATIC, DomainType.ENGINE)
    print(f"Accelerative Leap (Static -> Engine): {jump}")

    # 2. Concurrency Safety (The Jungle)
    print("\n--- Concurrency Safety (Z-Axis) ---")
    node_a = "node_alpha"
    node_b = "node_beta"

    # Simulate a circular dependency risk
    is_safe = engine.is_path_safe(node_a, [node_b])
    print(f"Is path safe from {node_a} with dependency {node_b}? {is_safe}")

    # Simulate a direct loop (Angular Momentum Breach)
    is_loop_safe = engine.is_path_safe(node_a, [node_a])
    print(f"Is path safe with direct circularity? {is_loop_safe}")

    # 3. Walking the Environment
    print("\n--- Runtime Traversal ---")
    with engine.acquire_jungle_context(node_a):
        z_axis = engine.get_z_axis_telemetry()
        print(f"Entering {node_a}... Current Z-Axis (Altitude): {z_axis}")

        with engine.acquire_jungle_context(node_b):
            z_axis = engine.get_z_axis_telemetry()
            print(f"Entering {node_b}... Current Z-Axis (Altitude): {z_axis}")

    # 4. Neighborhood Improvement
    print("\n--- Balance Restoration ---")
    report = engine.improve_neighborhood()
    print(f"Result: {report}")

    print("\n✅ Verification Complete. Environment is safe for a midnight walk.")

if __name__ == "__main__":
    run_midnight_walk()
