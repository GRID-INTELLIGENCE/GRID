# MYCELIUM — Accessibility-First Data Store

> *"Before words existed, meaning still moved."*

---

## Part I: Research Synthesis

### Two Ancient Communication Systems

Research from National Geographic, The Guardian, Bioneers (Suzanne Simard), and Wikipedia on mycorrhizal networks reveals two primordial communication architectures that predate human language by tens of thousands (or millions) of years.

---

### Chunked Research Table

| Dimension | Early Humans (30,000+ yrs ago) | Fungal Networks (400M+ yrs old) |
|-----------|-------------------------------|--------------------------------|
| **Medium** | Gesture, ochre marks on rock | Chemical signals through hyphae threads |
| **Vocabulary** | 26 recurring symbols across 200+ caves | 3 signal types: nutrients, defense chemicals, allelochemicals |
| **Grammar** | Symbol clusters repeat in patterns (e.g. "II ^ III X II") | Transfer direction + quantity = context |
| **Context** | Same gesture = different meaning depending on situation | Same network = mutualistic OR parasitic depending on need |
| **Hub Nodes** | Elders, skilled hunters (knowledge carriers) | "Mother Trees" — most connected, most giving |
| **Broadcast** | Cave walls = persistent shared memory | Chemical defense alerts propagate to neighbors |
| **Adaptation** | Truncated animal drawings evolved into abstract symbols | Shaded trees receive more carbon; stressed trees get priority |
| **Multimodal** | Gesture + call + expression combined = richer signal | Carbon + nitrogen + water + infochemicals = compound message |
| **Cultural Drift** | Chimps vs bonobos have different gesture "dialects" | Different forest types use different mycorrhizal strategies |
| **Persistence** | Symbols on cave walls last 30,000 years | Mycelium networks persist across tree generations |
| **Speed** | Instant (visual/gestural) | Minutes to hours (chemical transfer) |
| **Redundancy** | Same 5-symbol sequence found on necklace AND walls | 90% of land plants share the same network type |
| **Failure Mode** | Meaning lost if context unknown | Network degrades when "mother trees" removed (clear-cutting) |
| **Scale** | Trade networks carried symbols across Spain→France | Thousands of km of threads per square meter |
| **Core Principle** | **Meaning before syntax** | **Resource flow follows need** |

---

### Key Insight Extraction

| Principle | What It Means | Tool Design Implication |
|-----------|--------------|------------------------|
| **Meaning > Syntax** | Cavemen conveyed ideas with imperfect symbols. Grammar came later. | API should work even with incomplete/messy input. Forgive, don't reject. |
| **Context = Meaning** | Same gesture meant different things in different situations. | Operations should be context-aware. Same key, different behavior based on use pattern. |
| **Hub Architecture** | Mother Trees share the most, connect the most, survive the longest. | Design around "hub" data patterns — hot keys get priority treatment. |
| **Need-Based Flow** | Stressed trees get more resources automatically. | Auto-scaling priority — high-demand keys get more cache, faster access. |
| **Compound Signals** | Gesture + sound + expression = richer than any single channel. | Data entries carry metadata + TTL + priority + type = richer than plain key-value. |
| **Persistent Memory** | Cave walls = durable shared state. Gestures = ephemeral. | Two tiers: persistent (wall) and ephemeral (gesture). User chooses naturally. |
| **Graceful Degradation** | Networks adapt when nodes die. Gestures still work without symbols. | Always fall back gracefully. No Redis? Memory works. No network? Local works. |

---

## Part II: GRID Codebase Pattern Mapping

### Existing Patterns That Inform This Tool

| GRID Pattern | Source File | What It Does | Mycelium Analog |
|-------------|------------|-------------|-----------------|
| `CacheInterface` | `src/grid/infrastructure/cache.py` | Abstract get/set/delete/clear with TTL | Nutrient exchange interface |
| `MemoryCache` | `src/grid/infrastructure/cache.py` | In-memory dict + async locks + TTL | Local root storage |
| `CacheFactory` | `src/grid/infrastructure/cache.py` | Backend selection (memory/redis/sqlite) | Network type selection |
| `QueryCache` | `src/tools/rag/cache.py` | LRU + TTL + context hash for staleness | Adaptive resource allocation |
| `EventBus` | `src/grid/agentic/event_bus.py` | Redis pub/sub with in-memory fallback | Chemical signal broadcast |
| `UnifiedFabric` | `src/unified_fabric/__init__.py` | Domain-aware routing + event priority | Hyphae routing by domain |
| `PatternRecognizer` | `src/cognitive/patterns/recognition.py` | Recognize → Analyze → Recommend | Sense → Process → Respond |
| `CoffeeMode` | `src/cognitive/patterns/recognition.py` | Adaptive complexity (Espresso/Americano/Cold Brew) | Adaptive resource depth |
| `PatternDetection` | `src/cognitive/patterns/recognition.py` | Confidence scoring + explanation generation | Signal strength + context |

---

## Part III: MYCELIUM Tool Design

### Name: **MYCELIUM**
**M**emory **Y**ielding **C**ontextual **E**fficiency for **L**ightweight **I**nteractive **U**se and **M**anagement

### Philosophy

> Like mycelium threads beneath a forest floor, or symbols painted on cave walls —
> the best communication systems are **simple to use, rich in meaning, and adapt to need**.

### Core Design Principles

1. **Meaning Before Syntax** — Forgiving API. Works with incomplete input. Infers intent.
2. **Context Is King** — Same operation behaves differently based on detected use pattern.
3. **Hub Priority** — Hot data gets automatic priority. Cold data gracefully evicts.
4. **Need-Based Flow** — Resources flow where demand is highest. No manual tuning required.
5. **Compound Signals** — Every entry is richer than a plain key-value. Metadata is native.
6. **Two-Tier Memory** — Ephemeral (gesture) and Persistent (cave wall) modes coexist.
7. **Graceful Fallback** — Always works. Network down? Local mode. Redis gone? Memory mode.

---

### Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                    MYCELIUM                           │
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │   Gesture    │  │   Wall      │  │   Signal     │ │
│  │   Layer      │  │   Layer     │  │   Layer      │ │
│  │  (ephemeral) │  │ (persistent)│  │  (pub/sub)   │ │
│  │             │  │             │  │              │ │
│  │  in-memory   │  │  SQLite/    │  │  event bus   │ │
│  │  dict + TTL  │  │  file/Redis │  │  + channels  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬───────┘ │
│         │                │                │          │
│  ┌──────┴────────────────┴────────────────┴───────┐  │
│  │              Hyphae Router                      │  │
│  │   (context-aware routing + adaptive priority)   │  │
│  └──────────────────┬─────────────────────────────┘  │
│                     │                                │
│  ┌──────────────────┴─────────────────────────────┐  │
│  │           Mother Tree (Hub Manager)             │  │
│  │   (hot-key detection, load balancing, stats)    │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │           Coffee Mode Adapter                   │  │
│  │   Espresso: minimal, fast, tiny footprint       │  │
│  │   Americano: balanced, standard features        │  │
│  │   Cold Brew: full persistence, analytics, logs  │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

---

### Module Skeleton

#### 1. `mycelium/core.py` — The Root Interface

```python
"""
MYCELIUM Core — Like cave symbols: simple marks, rich meaning.

Forgiving API. Works with messy input. Adapts to context.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class Depth(StrEnum):
    """How deep to go. Borrowed from GRID's Coffee House."""
    ESPRESSO = "espresso"      # fast, minimal, in-memory only
    AMERICANO = "americano"    # balanced, local persistence
    COLD_BREW = "cold_brew"    # full features, distributed


class SignalType(StrEnum):
    """What kind of data. Like mycelium's 3 chemical types."""
    NUTRIENT = "nutrient"      # regular data (cache, session, config)
    DEFENSE = "defense"        # alerts, rate limits, circuit breakers
    GROWTH = "growth"          # analytics, counters, time-series


@dataclass
class Spore:
    """A single data entry. Richer than key-value. Like a compound signal."""
    key: str
    value: Any
    signal_type: SignalType = SignalType.NUTRIENT
    ttl: int | None = None                          # seconds, None = permanent
    priority: int = 1                                # 0=low, 1=normal, 2=high, 3=critical
    tags: list[str] = field(default_factory=list)    # for grouping and querying
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    access_count: int = 0                            # auto-tracked hub detection
    metadata: dict[str, Any] = field(default_factory=dict)


class MyceliumInterface(ABC):
    """Root interface. Like CacheInterface in GRID but richer."""

    @abstractmethod
    async def plant(self, key: str, value: Any, **opts) -> Spore:
        """Store something. Like planting a seed."""
        ...

    @abstractmethod
    async def harvest(self, key: str) -> Any | None:
        """Get something. Like harvesting a resource."""
        ...

    @abstractmethod
    async def signal(self, channel: str, message: Any) -> None:
        """Broadcast to listeners. Like chemical defense alerts."""
        ...

    @abstractmethod
    async def listen(self, channel: str, callback) -> None:
        """Subscribe to signals. Like root receptors."""
        ...

    @abstractmethod
    async def count(self, key: str, delta: int = 1) -> int:
        """Increment a counter. For analytics/rate-limiting."""
        ...

    @abstractmethod
    async def nearby(self, key: str, radius: float) -> list[Spore]:
        """Find related entries. Geospatial or tag-based proximity."""
        ...
```

#### 2. `mycelium/gesture.py` — Ephemeral Layer

```python
"""
Gesture Layer — Like hand signals between hunter-gatherers.
Fast, ephemeral, in-memory. Gone when the moment passes.

Maps to Redis use cases: session cache, API response cache, temp state.
"""

class GestureStore:
    """In-memory store with TTL, LRU eviction, and hub detection."""

    def __init__(self, max_size: int = 10_000):
        self._store: dict[str, Spore] = {}
        self._max_size = max_size

    async def plant(self, key, value, ttl=300, **opts) -> Spore: ...
    async def harvest(self, key) -> Any | None: ...
    async def _evict_coldest(self) -> None:
        """Remove least-accessed entry. Hub keys survive longer."""
        ...
    async def _promote_hub(self, spore: Spore) -> None:
        """If access_count crosses threshold, extend TTL automatically."""
        ...
```

#### 3. `mycelium/wall.py` — Persistent Layer

```python
"""
Wall Layer — Like symbols painted on cave walls.
Durable. Survives restarts. Shared across sessions.

Maps to Redis use cases: persistent sessions, leaderboards, config.
"""

class WallStore:
    """SQLite-backed persistent store. Zero config required."""

    def __init__(self, path: str = ".mycelium/wall.db"):
        ...
    async def plant(self, key, value, **opts) -> Spore: ...
    async def harvest(self, key) -> Any | None: ...
    async def query_by_tags(self, tags: list[str]) -> list[Spore]: ...
    async def time_series(self, key_prefix: str, since: datetime) -> list[Spore]: ...
```

#### 4. `mycelium/signal.py` — Pub/Sub Layer

```python
"""
Signal Layer — Like chemical alerts through mycelium threads.
Broadcast messages. Subscribe to channels. Real-time events.

Maps to Redis use cases: event streaming, task queues, notifications.
"""

class SignalBus:
    """Event bus with channel routing. In-memory default, Redis optional."""

    def __init__(self, use_network: bool = False):
        self._channels: dict[str, list[Callable]] = {}
        self._history: deque = deque(maxlen=1000)

    async def signal(self, channel, message) -> None: ...
    async def listen(self, channel, callback) -> None: ...
    async def replay(self, channel, since: datetime) -> list: ...
```

#### 5. `mycelium/hyphae.py` — Context-Aware Router

```python
"""
Hyphae Router — Like fungal threads that route nutrients where needed.

Decides: gesture (ephemeral) or wall (persistent)?
Detects: hot keys (hub nodes) and auto-promotes them.
Adapts: Coffee Mode changes behavior depth.
"""

class HyphaeRouter:
    """Routes operations to the right layer based on context."""

    def __init__(self, depth: Depth = Depth.AMERICANO):
        self.gesture = GestureStore()
        self.wall = WallStore() if depth != Depth.ESPRESSO else None
        self.signal_bus = SignalBus()
        self.depth = depth

    async def plant(self, key, value, **opts) -> Spore:
        """Auto-route: short TTL → gesture. No TTL → wall. Has channel → signal."""
        ...

    async def harvest(self, key) -> Any | None:
        """Check gesture first (fast), then wall (durable). Like cache-aside."""
        ...
```

#### 6. `mycelium/mother_tree.py` — Hub Manager & Analytics

```python
"""
Mother Tree — The most connected node in the network.

Tracks access patterns. Detects hot keys. Manages health.
Provides simple analytics without external dependencies.

Maps to Redis use cases: rate limiting, counters, leaderboards, analytics.
"""

class MotherTree:
    """Hub manager inspired by GRID's PatternRecognizer triad."""

    async def detect_hubs(self) -> list[str]:
        """Find hot keys (high access_count). Like mother trees in a forest."""
        ...

    async def rate_limit(self, key: str, max_per_window: int, window_secs: int) -> bool:
        """Simple rate limiting. Returns True if allowed, False if throttled."""
        ...

    async def leaderboard(self, prefix: str, top_n: int = 10) -> list[tuple[str, float]]:
        """Sorted ranking. Like sorted sets but simpler."""
        ...

    async def counter(self, key: str, delta: int = 1) -> int:
        """Atomic increment. For real-time analytics."""
        ...

    async def health(self) -> dict:
        """Network health: memory usage, hit rates, hub distribution."""
        ...
```

#### 7. `mycelium/adapt.py` — Coffee Mode Adapter

```python
"""
Coffee Mode Adapter — Borrowed from GRID's Flow Pattern.

Dynamically adjusts tool behavior based on detected load and environment.
  Espresso:   Minimal. In-memory only. Zero dependencies. Starts in <1ms.
  Americano:  Balanced. Local SQLite persistence. No network needed.
  Cold Brew:  Full. Redis/network backend. Distributed. All features.
"""

class CoffeeModeAdapter:
    """Auto-detects appropriate depth, or user sets it explicitly."""

    @staticmethod
    def detect() -> Depth:
        """Sense environment. No Redis? → Americano. No disk? → Espresso."""
        ...

    @staticmethod
    def explain(depth: Depth) -> str:
        """Plain-language explanation of current mode. No jargon."""
        ...
```

---

### Use Case Mapping

| Redis Use Case | Mycelium Equivalent | How It Works (Plain Language) |
|---------------|--------------------|-----------------------------|
| **Cache API response** | `plant("api:/users", data, ttl=60)` | Store it. It disappears in 60 seconds. |
| **Session storage** | `plant("session:abc", user, ttl=3600)` | Remember this user for 1 hour. |
| **Rate limiting** | `mother.rate_limit("ip:1.2.3.4", 100, 60)` | Allow 100 requests per minute. True/False. |
| **Counter** | `mother.counter("page:views")` | Add 1. Get new total. That's it. |
| **Leaderboard** | `mother.leaderboard("scores", top_n=10)` | Top 10 scores. Sorted. Done. |
| **Pub/Sub** | `signal("orders", new_order)` | Shout it. Everyone listening hears it. |
| **Task queue** | `signal("tasks", job)` + worker `listen("tasks", do_job)` | Post a job. A worker picks it up. |
| **Geospatial** | `plant("cafe:1", loc, tags=["geo:40.7,-74.0"])` + `nearby(...)` | Store with location. Find what's close. |
| **Time series** | `plant("temp:2026-02-24T11:00", 22.5, signal_type=GROWTH)` | Store timestamped data. Query ranges later. |
| **Config store** | `plant("config:theme", "dark")` (no TTL = permanent) | Store it forever. Survives restart. |

---

### Getting Started (3 Lines)

```python
from mycelium import Mycelium

m = Mycelium()                              # auto-detects best mode
await m.plant("greeting", "hello world")    # store
print(await m.harvest("greeting"))          # retrieve → "hello world"
```

### Explaining Complex Concepts Simply

Following the cave-symbol principle — **meaning before syntax** — Mycelium explains itself:

```python
m.explain("cache")
# → "You give it a name and a thing. It remembers for a while. Then forgets."

m.explain("pubsub")
# → "You shout into a channel. Anyone listening hears it. Nobody listening? Gone."

m.explain("rate_limit")
# → "You set a speed limit. Too many requests? Blocked. Simple."

m.explain("leaderboard")
# → "Numbers go in. Biggest ones float to the top. You pick how many to see."
```

---

### Comparison: Redis vs Mycelium

| Aspect | Redis | Mycelium |
|--------|-------|----------|
| **Setup** | Install binary, configure, start server | `pip install mycelium` → done |
| **Dependencies** | External server process | Zero (in-memory default) |
| **Learning curve** | Moderate (commands, data types, config) | Minimal (plant/harvest/signal) |
| **Data model** | 15+ data types to learn | 1 type: `Spore` (carries everything) |
| **Persistence** | RDB/AOF config needed | Auto (SQLite, zero config) |
| **Pub/Sub** | Separate commands, delivery semantics | `signal()` / `listen()` |
| **Rate limiting** | DIY with Lua scripts or modules | `rate_limit(key, max, window)` |
| **Scaling** | Cluster/Sentinel config | Coffee Mode auto-adapts |
| **Failure mode** | Server down = app breaks | Graceful fallback to simpler mode |
| **Explanation** | Technical docs (500+ commands) | `m.explain("anything")` |

---

## Part IV: What Makes This Different

### Borrowed From Nature, Built From Code

| Source | Contribution | Where It Lives |
|--------|-------------|---------------|
| **Cave Symbols** | Forgiving input, meaning > syntax, persistent shared memory | API design, Wall layer, explain() |
| **Gesture Communication** | Ephemeral by default, context-dependent, multimodal | Gesture layer, context routing |
| **Mycelium Networks** | Hub priority, need-based flow, chemical signaling | Mother Tree, Hyphae Router, Signal Bus |
| **Mother Trees** | Most-connected nodes share most, survive longest | Hub detection, hot-key auto-promotion |
| **GRID CoffeeMode** | Adaptive depth based on cognitive load | Coffee Mode Adapter (Espresso/Americano/Cold Brew) |
| **GRID PatternRecognizer** | Recognize → Analyze → Recommend triad | Hub detection → Stats → Auto-optimize |
| **GRID CacheInterface** | Abstract storage with TTL | MyceliumInterface base class |
| **GRID EventBus** | Redis pub/sub with in-memory fallback | Signal layer with graceful degradation |
| **GRID UnifiedFabric** | Domain-aware routing, event priority | Hyphae Router with context-aware dispatch |
| **GRID QueryCache** | LRU + TTL + staleness detection | Gesture layer eviction strategy |

---

## Part V: Open Research Questions

These elements are present in the design but not yet fully explainable — they mirror patterns in nature and GRID that warrant deeper scientific investigation:

1. **Hub Emergence** — Why do some keys naturally become "mother trees"? Can we predict this?
2. **Network Resilience** — Mycelium networks survive losing individual nodes. How to replicate this property in distributed caching without complex consensus protocols?
3. **Chemical Gradient Routing** — Mycelium routes nutrients along concentration gradients. Can data priority work the same way — flowing toward "need" rather than being explicitly routed?
4. **Symbol Compression** — Cave artists reduced entire animals to single wavy lines. What's the equivalent compression for data access patterns? Can we auto-detect when a complex query reduces to a simpler one?
5. **Gestural Ambiguity as Feature** — Same gesture, different meaning based on context. Traditional databases treat ambiguity as error. What if the tool embraced it — same key resolves differently based on caller context?
6. **Temporal Resonance** — GRID's Time pattern uses audio-engineering Q-factors for temporal matching. Can cache TTLs be set dynamically based on temporal resonance with access patterns rather than fixed durations?

---

## Sources

### Early Human Communication
- **National Geographic** — "Chimps show that actions spoke louder than words in language evolution" (Pollick & de Waal, Emory University, PNAS 2007)
- **The Guardian** — "Did Stone Age cavemen talk to each other in symbols?" (Genevieve von Petzinger, University of Victoria — database of 26 symbols across 200+ caves, 30,000+ years old)

### Fungal Networks
- **Bioneers** — "The Wood Wide Web: The Intelligent Underground Mycelial Network" (Suzanne Simard, University of British Columbia — Mother Tree Project)
- **Wikipedia** — "Mycorrhizal network" (comprehensive survey of CMN research, signal types, and inter-plant communication mechanisms)

### GRID Codebase
- `src/grid/infrastructure/cache.py` — CacheInterface, MemoryCache, CacheFactory
- `src/tools/rag/cache.py` — QueryCache (LRU + TTL + context hashing)
- `src/grid/agentic/event_bus.py` — EventBus (Redis pub/sub + in-memory fallback)
- `src/unified_fabric/__init__.py` — UnifiedFabric (domain routing, event priority)
- `src/cognitive/patterns/recognition.py` — PatternRecognizer, CoffeeMode, PatternDetection
- `src/cognitive/scaffolding_engine.py` — ScaffoldingEngine (dynamic content adaptation, 11 strategies)
- `src/cognitive/patterns/explanations.py` — PatternExplanation (human-readable pattern descriptions)
- `src/cognitive/router.py` — CognitiveRouter (expertise-aware routing, load-based adaptations)

---

## Part VI: Assistive Cognitive Augmentation Layer

> *Geometry is universal — the language of space, time, and relationship.*
> *Meaning emerges from resonance, not just logic.*

### The Substrate: Why Geometry Works for Accessibility

GRID's 9 cognitive patterns are geometric at their core — symmetry, fractals, resonance, rhythm. These aren't arbitrary metaphors. They map to how brains actually process information:

- **Symmetry** → Logical consistency ("If A = B, then B = A") — reduces cognitive load by establishing predictable rules
- **Fractals** → Recursive decomposition ("Break the big thing into small same-shaped things") — makes complex systems approachable
- **Resonance** → Alignment detection ("Does this click with what you already know?") — leverages existing mental models
- **Rhythm** → Temporal predictability ("What comes next?") — reduces anxiety and builds momentum

For users with cognitive disabilities, neurodivergence, or learning differences, these geometric primitives are **more accessible than language** — they're closer to the cave-symbol principle of meaning-before-syntax.

### GRID Patterns That Ground This Layer

| GRID Component | Source | Role in Assistive Layer |
|---------------|--------|------------------------|
| `ScaffoldingEngine` | `src/cognitive/scaffolding_engine.py` | Dynamic content simplification based on load + expertise |
| `ScaffoldingStrategy` | `src/cognitive/scaffolding_engine.py` | 11 strategies: chunking, progressive disclosure, hints, examples, step-by-step, etc. |
| `PatternExplanation` | `src/cognitive/patterns/explanations.py` | Human-readable: short_description, full_explanation, when_applies, what_to_do, benefits |
| `CognitiveRouter` | `src/cognitive/router.py` | Routes by expertise (NOVICE→EXPERT), load (LIGHT→HEAVY), mode (FAST→DELIBERATE) |
| `CoffeeMode` | `src/cognitive/patterns/recognition.py` | Adaptive depth: Espresso (minimal), Americano (balanced), Cold Brew (full) |
| `PatternRecognizer` | `src/cognitive/patterns/recognition.py` | Recognize → Analyze → Recommend triad for each pattern |

### Module: `mycelium/navigator.py` — Pattern Navigator

The Pattern Navigator lets users explore data concepts through cognitive patterns interactively.

```python
"""
Pattern Navigator — Explore concepts through geometric resonance.

Like how cave artists reduced a horse to a single wavy line,
the Navigator reduces complex data concepts to their geometric essence.

Grounded in GRID's PatternExplanation and ScaffoldingEngine.
"""

from dataclasses import dataclass
from enum import StrEnum


class ResonanceLevel(StrEnum):
    """How well an explanation 'clicks' with the user."""
    SILENT = "silent"        # didn't land — try different pattern
    HUM = "hum"              # partial — refine
    RING = "ring"            # clear resonance — keep going


@dataclass
class PatternLens:
    """A way of seeing a concept through a specific cognitive pattern."""
    pattern: str             # flow, spatial, rhythm, color, etc.
    analogy: str             # the geometric analogy
    eli5: str                # explain like I'm 5
    visual_hint: str         # what to picture
    when_useful: str         # when this lens helps most


class PatternNavigator:
    """Interactive concept explorer using GRID's 9 patterns as lenses."""

    # Each Redis-like concept mapped to multiple pattern lenses
    CONCEPT_LENSES: dict[str, list[PatternLens]] = {
        "cache": [
            PatternLens(
                pattern="flow",
                analogy="A river with pools — fast water flows past, pools hold what you need nearby.",
                eli5="A shelf next to you with stuff you use a lot. Saves walking to the warehouse.",
                visual_hint="Picture a river. The pools are your cache. Water is data flowing through.",
                when_useful="When you keep asking for the same thing and it's slow to get.",
            ),
            PatternLens(
                pattern="rhythm",
                analogy="A heartbeat — regular pulses of checking and refreshing.",
                eli5="Like checking your fridge. You know milk expires, so you check before using it.",
                visual_hint="Picture a clock ticking. Each tick = check if data is still fresh.",
                when_useful="When data changes on a schedule and you need to stay current.",
            ),
        ],
        "pubsub": [
            PatternLens(
                pattern="spatial",
                analogy="A town square — shout in the middle, everyone nearby hears.",
                eli5="A group chat. You post once. Everyone in the group sees it.",
                visual_hint="Picture a megaphone in a room. Walls are channels. Rooms are topics.",
                when_useful="When many parts of your app need to react to the same event.",
            ),
            PatternLens(
                pattern="cause",
                analogy="Dominoes — one falls, the next reacts, chain continues.",
                eli5="You flip a switch. The light turns on. That's pub/sub.",
                visual_hint="Picture dominoes falling in a line. Each domino is a subscriber.",
                when_useful="When action A should always trigger reactions B, C, D.",
            ),
        ],
        "rate_limit": [
            PatternLens(
                pattern="rhythm",
                analogy="A metronome — only one beat per interval, no rushing.",
                eli5="A water fountain. It only gives a sip at a time. Can't flood it.",
                visual_hint="Picture a turnstile. One person through per second. No exceptions.",
                when_useful="When too many requests at once would break something.",
            ),
        ],
        "leaderboard": [
            PatternLens(
                pattern="deviation",
                analogy="The tallest tree stands out from the forest canopy.",
                eli5="A race. First place is the one furthest ahead. Simple.",
                visual_hint="Picture trees of different heights. You can see the tallest instantly.",
                when_useful="When you need to rank things and show the top ones.",
            ),
        ],
        "time_series": [
            PatternLens(
                pattern="time",
                analogy="Tree rings — each ring records a moment, together they tell a story.",
                eli5="A diary. One entry per day. You can read back and see what happened.",
                visual_hint="Picture tree rings. Wider rings = good years. Narrow = stress.",
                when_useful="When you want to track how something changes over time.",
            ),
        ],
    }

    def explore(self, concept: str, preferred_pattern: str | None = None) -> PatternLens | None:
        """Show a concept through a pattern lens. User picks which resonates."""
        ...

    def try_different(self, concept: str, feedback: ResonanceLevel) -> PatternLens | None:
        """User says 'didn't click' → try a different pattern lens."""
        ...

    def simplify(self, concept: str) -> str:
        """ELI5 mode. Always available. Returns the simplest explanation."""
        ...
```

---

## Part VII: Accessibility & Inclusive Design

### Design Principle: Perceivable, Operable, Navigable, Understandable

Mycelium's interface adapts to the user — not the other way around.

### Module: `mycelium/sensory.py` — Sensory Mode

```python
"""
Sensory Mode — Adaptive interface for sensory, motor, and cognitive needs.

Inspired by:
- GRID's CognitiveRouter (NOVICE→EXPERT, LIGHT→HEAVY routing)
- GRID's ScaffoldingEngine (progressive disclosure, simplification)
- Mycelium's Mother Tree principle (network adapts to stressed nodes)
"""

from dataclasses import dataclass, field
from enum import StrEnum


class SensoryProfile(StrEnum):
    """Predefined sensory profiles. User picks one, or system detects."""
    DEFAULT = "default"          # standard interface
    LOW_VISION = "low_vision"    # high contrast, large text, screen reader optimized
    MOTOR = "motor"              # voice-first, minimal clicks, large targets
    COGNITIVE = "cognitive"      # reduced clutter, step-by-step, slower pace
    FOCUS = "focus"              # minimal distractions, single-task view
    CALM = "calm"                # grayscale, soft transitions, no animations


@dataclass
class SensoryAdaptation:
    """A single adaptation applied to the interface."""
    what: str                    # e.g. "increase_font_size"
    why: str                     # e.g. "Low vision profile active"
    reversible: bool = True      # user can always undo


@dataclass
class SensoryState:
    """Current sensory configuration."""
    profile: SensoryProfile = SensoryProfile.DEFAULT
    adaptations: list[SensoryAdaptation] = field(default_factory=list)
    text_scale: float = 1.0      # 1.0 = normal, 2.0 = double
    contrast: str = "normal"     # normal, high, inverted
    motion: str = "normal"       # normal, reduced, none
    audio_cues: bool = False     # auditory feedback for actions
    speech_rate: float = 1.0     # text-to-speech speed multiplier


class SensoryMode:
    """Manages sensory adaptations. No data stored without consent."""

    def apply_profile(self, profile: SensoryProfile) -> SensoryState:
        """Apply a predefined sensory profile."""
        ...

    def adjust(self, **overrides) -> SensoryState:
        """Fine-tune individual settings. User has full control."""
        ...

    def explain_current(self) -> str:
        """Plain-language description of active adaptations."""
        # e.g. "Text is 1.5x larger. Colors are high contrast. Animations are off."
        ...
```

### Accessibility Checklist (Built Into Design)

| Requirement | How Mycelium Addresses It |
|-------------|--------------------------|
| **Screen reader** | All output includes plain-text descriptions. No visual-only information. |
| **Keyboard navigation** | Every action has a keyboard shortcut. Tab order is logical. |
| **High contrast** | `SensoryProfile.LOW_VISION` activates high-contrast mode automatically. |
| **Reduced motion** | `SensoryProfile.CALM` disables all animations and transitions. |
| **Voice input** | `SensoryProfile.MOTOR` enables voice-first interaction. |
| **Cognitive load** | `SensoryProfile.COGNITIVE` triggers ScaffoldingEngine (chunking, step-by-step). |
| **Text-to-speech** | Customizable voice profiles with adjustable speech rate. |
| **Privacy** | On-device processing. No cloud. No storage without explicit opt-in. |

---

## Part VIII: Controlled Autonomy & User Agency

### Design Principle: Augment, Never Replace

> *"GRID's ethical framework: Does this pattern serve the user's growth?"*
> *"The system facilitates resonance. It does not impose meaning."*

### Module: `mycelium/copilot.py` — Co-Pilot Mode & Trust Meter

```python
"""
Co-Pilot Mode — AI suggests, human decides.

Every suggestion is:
1. Explained in plain language (why this suggestion?)
2. Shown with a Trust Meter (how confident? how aligned with your preferences?)
3. Reversible (undo anything, anytime)
4. Optional (never auto-applied without explicit approval)

Grounded in GRID's boundary engine and Triadic Safeguarding principles.
"""

from dataclasses import dataclass
from enum import StrEnum


class ApprovalLevel(StrEnum):
    """How much autonomy the user grants the tool."""
    SUGGEST_ONLY = "suggest_only"      # show suggestions, never act
    ASK_FIRST = "ask_first"            # suggest + ask before acting
    AUTO_MINOR = "auto_minor"          # auto-apply minor, ask for major
    FULL_AUTO = "full_auto"            # auto-apply all (user explicitly opts in)


@dataclass
class Suggestion:
    """A single suggestion from the tool to the user."""
    action: str                        # what it wants to do
    reason: str                        # why (plain language)
    pattern_basis: str                 # which cognitive pattern informed this
    confidence: float                  # 0.0–1.0
    trust_score: float                 # alignment with user's past preferences
    eli5: str                          # explain like I'm 5


@dataclass
class TrustMeter:
    """Visual indicator of suggestion alignment with user preferences."""
    score: float                       # 0.0–1.0
    label: str                         # "Low", "Medium", "High", "Very High"
    reasoning: str                     # e.g. "Based on your preference for symmetry-based explanations"

    @staticmethod
    def from_score(score: float, reasoning: str) -> "TrustMeter":
        if score >= 0.8:
            label = "Very High"
        elif score >= 0.6:
            label = "High"
        elif score >= 0.4:
            label = "Medium"
        else:
            label = "Low"
        return TrustMeter(score=score, label=label, reasoning=reasoning)


class CoPilot:
    """Co-Pilot mode. Suggests, explains, waits for approval."""

    def __init__(self, approval_level: ApprovalLevel = ApprovalLevel.ASK_FIRST):
        self.approval_level = approval_level
        self.preference_history: list[dict] = []   # tracks what user accepts/rejects

    def suggest(self, action: str, context: dict) -> Suggestion:
        """Generate a suggestion with full explanation and trust score."""
        ...

    def explain_decision(self, suggestion: Suggestion) -> str:
        """'Explain Your Decision' — why was this suggested?"""
        # e.g. "I suggested caching this because you access it 47 times/minute.
        #        Pattern: Repetition. Trust: High (you've accepted similar suggestions 8 times)."
        ...

    def user_feedback(self, suggestion: Suggestion, accepted: bool, reason: str | None = None):
        """Learn from user's accept/reject decisions. Stored locally only."""
        ...
```

### Module: `mycelium/scaffolding.py` — Adaptive Scaffolding

```python
"""
Adaptive Scaffolding — Dynamic content adaptation for Mycelium.

Directly extends GRID's ScaffoldingEngine and CognitiveRouter patterns.
Adjusts explanation depth, complexity, and format based on:
  - Detected cognitive load (from interaction patterns)
  - User expertise level (from preference history)
  - Explicit feedback ("too complex" / "too simple")
"""

from enum import StrEnum


class ScaffoldDepth(StrEnum):
    """Scaffolding depth levels. Maps to GRID's load thresholds."""
    NONE = "none"                # expert user, no scaffolding
    LIGHT = "light"              # examples only
    MODERATE = "moderate"        # examples + explanations + chunking
    FULL = "full"                # step-by-step + hints + progressive disclosure
    MAXIMUM = "maximum"          # all strategies + visual aids + audio cues


class AdaptiveScaffold:
    """Wraps GRID's ScaffoldingEngine for Mycelium's accessibility layer."""

    def determine_depth(self, interaction_history: list, explicit_feedback: str | None = None) -> ScaffoldDepth:
        """Auto-detect appropriate scaffolding depth."""
        # If user said "too complex" → increase depth
        # If user said "I know this" → decrease depth
        # If no feedback → infer from interaction speed and error rate
        ...

    def scaffold_explanation(self, concept: str, depth: ScaffoldDepth) -> dict:
        """Apply scaffolding to a concept explanation.

        Returns dict with keys:
          - summary: one-line gist
          - steps: list of step-by-step breakdown (if depth >= MODERATE)
          - examples: concrete examples (if depth >= LIGHT)
          - visual: visual description/diagram hint (if depth >= FULL)
          - audio_script: text-to-speech friendly version (if depth == MAXIMUM)
        """
        ...

    def feedback(self, too_complex: bool | None = None, too_simple: bool | None = None):
        """User feedback adjusts future scaffolding depth."""
        ...
```

---

## Part IX: Ethical Guardrails & Risk Mitigation

### Risk Table

| Risk | Mitigation | Mycelium Implementation |
|------|-----------|------------------------|
| **Over-reliance on AI** | Human-in-the-loop for critical decisions | `CoPilot.approval_level` defaults to `ASK_FIRST`. `FULL_AUTO` requires explicit opt-in. |
| **Data privacy violations** | On-device processing, no cloud storage | All layers (Gesture, Wall, Signal) run locally. No network calls by default. |
| **Cultural insensitivity** | Diversity audits of explanations and analogies | `PatternNavigator` uses universal geometric metaphors, not culture-specific ones. |
| **Accessibility gaps** | Continuous testing with disability advocacy groups | `SensoryMode` profiles designed with WCAG 2.2 AA as baseline, not ceiling. |
| **Stigma around assistive AI** | Normalize through design — assistive features are default, not add-on | Every user gets `PatternNavigator`. It's not "assistive mode" — it's the primary interface. |
| **Explanation opacity** | Every decision is explainable | `CoPilot.explain_decision()` is mandatory. No suggestion without a reason. |
| **Preference lock-in** | User can reset all learned preferences | `CoPilot.preference_history` is clearable. No permanent state without consent. |
| **Cognitive overload from tool itself** | Adaptive scaffolding | `AdaptiveScaffold` reduces its own complexity when user shows signs of overload. |

### Privacy Dashboard (Concept)

```
┌─────────────────────────────────────────────────┐
│  MYCELIUM Privacy                               │
│                                                 │
│  [ ] Share usage data to improve features       │
│  [ ] Allow tool to learn from my interactions   │
│      (default: OFF)                             │
│  [x] Keep all data on this device              │
│      (default: ON, not changeable)              │
│                                                 │
│  [Clear All Stored Preferences]                 │
│  [Export My Data]                                │
│  [Delete Everything]                            │
└─────────────────────────────────────────────────┘
```

---

## Part X: Resonance Framework — The Philosophical Foundation

### Why This Tool Is Different From "Just Another Cache"

Traditional data tools are designed around **commands** — you learn a vocabulary of operations and apply them correctly. Redis has 500+ commands. That's a language barrier.

Mycelium is designed around **resonance** — you describe what you need, and the tool finds the pattern that fits. Like how:

- A caveman didn't need grammar to point at a bison on a wall and make another human understand "danger"
- A mother tree doesn't need a protocol to route carbon to a shaded seedling — need creates flow
- A gesture means different things in different contexts — and that's a feature, not a bug

### The Resonance Loop

```
User Intent → Pattern Detection → Geometric Analogy → Scaffolded Explanation
     ↑                                                        │
     └──────── Feedback ("clicked" / "didn't click") ─────────┘
```

This is GRID's `Recognize → Analyze → Recommend` triad applied to **understanding itself**.

### Consciousness Parallel (Research Note)

The user's directive draws a parallel between GRID's geometric resonance and neural geometry research (including psilocybin studies on default mode network disruption). Key structural parallel:

| Element | GRID Architecture | Neural Geometry | Mycelium Tool |
|---------|------------------|----------------|---------------|
| **Substrate** | Geometric resonance patterns | Small-world neural networks | Pattern lenses |
| **Basic unit** | Pattern (Symmetry, Fractal, etc.) | Synaptic resonance | PatternLens analogy |
| **Emergence** | Patterns resonate → new patterns | Thoughts resonate → new meanings | Explanation clicks → deeper understanding |
| **Disruption** | Routines adapt to user input | Ego dissolves, revealing resonance | Scaffolding adapts to feedback |
| **Ethical core** | User autonomy + resonance alignment | Compassion + curiosity | Suggest, never impose |

This parallel suggests that **the most accessible interface is one that resonates with the user's existing cognitive geometry** — not one that forces them to learn a new symbolic system.

This is a subject for deeper research. The tool design acknowledges it as an influence without claiming scientific certainty.

---

## Part XI: Complete Module Map

```
mycelium/
├── core.py              # Spore, MyceliumInterface, Depth, SignalType
├── gesture.py           # GestureStore (ephemeral in-memory)
├── wall.py              # WallStore (persistent SQLite)
├── signal.py            # SignalBus (pub/sub event bus)
├── hyphae.py            # HyphaeRouter (context-aware routing)
├── mother_tree.py       # MotherTree (hub manager, analytics, rate limiting)
├── adapt.py             # CoffeeModeAdapter (Espresso/Americano/Cold Brew)
├── navigator.py         # PatternNavigator (geometric concept explorer)
├── sensory.py           # SensoryMode (accessibility profiles)
├── copilot.py           # CoPilot + TrustMeter (controlled autonomy)
├── scaffolding.py       # AdaptiveScaffold (dynamic explanation depth)
├── privacy.py           # PrivacyDashboard (on-device, opt-in only)
└── explain.py           # Explanation engine (ELI5, pattern-based, resonance feedback)
```

### Layer Interaction

```
User
  │
  ▼
┌──────────────────────────────────┐
│  CoPilot (suggest, explain, ask) │ ← TrustMeter
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  PatternNavigator                │ ← User picks lens, gives feedback
│  (geometric concept explorer)    │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  AdaptiveScaffold                │ ← Adjusts depth based on feedback + load
│  (chunking, ELI5, step-by-step) │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  SensoryMode                     │ ← Adapts output format (visual, audio, tactile)
│  (accessibility profiles)        │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  HyphaeRouter                    │ ← Routes to correct data layer
│  (context-aware dispatch)        │
└──────────┬───────────────────────┘
           │
     ┌─────┼──────┐
     ▼     ▼      ▼
  Gesture  Wall  Signal
  (fast)  (durable) (broadcast)
```

---

## Summary: What MYCELIUM Is

A **scoped, accessibility-first, user-centric data tool** that:

1. **Simplifies Redis-like functionality** into 3 verbs (`plant`/`harvest`/`signal`) and 1 data type (`Spore`)
2. **Explains complex data concepts** through geometric pattern lenses — not jargon
3. **Adapts to the user** — cognitive load, expertise, sensory needs, preferences
4. **Never imposes** — suggests, explains, waits for approval (Co-Pilot + Trust Meter)
5. **Runs locally** — zero cloud, zero tracking, zero dependencies by default
6. **Degrades gracefully** — always works, even without network/disk/Redis
7. **Is grounded in nature** — mycelium networks (need-based routing), cave symbols (meaning before syntax)
8. **Is grounded in code** — extends GRID's ScaffoldingEngine, CognitiveRouter, PatternRecognizer, CoffeeMode, EventBus patterns

> *Like mycelium: simple threads, profound network.*
> *Like cave symbols: imperfect marks, perfect meaning.*
