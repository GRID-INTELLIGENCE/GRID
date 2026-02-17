# Architecture Proposal: Decoupling Vision UI

**Status:** Proposed
**Date:** 2025-12-03
**Target:** `src/vision_ui` (Fan-In: 13)

## Problem Statement
The `vision_ui` module has become a "High Fan-In" node (13 incoming dependencies), meaning core business logic and services are directly importing UI components. This violates Clean Architecture principles, making the system brittle, hard to test, and tightly coupled.

## Proposed Solution: Dependency Inversion
We propose inverting the dependency relationship. Instead of Core depending on UI, Core will depend on an abstraction (`IVisionService`), and the UI will implement this abstraction. The `GridAppBuilder` will wire them together at runtime.

### Visualization

```mermaid
graph TD
    %% Current State
    subgraph Current_Architecture [Current: High Coupling]
        style Current_Architecture fill:#ffebee,stroke:#c62828,stroke-width:2px
        M1[Business Logic] -->|Direct Import| VUI[vision_ui]
        M2[Data Processor] -->|Direct Import| VUI
        M3[Controller] -->|Direct Import| VUI
        VUI :::hotspot
    end

    %% Desired State
    subgraph Target_Architecture [Target: Dependency Inversion]
        style Target_Architecture fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
        D1[Business Logic] -->|Depends on| I[<< Interface >>\nIVisionService]
        D2[Data Processor] -->|Depends on| I
        VUI_Impl[vision_ui] -.->|Implements| I
        I :::interface
    end

    classDef hotspot fill:#ffccbc,stroke:#bf360c,stroke-width:2px;
    classDef interface fill:#fff9c4,stroke:#fbc02d,stroke-dasharray: 5 5;
```

## Implementation Plan

1.  **Define Protocol**: Create `IVisionService` in `src/core/interfaces.py`.
2.  **Implement Service**: Create `VisionService` in `src/vision_ui/service.py` implementing the protocol.
3.  **Update Builder**: Add `with_vision_service()` to `GridAppBuilder` in `src/core/builder.py`.
4.  **Refactor Consumers**: Update modules to use `IVisionService` injected via constructor or method arguments.

## Benefits
- **Decoupling**: Core logic no longer knows about UI implementation details.
- **Testability**: Can easily mock `IVisionService` for unit tests.
- **Flexibility**: Can swap UI implementations (e.g., Console vs. Web vs. GUI) without changing core logic.
