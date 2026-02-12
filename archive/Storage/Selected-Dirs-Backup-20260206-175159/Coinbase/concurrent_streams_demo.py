"""
Complementary Concurrent Stream Patterns with Thread Pooling
Models quantization-aware timing and synchronized intensity drops across threads
"""

import concurrent.futures
import threading
import queue
import time
import random
from dataclasses import dataclass, field
from typing import List, Callable, Optional, Dict
from enum import Enum, auto
import math


class StreamPhase(Enum):
    """Quantization states for stream processing"""
    BUILD = auto()      # Tension accumulation
    SUSTAIN = auto()   # Steady state
    DROP = auto()      # Event release
    RELEASE = auto()   # Decay phase


@dataclass
class EventPacket:
    """Quantized event with timing and intensity metadata"""
    timestamp: float
    intensity: float          # 0.0 to 1.0
    phase: StreamPhase
    stream_id: str
    data: any = None
    
    # Quantization grid position
    grid_position: float = field(default=0.0)  # 0.0-1.0 within measure
    
    def is_on_grid(self, tolerance: float = 0.05) -> bool:
        """Check if event falls on quantized grid point"""
        return abs(self.grid_position - round(self.grid_position * 4) / 4) < tolerance


class QuantizedThreadPool:
    """
    Thread pool with quantization-aware scheduling
    Complementary patterns: Producer/Consumer, Transformer/Aggregator
    """
    
    def __init__(self, max_workers: int = 4, bpm: float = 120.0, 
                 measure_beats: int = 4):
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="quantized"
        )
        self.bpm = bpm
        self.measure_beats = measure_beats
        self.beat_duration = 60.0 / bpm
        self.measure_duration = self.beat_duration * measure_beats
        
        # Stream coordination
        self._barrier = threading.Barrier(max_workers) if max_workers > 1 else None
        self._phase_lock = threading.RLock()
        self._current_phase = StreamPhase.BUILD
        self._intensity_curve = 0.0
        
        # Event queues for concurrent streams
        self._stream_queues: Dict[str, queue.Queue] = {}
        self._results: List[EventPacket] = []
        self._results_lock = threading.Lock()
        
    def get_grid_position(self) -> float:
        """Current position within measure (0.0-1.0)"""
        now = time.time()
        return (now % self.measure_duration) / self.measure_duration
    
    def get_phase(self) -> StreamPhase:
        """Determine current phase based on grid position and intensity"""
        pos = self.get_grid_position()
        with self._phase_lock:
            # Quantized phase transitions at grid boundaries
            if pos < 0.75:
                return StreamPhase.BUILD if self._intensity_curve < 0.8 else StreamPhase.SUSTAIN
            elif pos < 0.95:
                return StreamPhase.DROP
            else:
                return StreamPhase.RELEASE
    
    def _producer_pattern(self, stream_id: str, 
                         event_generator: Callable[[], any],
                         intensity_fn: Callable[[float], float]) -> None:
        """
        Complementary Pattern 1: Producer
        Generates events quantized to the grid
        """
        while not getattr(threading.current_thread(), '_stop_event', False):
            grid_pos = self.get_grid_position()
            phase = self.get_phase()
            
            # Calculate intensity based on position in curve
            intensity = intensity_fn(grid_pos)
            
            with self._phase_lock:
                self._intensity_curve = intensity
            
            # Only produce on quantized grid points (16th note resolution)
            if abs(grid_pos * 16 - round(grid_pos * 16)) < 0.02:
                packet = EventPacket(
                    timestamp=time.time(),
                    intensity=intensity,
                    phase=phase,
                    stream_id=stream_id,
                    data=event_generator(),
                    grid_position=grid_pos
                )
                
                if stream_id in self._stream_queues:
                    self._stream_queues[stream_id].put(packet)
                
                with self._results_lock:
                    self._results.append(packet)
            
            # Adaptive sleep based on intensity (higher = more responsive)
            sleep_time = self.beat_duration / 16 * (1.5 - intensity * 0.5)
            time.sleep(max(0.001, sleep_time))
    
    def _consumer_pattern(self, stream_id: str, 
                         process_fn: Callable[[EventPacket], any],
                         target_stream: str) -> None:
        """
        Complementary Pattern 2: Consumer
        Processes events from producer, transforms them
        """
        if target_stream not in self._stream_queues:
            self._stream_queues[target_stream] = queue.Queue()
        
        q = self._stream_queues[target_stream]
        
        while not getattr(threading.current_thread(), '_stop_event', False):
            try:
                packet = q.get(timeout=0.1)
                
                # Process with intensity-dependent transformation
                transformed = process_fn(packet)
                
                # Create new packet with transformed data
                new_packet = EventPacket(
                    timestamp=time.time(),
                    intensity=packet.intensity * 0.9,  # Slight attenuation
                    phase=packet.phase,
                    stream_id=stream_id,
                    data=transformed,
                    grid_position=self.get_grid_position()
                )
                
                with self._results_lock:
                    self._results.append(new_packet)
                    
            except queue.Empty:
                continue
    
    def _aggregator_pattern(self, stream_ids: List[str]) -> None:
        """
        Complementary Pattern 3: Aggregator
        Synchronizes multiple streams at drop points
        """
        while not getattr(threading.current_thread(), '_stop_event', False):
            phase = self.get_phase()
            
            # On DROP phase, synchronize and aggregate
            if phase == StreamPhase.DROP:
                aggregated = []
                
                for sid in stream_ids:
                    if sid in self._stream_queues:
                        # Drain queue for this moment
                        while not self._stream_queues[sid].empty():
                            try:
                                packet = self._stream_queues[sid].get_nowait()
                                aggregated.append(packet)
                            except queue.Empty:
                                break
                
                if aggregated:
                    # Calculate synchronized intensity
                    max_intensity = max(p.intensity for p in aggregated)
                    
                    sync_packet = EventPacket(
                        timestamp=time.time(),
                        intensity=max_intensity,
                        phase=StreamPhase.DROP,
                        stream_id="aggregate",
                        data={
                            "packets": aggregated,
                            "count": len(aggregated),
                            "sync_point": self.get_grid_position()
                        },
                        grid_position=self.get_grid_position()
                    )
                    
                    with self._results_lock:
                        self._results.append(sync_packet)
                        
                        # Clear old results to prevent memory bloat
                        if len(self._results) > 1000:
                            self._results = self._results[-500:]
                
                # Wait for next measure
                time.sleep(self.measure_duration * 0.1)
            else:
                time.sleep(self.beat_duration / 4)
    
    def _modulator_pattern(self, stream_id: str, 
                          base_stream: str,
                          modulation_fn: Callable[[EventPacket, float], any]) -> None:
        """
        Complementary Pattern 4: Modulator
        Applies intensity-curve modulation to base stream
        """
        if base_stream not in self._stream_queues:
            self._stream_queues[base_stream] = queue.Queue()
        
        q = self._stream_queues[base_stream]
        
        while not getattr(threading.current_thread(), '_stop_event', False):
            try:
                packet = q.get(timeout=0.05)
                
                # Apply modulation based on current intensity curve
                with self._phase_lock:
                    curve_value = self._intensity_curve
                
                modulated = modulation_fn(packet, curve_value)
                
                new_packet = EventPacket(
                    timestamp=time.time(),
                    intensity=packet.intensity * (0.5 + curve_value),
                    phase=packet.phase,
                    stream_id=stream_id,
                    data=modulated,
                    grid_position=packet.grid_position
                )
                
                if stream_id not in self._stream_queues:
                    self._stream_queues[stream_id] = queue.Queue()
                self._stream_queues[stream_id].put(new_packet)
                
            except queue.Empty:
                continue
    
    def launch_complementary_streams(self, duration_seconds: float = 10.0) -> List[EventPacket]:
        """
        Launch all complementary patterns concurrently
        """
        self._stream_queues = {
            "primary": queue.Queue(),
            "secondary": queue.Queue(),
            "tertiary": queue.Queue()
        }
        
        futures = []
        
        # Producer streams (complementary timing offsets)
        futures.append(self.executor.submit(
            self._producer_pattern,
            "primary",
            lambda: random.gauss(0, 1),  # White noise source
            lambda pos: 0.2 + 0.8 * (pos / 0.75) if pos < 0.75 else 1.0  # Build curve
        ))
        
        futures.append(self.executor.submit(
            self._producer_pattern,
            "secondary",
            lambda: random.random() > 0.5,  # Binary events
            lambda pos: math.sin(pos * math.pi * 4) * 0.5 + 0.5  # Oscillating
        ))
        
        # Consumer streams (process producers)
        futures.append(self.executor.submit(
            self._consumer_pattern,
            "primary_processed",
            lambda p: p.data * 2 if isinstance(p.data, (int, float)) else p.data,
            "primary"
        ))
        
        # Modulator stream
        futures.append(self.executor.submit(
            self._modulator_pattern,
            "modulated",
            "secondary",
            lambda p, curve: {"original": p.data, "curve": curve, 
                            "modulated": p.data and curve > 0.5}
        ))
        
        # Aggregator (synchronizes at drop points)
        futures.append(self.executor.submit(
            self._aggregator_pattern,
            ["primary", "secondary", "primary_processed", "modulated"]
        ))
        
        # Let it run
        time.sleep(duration_seconds)
        
        # Signal shutdown
        for f in futures:
            f.cancel()
        
        self.executor.shutdown(wait=False)
        
        return self._results


class AdaptiveDropScheduler:
    """
    Schedules synchronized drops across multiple concurrent streams
    with quantization-aware timing
    """
    
    def __init__(self, pool: QuantizedThreadPool):
        self.pool = pool
        self._drop_callbacks: List[Callable[[float, List[EventPacket]], None]] = []
        self._scheduled_drops: List[float] = []
        
    def on_drop(self, callback: Callable[[float, List[EventPacket]], None]):
        """Register callback for drop events"""
        self._drop_callbacks.append(callback)
        
    def schedule_quantized_drop(self, measure_number: int, 
                                 beat_position: float = 0.75) -> None:
        """
        Schedule a drop at specific quantized position
        measure_number: which measure (0-indexed)
        beat_position: within measure (0.0-1.0, default 0.75 = 3rd beat)
        """
        drop_time = measure_number * self.pool.measure_duration + \
                    beat_position * self.pool.measure_duration
        self._scheduled_drops.append(drop_time)
    
    def check_and_trigger(self, current_results: List[EventPacket]) -> None:
        """Check if any drops should trigger based on current state"""
        current_phase = self.pool.get_phase()
        
        if current_phase == StreamPhase.DROP:
            # Find packets at this moment
            recent = [r for r in current_results 
                     if time.time() - r.timestamp < 0.1]
            
            for callback in self._drop_callbacks:
                callback(self.pool.get_grid_position(), recent)


def demo_complementary_streams():
    """Demonstrate concurrent complementary patterns"""
    
    print("=" * 60)
    print("CONCURRENT STREAM PATTERNS WITH QUANTIZED THREAD POOL")
    print("=" * 60)
    
    # Initialize pool at 140 BPM, 4/4 time
    pool = QuantizedThreadPool(max_workers=6, bpm=140.0, measure_beats=4)
    scheduler = AdaptiveDropScheduler(pool)
    
    drop_count = [0]
    
    def on_drop(grid_pos: float, packets: List[EventPacket]):
        drop_count[0] += 1
        intensities = [p.intensity for p in packets]
        avg_intensity = sum(intensities) / len(intensities) if intensities else 0
        
        print(f"\n[DROP #{drop_count[0]} @ grid={grid_pos:.3f}]")
        print(f"  Intensity: {avg_intensity:.3f}")
        print(f"  Packets synchronized: {len(packets)}")
        print(f"  Streams: {set(p.stream_id for p in packets)}")
    
    scheduler.on_drop(on_drop)
    
    print(f"\nLaunching complementary streams...")
    print(f"BPM: {pool.bpm}, Measure: {pool.measure_beats} beats")
    print(f"Grid resolution: 16th notes")
    print(f"Duration: 8 seconds\n")
    
    # Run the system
    results = pool.launch_complementary_streams(duration_seconds=8.0)
    
    print(f"\n{'=' * 60}")
    print(f"RESULTS SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total events generated: {len(results)}")
    print(f"Drops triggered: {drop_count[0]}")
    
    # Analyze by stream
    by_stream = {}
    for r in results:
        by_stream.setdefault(r.stream_id, []).append(r)
    
    print(f"\nEvents per stream:")
    for stream_id, packets in sorted(by_stream.items()):
        avg_intensity = sum(p.intensity for p in packets) / len(packets)
        on_grid = sum(1 for p in packets if p.is_on_grid())
        print(f"  {stream_id:20s}: {len(packets):4d} events, "
              f"avg intensity={avg_intensity:.3f}, on-grid={on_grid}")
    
    # Phase distribution
    by_phase = {}
    for r in results:
        by_phase.setdefault(r.phase.name, 0)
        by_phase[r.phase.name] += 1
    
    print(f"\nPhase distribution:")
    for phase, count in sorted(by_phase.items()):
        print(f"  {phase:10s}: {count} events")
    
    return results


if __name__ == "__main__":
    demo_complementary_streams()
