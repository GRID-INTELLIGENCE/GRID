import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from grid.libraries.performance_monitoring import PerformanceMonitor


async def verify_capabilities():
    print("🚀 Verifying 'Executable Now' Capabilities...")

    monitor = PerformanceMonitor()

    print("\n📊 1. System Metrics Collection:")
    metrics = await monitor.collect_system_metrics()
    for name, metric in metrics.items():
        print(f"  - {name}: {metric.value}{metric.unit} ({metric.status})")

    print("\n✅ Verification Complete!")

if __name__ == "__main__":
    asyncio.run(verify_capabilities())
