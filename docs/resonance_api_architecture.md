```mermaid
graph TB
    %% Client Layer
    subgraph "Client Layer"
        Browser[Browsers]
        IDE[IDE Integrations]
        Tools[CLI Tools]
    end

    %% API Layer
    subgraph "API Layer (FastAPI)"
        subgraph "REST Endpoints"
            Process[POST /process<br/>Full activity processing]
            Context[GET /context<br/>Fast context snapshot]
            Paths[GET /paths<br/>Path triage options]
            Definitive[POST /definitive<br/>Canvas flip checkpoint]
            Envelope[GET /envelope/{id}<br/>ADSR envelope metrics]
            Complete[POST /complete/{id}<br/>Activity completion]
            Events[GET /events/{id}<br/>Activity events history]
        end

        subgraph "Real-time Communication"
            WS[WebSocket /ws/{activity_id}<br/>Real-time feedback stream]
        end
    end

    %% Service Layer
    subgraph "Service Layer"
        ResonanceSvc[ResonanceService<br/>Activity orchestration]
        ActivityRes[ActivityResonance<br/>Core resonance logic]
    end

    %% Core Components
    subgraph "Core Components"
        ContextProv[ContextProvider<br/>Fast context from application/]
        PathVis[PathVisualizer<br/>Path triage from light_of_the_seven/]
        ADSREnv[ADSREnvelope<br/>Haptic-like feedback]
        Feedback[ResonanceFeedback<br/>Real-time state updates]
    end

    %% Data Layer
    subgraph "Data Layer"
        Repo[ResonanceRepository<br/>Activity persistence]
        EventsDB[(Activity Events)]
        MetadataDB[(Activity Metadata)]
    end

    %% External Integrations
    subgraph "External Services"
        Databricks[Databricks Bridge<br/>Event logging]
        Skills[Skills Registry<br/>Schema transforms,<br/>compression, RAG]
        Tracing[Tracing Manager<br/>Performance monitoring]
    end

    %% Data Flow
    Browser --> Process
    Browser --> Context
    Browser --> Paths
    Browser --> Definitive
    Browser --> WS

    IDE --> Process
    IDE --> WS

    Tools --> Process
    Tools --> Context

    Process --> ResonanceSvc
    Context --> ResonanceSvc
    Paths --> ResonanceSvc
    Definitive --> ResonanceSvc
    Envelope --> ResonanceSvc
    Complete --> ResonanceSvc
    Events --> ResonanceSvc
    WS --> ResonanceSvc

    ResonanceSvc --> ActivityRes
    ResonanceSvc --> Repo

    ActivityRes --> ContextProv
    ActivityRes --> PathVis
    ActivityRes --> ADSREnv
    ActivityRes --> Feedback

    ResonanceSvc --> Databricks
    Definitive --> Skills
    API --> Tracing

    Repo --> EventsDB
    Repo --> MetadataDB

    %% Feedback Loop
    Feedback -.-> WS
    ADSREnv -.-> Feedback

    %% Styling
    classDef api fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef service fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef core fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef data fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef external fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef client fill:#f5f5f5,stroke:#424242,stroke-width:2px

    class Process,Context,Paths,Definitive,Envelope,Complete,Events,WS api
    class ResonanceSvc service
    class ActivityRes,ContextProv,PathVis,ADSREnv,Feedback core
    class Repo,EventsDB,MetadataDB data
    class Databricks,Skills,Tracing external
    class Browser,IDE,Tools client
```

### Resonance API Architecture Overview

**Left-to-Right Communication Pattern:**
- **Left Side (Fast Context)**: ContextProvider pulls from `application/` directory
- **Right Side (Path Triage)**: PathVisualizer analyzes from `light_of_the_seven/` directory
- **Center (Feedback)**: ADSR envelope provides haptic-like synchronous updates

**Key Endpoints:**
- `POST /process`: Full activity processing with resonance feedback
- `POST /definitive`: Mid-process checkpoint (~65%) that "flips the canvas" from chaotic to coherent
- `WebSocket /ws/{activity_id}`: Real-time feedback streaming
- `GET /context`: Fast context snapshots
- `GET /paths`: Path triage with left/right/straight options

**Data Flow:**
1. Client requests → API router
2. Router → ResonanceService orchestration
3. Service → ActivityResonance core logic
4. Core logic coordinates ContextProvider + PathVisualizer + ADSREnvelope
5. Feedback streamed back via WebSocket/callbacks
6. Events persisted to repository
7. External logging via Databricks Bridge

**Concurrency Handling:**
- Synchronous resonance processing with async API endpoints
- Threading for feedback loops (mitigates asyncio constraints)
- WebSocket connections for real-time updates
- Activity-scoped state management

**Error Handling:**
- Application boundary error wrapping
- Mothership exception handling
- Standardized HTTP error responses
