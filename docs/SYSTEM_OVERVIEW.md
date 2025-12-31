# System Overview

A comprehensive visual guide to the LineageGraph system architecture and data flow.

## System Architecture Diagram

```mermaid
graph TB
    subgraph UserLayer["User Interface"]
        Browser[Web Browser]
    end
    
    subgraph PresentationLayer["Presentation Layer"]
        ReactApp[React Application<br/>Vite Dev Server<br/>localhost:5173]
        Components[UI Components<br/>Query Interface<br/>Results Display]
    end
    
    subgraph ApplicationLayer["Application Layer"]
        FastAPI[FastAPI Server<br/>REST API<br/>localhost:8000]
        Endpoints[API Endpoints<br/>/health<br/>/api/query]
    end
    
    subgraph OrchestrationLayer["Orchestration Layer"]
        LangGraph[LangGraph Agent<br/>State Machine]
        Nodes[Agent Nodes<br/>Plan, Investigate<br/>Tool, Synthesize]
    end
    
    subgraph DataLayer["Data Layer"]
        VectorStore[(DuckDB<br/>Vector Database<br/>File-based)]
        GraphStore[(PostgreSQL<br/>Graph Database<br/>Port 5432)]
    end
    
    subgraph ServiceLayer["Service Layer"]
        Ollama[Ollama LLM<br/>Mistral 7B<br/>Port 11434]
        Jaeger[Jaeger<br/>OpenTelemetry<br/>Port 16686]
    end
    
    Browser --> ReactApp
    ReactApp --> Components
    Components -->|HTTP POST| FastAPI
    FastAPI --> Endpoints
    Endpoints --> LangGraph
    LangGraph --> Nodes
    Nodes --> VectorStore
    Nodes --> GraphStore
    Nodes --> Ollama
    LangGraph -.->|Traces| Jaeger
    FastAPI -->|Response| ReactApp
    
    style UserLayer fill:#f0f8ff
    style PresentationLayer fill:#e1f5ff
    style ApplicationLayer fill:#fff4e1
    style OrchestrationLayer fill:#ffe1f5
    style DataLayer fill:#e1ffe1
    style ServiceLayer fill:#f5e1ff
```

## Data Flow Architecture

```mermaid
flowchart LR
    subgraph Input["Input"]
        Query[Natural Language Query]
    end
    
    subgraph Processing["Processing Pipeline"]
        Embed[Embed Query]
        VectorSearch[Vector Search]
        GraphQuery[Graph Query]
        LLMReason[LLM Reasoning]
    end
    
    subgraph Storage["Data Storage"]
        VDB[(Vector DB)]
        GDB[(Graph DB)]
    end
    
    subgraph Output["Output"]
        Answer[Natural Language Answer]
        Context[Context Documents]
        Lineage[Lineage Path]
    end
    
    Query --> Embed
    Embed --> VectorSearch
    VectorSearch --> VDB
    VDB --> VectorSearch
    VectorSearch --> GraphQuery
    GraphQuery --> GDB
    GDB --> GraphQuery
    VectorSearch --> LLMReason
    GraphQuery --> LLMReason
    LLMReason --> Answer
    VectorSearch --> Context
    GraphQuery --> Lineage
    
    style Input fill:#e1f5ff
    style Processing fill:#fff4e1
    style Storage fill:#ffe1f5
    style Output fill:#e1ffe1
```

## Agent Workflow

```mermaid
stateDiagram-v2
    [*] --> Start: User Query Received
    
    Start --> Planning: Initialize Agent
    Planning --> PlanningLLM: Generate Plan
    PlanningLLM --> Investigating: Plan Ready
    
    Investigating --> InvestigatingLLM: Select Tools
    InvestigatingLLM --> Executing: Tools Selected
    
    Executing --> VectorTool: Execute Vector Search
    Executing --> GraphTool: Execute Graph Query
    
    VectorTool --> CheckConfidence: Results Received
    GraphTool --> CheckConfidence: Results Received
    
    CheckConfidence --> Investigating: Need More Info
    CheckConfidence --> Synthesizing: Sufficient Info
    
    Synthesizing --> SynthesizingLLM: Generate Answer
    SynthesizingLLM --> Complete: Answer Ready
    
    Complete --> [*]: Return Response
    
    note right of Planning
        Analyze query intent
        Create execution strategy
    end note
    
    note right of Executing
        Run selected tools
        Collect results
    end note
    
    note right of Synthesizing
        Combine all results
        Generate final answer
    end note
```

## Technology Stack

```mermaid
mindmap
    root((LineageGraph))
        Frontend
            React 18
            Vite 5
            Axios
        Backend
            FastAPI
            Python 3.11
            Pydantic
        Agent
            LangGraph
            LangChain
            State Machine
        Data
            DuckDB
            PostgreSQL
            Sentence Transformers
        Services
            Ollama
            Jaeger
            OpenTelemetry
```

## Component Relationships

```mermaid
erDiagram
    FRONTEND ||--o{ API : "sends requests"
    API ||--|| AGENT : "orchestrates"
    AGENT ||--o{ TOOLS : "executes"
    TOOLS ||--|| VECTOR_DB : "queries"
    TOOLS ||--|| GRAPH_DB : "queries"
    AGENT ||--|| LLM : "uses for reasoning"
    AGENT ||--o{ TRACING : "generates"
    
    FRONTEND {
        string React
        string Vite
        int port_5173
    }
    
    API {
        string FastAPI
        int port_8000
        string endpoints
    }
    
    AGENT {
        string LangGraph
        string state_machine
        array nodes
    }
    
    TOOLS {
        string search_vector_db
        string get_dependencies
        string validate_path
    }
    
    VECTOR_DB {
        string DuckDB
        string file_based
        int embeddings
    }
    
    GRAPH_DB {
        string PostgreSQL
        int nodes
        int edges
    }
    
    LLM {
        string Ollama
        string Mistral_7B
        int tokens_per_sec
    }
```

## Request-Response Cycle

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant F as Frontend
    participant A as API
    participant AG as Agent
    participant V as Vector DB
    participant G as Graph DB
    participant L as LLM
    
    U->>F: Enter Query
    F->>A: POST /api/query
    A->>AG: Initialize Agent
    
    AG->>AG: Plan Node
    AG->>L: Generate Plan
    L-->>AG: Execution Plan
    
    AG->>AG: Investigate Node
    AG->>L: Select Tools
    L-->>AG: Tool Selection
    
    AG->>V: search_vector_db()
    V-->>AG: Relevant Tables
    
    AG->>G: get_dependencies()
    G-->>AG: Dependency Tree
    
    AG->>AG: Synthesize Node
    AG->>L: Generate Answer
    L-->>AG: Final Answer
    
    AG-->>A: Agent State
    A-->>F: JSON Response
    F-->>U: Display Results
```

## Performance Metrics

```mermaid
pie title Query Processing Time Breakdown
    "LLM Inference" : 75
    "Vector Search" : 5
    "Graph Query" : 10
    "Network/Overhead" : 10
```

## Deployment Architecture

```mermaid
graph TB
    subgraph Local["Local Development"]
        DevFrontend[Frontend Dev Server]
        DevBackend[Backend Server]
        DevDB[(Local Databases)]
        DevLLM[Local Ollama]
    end
    
    subgraph CI["CI/CD Pipeline"]
        GitHub[GitHub Actions]
        Tests[Test Suite]
        Lint[Linting]
    end
    
    subgraph Production["Production Ready"]
        ProdFrontend[Frontend Build]
        ProdBackend[Backend API]
        ProdDB[(Production DBs)]
        ProdLLM[LLM Service]
    end
    
    DevFrontend --> DevBackend
    DevBackend --> DevDB
    DevBackend --> DevLLM
    
    GitHub --> Tests
    GitHub --> Lint
    
    Tests --> Production
    Lint --> Production
    
    style Local fill:#e1f5ff
    style CI fill:#fff4e1
    style Production fill:#ffe1f5
```

