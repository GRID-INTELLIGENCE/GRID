"""
The Resonance Chase Demo
========================
A standalone simulation demonstrating Grade Phase 5 Resonance components 
in action within a "Chase" scenario.
"""
import sys
import os
import time
import numpy as np

# Ensure we can import from src/
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), 'src')))

from application.resonance import (
    GravitationalSystem, GravitationalPoint, AttractionForce, EquilibriumState,
    ADSRParams, ArenaIntegration, Goal, Rule, MermaidDiagramGenerator,
    DatabricksBridge
)

def run_chase_simulation():
    print("--- 🌌 Initializing The Resonance Chase ---")
    
    # Check for Databricks Telemetry
    bridge = None
    if "--databricks" in sys.argv:
         print("🚀 Databricks Telemetry Enabled (Bridge Connecting...)")
         bridge = DatabricksBridge()
         # Start the bridge loop
         import asyncio
         try:
             loop = asyncio.get_event_loop()
         except RuntimeError:
             loop = asyncio.new_event_loop()
             asyncio.set_event_loop(loop)
         
         if loop.is_running():
             asyncio.run_coroutine_threadsafe(bridge.start(), loop)
         else:
             # In a script with no main loop, we might need a background thread for the loop
             # or just run it. For this demo, let's just start it in a thread.
             import threading
             def start_loop(loop):
                 asyncio.set_event_loop(loop)
                 loop.run_forever()
             
             t = threading.Thread(target=start_loop, args=(loop,), daemon=True)
             t.start()
             asyncio.run_coroutine_threadsafe(bridge.start(), loop)

    # 1. Setup Hunter and Prey
    hunter_pos = np.array([0.0, 0.0])
    prey_pos = np.array([5.0, 5.0])
    
    # 2. Setup Gravitational System (The Pursuit Engine)
    attraction = AttractionForce(strength=0.5)
    target_point = GravitationalPoint(prey_pos)
    gravity = GravitationalSystem(target_point, attraction)
    equilibrium = EquilibriumState(tolerance=0.1)
    
    # 3. Setup ADSR Envelopes (The Intensity Controller)
    # Define intensity phases for the chase
    intensity_config = ADSRParams(
        attack_time=2.0,    # 2 ticks to reach max intensity
        decay_time=1.0,     # 1 tick to stabilize
        sustain_level=1.0,  # Maintain full intensity
        release_time=2.0    # 2 ticks to wind down
    )
    
    # 4. Setup Arena Integration (The Reward Engine)
    goal = Goal(name="Catch the Prey", target_score=10.0)
    rules = [
        Rule(condition="distance < 1.0", action="REWARD", target="Proximity Bonus"),
        Rule(condition="distance < 0.2", action="REWARD", target="Capture Bonus")
    ]
    # Pass 'bridge' as 'vortex' argument (using older arg name for compatibility if not updated)
    # Checking ArenaIntegration definition, arg is 'vortex'.
    arena = ArenaIntegration(rules=rules, goal=goal, vortex=bridge)
    
    # 5. Simulation Loop
    ticks = 20  # Increased ticks to allow capture
    print(f"Hunter Start: {hunter_pos} | Prey Target: {prey_pos}")
    print("-" * 40)
    
    current_intensity = 0.0
    
    for tick in range(1, ticks + 1):
        # Calculate Distance
        p1_minus_p2 = prey_pos - hunter_pos
        distance = np.linalg.norm(p1_minus_p2)
        
        # Simple ADSR phase logic for demo
        if tick <= 4:
            phase = "ATTACK"
            current_intensity += 0.25
        elif tick <= 6:
            phase = "DECAY"
            current_intensity = 0.8
        elif tick <= 15:
            phase = "SUSTAIN"
            current_intensity = 1.0
        else:
            phase = "RELEASE"
            current_intensity -= 0.5
            current_intensity = max(0, current_intensity)
            
        # Modulate Gravity Strength by Phase Intensity
        # Increased multiplier for faster pursuit
        gravity.attraction_force.strength = current_intensity * 5.0
        
        # Apply Gravity
        hunter_pos = gravity.apply_gravity(hunter_pos)
        
        # Check Arena Rewards
        event_context = {"action": "MOVE", "distance": distance}
        arena.process_event(event_context)

        if distance < 1.0:
            status = "🎯 NEAR"
        if distance < 0.3:
             status = "🏆 CAPTURED"
        else:
            status = "🏃 CHASING"
            
        print(f"Tick {tick:02d} | [{phase:7}] | Dist: {distance:5.2f} | Pos: {hunter_pos} | {status}")
        
        if equilibrium.is_in_equilibrium(hunter_pos - prey_pos):
            print("--- ⚖️ Equilibrium Reached! ---")
            break
            
        time.sleep(0.05)

    print("-" * 40)
    print("--- 📊 Arena Summary ---")
    print(f"Total Score: {arena.reward_system.score}")
    print(f"Achievements: {arena.reward_system.achievements}")
    
    # 6. Generate Mermaid Diagram of the Logic
    generator = MermaidDiagramGenerator()
    diagram = generator.generate_flowchart(
        title="Resonance Pursuit Logic",
        nodes={
            "A": "Start Position",
            "B": "Gravity Calculation",
            "C": "ADSR Envelope Modulation",
            "D": "Arena Event Processing",
            "E": "Equilibrium Verification"
        },
        edges=[
            "A --> B",
            "B --> C",
            "C --> D",
            "D --> E",
            "E -- No --> B",
            "E -- Yes --> End[Finish]"
        ]
    )
    
    with open("resonance_chase_report.md", "w") as f:
        f.write("# Resonance Chase Report\n\n")
        f.write("Generated from Phase 5 Components Demonstration.\n\n")
        f.write("## Simulation Logic\n")
        f.write(f"```mermaid\n{diagram}\n```\n")
        f.write("\n## Arena Status\n")
        f.write(f"- Score: {arena.reward_system.score}\n")
        f.write(f"- Achievements: {', '.join(arena.reward_system.achievements)}\n")

    print("\n✅ Report generated: resonance_chase_report.md")

if __name__ == "__main__":
    try:
        # Simple CLI argument check
        if "--databricks" in sys.argv:
            print("🚀 Databricks Telemetry Enabled")
            # In a real app, this would toggle a config flag
            # For this demo, the Service automatically picks up env vars
            
        run_chase_simulation()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
