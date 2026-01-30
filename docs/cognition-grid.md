# Cognition Grid

This document defines a shared vocabulary for integrating environmental perception and cognitive patterns into the Grid framework. It describes nine pattern categories ("books") that can be referenced from code, experiments, or UI.

Each pattern has:
- **Name**: Human-friendly label
- **Code**: Stable identifier for programmatic reference
- **Color**: Canonical book color
- **Focus**: Core cognitive question it highlights
- **Description**: Short explanation
- **Examples**: Practical, real-world scenarios

## Pattern Catalog

### Green Book – Flow & Motion (`FLOW_MOTION`)
- **Focus**: How attention tracks change and predicts where things will be next.
- **Description**: Concerns visible or implied movement of people, vehicles, animals, and micro-movements in a scene.
- **Examples**:
  - Crowd flow in a station, one person moving against the stream.
  - Cars merging into a lane, a bicycle weaving through static traffic.
  - A dog zig-zagging on a leash, birds taking off in waves.
  - Hand gestures, fidgeting, shifting posture.

### Blue Book – Spatial Relationships (`SPATIAL_RELATIONSHIPS`)
- **Focus**: How objects and agents are arranged in space relative to each other and the observer.
- **Description**: Distances, alignments, clustering, and frames of reference that shape how a scene is navigated and interpreted.
- **Examples**:
  - Personal distance between strangers vs friends in a queue.
  - Desk objects clustered, lined up, or scattered.
  - Cars parked at angles vs perfectly aligned.
  - "My left" vs "next to the window" vs "north" as different reference frames.

### Yellow Book – Natural Rhythms (`NATURAL_RHYTHMS`)
- **Focus**: Periodic or quasi-periodic changes in natural or ambient phenomena.
- **Description**: Cycles and oscillations in the environment that can entrain the body or mind.
- **Examples**:
  - Trees swaying with wind, branches returning to a resting shape.
  - Cloud drift, variations in sky brightness.
  - Shadows moving and stretching during the day.
  - Waves on water, gust cycles, insect or bird choruses.

### Orange Book – Color & Light (`COLOR_LIGHT`)
- **Focus**: How contrast, brightness, and hue shape salience and emotional tone.
- **Description**: Patterns in light, color, reflection, and contrast that draw or guide attention.
- **Examples**:
  - A bright sign on a grey street; a single lit window at night.
  - Strong silhouettes against a sunset.
  - Reflections in puddles or glass facades.
  - Color groupings (e.g., uniforms, branding) dominating a space.

### Purple Book – Repetition & Habit (`REPETITION_HABIT`)
- **Focus**: How repeated events are compressed into routines and expectations.
- **Description**: Recurrent actions, sequences, and cycles that become predictable and often fade from conscious notice.
- **Examples**:
  - Traffic lights changing through a fixed sequence.
  - A bus or train arriving at regular intervals.
  - Foot-tapping, phone-checking, or other micro-habits.
  - Birds or pets following the same patrol routes.

### Red Book – Deviation & Surprise (`DEVIATION_SURPRISE`)
- **Focus**: Violations of expected patterns and the attention/curiosity they trigger.
- **Description**: Outliers, anomalies, and breaks in rhythm or arrangement that stand out against a background pattern.
- **Examples**:
  - A single bright outfit in a dark-suited crowd.
  - Somebody abruptly stopping in a flow of moving people.
  - A skipped traffic light cycle, or a bus arriving very early.
  - Out-of-place items (e.g., chair in hallway, umbrella on a clear day).

### Teal Book – Cause & Effect (`CAUSE_EFFECT`)
- **Focus**: Linking events into explanations: "this happened because of that".
- **Description**: Physical, social, and indirect causal chains, including delayed or non-obvious effects.
- **Examples**:
  - Wind causing leaves to move; pressure causing a door to open.
  - A loud sound making people turn their heads.
  - A small blockage upstream causing a large traffic jam downstream.
  - Earlier rain leading to slippery conditions later.

### Silver Book – Temporal Patterns (`TEMPORAL_PATTERNS`)
- **Focus**: Structure in time: sequence, duration, timing, and recurrence.
- **Description**: How events are ordered, repeated, or grouped in time, independent of spatial layout.
- **Examples**:
  - Clock ticks, bells, digital countdowns.
  - Trains or planes appearing at predictable intervals.
  - Rush-hour density vs mid-day sparsity.
  - Individual energy, focus, or mood cycles during a day.

### Gold Book – Combination Patterns (`COMBINATION_PATTERNS`)
- **Focus**: Interactions between two or more other pattern types.
- **Description**: Higher-order patterns that emerge when motion, space, rhythm, color, habit, surprise, and causality overlap.
- **Examples**:
  - Headlights forming rivers of light that reflect traffic flow.
  - A daily commute with fixed time (temporal), route (spatial), and repeated stops (habit).
  - A sudden blackout (deviation) causing coordinated phone-glow (cause & effect + light).
  - Store layouts using color blocks to guide motion paths.

## Programmatic Reference

In code, each pattern is represented by a stable identifier and associated metadata (name, color, description, examples). See `src/utils/cognition_grid.py` for the canonical implementation and helper functions.

Suggested usage patterns:
- Attach a cognition pattern identifier to an observation, event, or metric for downstream analysis.
- Drive UI elements (icons, labels, colors) from the pattern metadata instead of hard-coding.
- Use combination patterns when multiple base patterns are simultaneously relevant.
