# 📊 StillMe IPC Dashboard Architecture

## Data Flow Diagram

```mermaid
graph TB
    A[Learning System] --> B[MetricsEmitter]
    B --> C[JSONL Events]
    B --> D[SQLite Database]
    
    C --> E[Aggregator]
    D --> E
    
    E --> F[CSV Reports]
    E --> G[Dashboard]
    
    G --> H[Streamlit UI]
    G --> I[FastAPI UI]
    
    H --> J[Charts & Tables]
    I --> J
    
    K[User] --> H
    K --> I
```

## Component Architecture

```mermaid
graph LR
    A[MetricsEmitter] --> B[PrivacyManager]
    A --> C[Registry]
    A --> D[Queries]
    
    B --> E[PIIRedactor]
    C --> F[MetricDefinition]
    D --> G[SQLite]
    
    H[Aggregator] --> I[CSV Export]
    H --> J[Summary Reports]
    
    K[Streamlit App] --> L[Charts]
    K --> M[Tables]
    K --> N[Filters]
    
    O[FastAPI App] --> P[WebSocket]
    O --> Q[REST API]
    O --> R[Real-time Updates]
```

## Metrics Schema

```mermaid
erDiagram
    RUNS {
        int id PK
        string session_id UK
        datetime started_at
        datetime ended_at
        string git_sha
        string version
        boolean success
        string stage
        string notes
    }
    
    METRICS {
        int id PK
        int run_id FK
        string name
        float value
        string unit
        string tag
        datetime ts
        string metadata
    }
    
    ERRORS {
        int id PK
        int run_id FK
        string type
        string message
        datetime ts
        string context_json
    }
    
    ROLLUPS {
        int id PK
        string date
        string metric
        float value
        string unit
        string dim_key
        string dim_val
    }
    
    RUNS ||--o{ METRICS : has
    RUNS ||--o{ ERRORS : has
```

## Dashboard Components

```mermaid
graph TD
    A[Streamlit App] --> B[Header]
    A --> C[Sidebar]
    A --> D[Main Content]
    A --> E[Footer]
    
    B --> F[Status Indicators]
    B --> G[Quick Metrics]
    
    C --> H[Date Range Filter]
    C --> I[Stage Filter]
    C --> J[Source Filter]
    C --> K[Component Filter]
    C --> L[Auto-refresh Control]
    
    D --> M[Learning Curve Tab]
    D --> N[Performance Tab]
    D --> O[Ingest Volume Tab]
    D --> P[Error Analysis Tab]
    D --> Q[Sessions Tab]
    
    M --> R[Pass Rate Chart]
    M --> S[Accuracy Chart]
    M --> T[Self-Assessment Chart]
    
    N --> U[Latency Chart]
    N --> V[Memory Gauge]
    N --> W[CPU Gauge]
    
    O --> X[Source Distribution]
    O --> Y[Daily Trends]
    O --> Z[Quality Metrics]
    
    P --> AA[Error Types]
    P --> BB[Error Trends]
    P --> CC[Error Summary]
    
    Q --> DD[Sessions Table]
    Q --> EE[Session Details]
    Q --> FF[Drill-down]
```

## Technology Stack

```mermaid
graph TB
    A[Frontend] --> B[Streamlit]
    A --> C[Plotly]
    A --> D[Pandas]
    
    E[Backend] --> F[Python]
    E --> G[SQLite]
    E --> H[FastAPI]
    
    I[Data] --> J[JSONL]
    I --> K[CSV]
    I --> L[SQLite]
    
    M[Infrastructure] --> N[Docker]
    M --> O[GitHub Actions]
    M --> P[Monitoring]
```

## Security & Privacy

```mermaid
graph TD
    A[Data Input] --> B[PrivacyManager]
    B --> C[PIIRedactor]
    C --> D[Anonymization]
    D --> E[Audit Log]
    
    F[User Access] --> G[Authentication]
    G --> H[Authorization]
    H --> I[Session Management]
    
    J[Data Storage] --> K[Encryption]
    K --> L[Access Control]
    L --> M[Retention Policy]
```

## Performance Optimization

```mermaid
graph LR
    A[Data Collection] --> B[Batch Processing]
    B --> C[Compression]
    C --> D[Caching]
    D --> E[Indexing]
    
    F[Query Optimization] --> G[SQL Indexes]
    F --> H[Query Caching]
    F --> I[Connection Pooling]
    
    J[UI Optimization] --> K[Lazy Loading]
    J --> L[Data Pagination]
    J --> M[Chart Optimization]
```

## Deployment Architecture

```mermaid
graph TB
    A[Development] --> B[Local Testing]
    B --> C[GitHub Actions]
    C --> D[Production]
    
    E[Monitoring] --> F[Logs]
    E --> G[Metrics]
    E --> H[Alerts]
    
    I[Scaling] --> J[Horizontal]
    I --> K[Vertical]
    I --> L[Auto-scaling]
```
