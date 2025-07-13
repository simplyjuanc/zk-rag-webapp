# Definition of Done

- I have embedded all of my and have them in a Vector DB.
- My (new) notes are processed on a weekly basis.
- I can query my notes and get both:
  - A synthesised answer.
  - References to the original documents.
- The above is rendered in some basic form of a web UI.

# Context

I write many notes on every sort of topic that I learn or media that I consume, and I want to develop and app that will use LLM models as well as a basic data pipeline to ask questions about my own thinking (as captured in those notes) throughout the years I haven been taking notes.

As interested as I am in questioning my own notes and thinking, my objective is also to learn and get exposure into data (RAG-ish) pipelines, as well as general app development. I am a web developer with ~3 years of experience in both front end and back end technologies, but primarily the latter.

The notes are in markdown format and are all found under a specific directory in my local Desktop, although they can be nested within further directories.
Most of these have also some additional metadata at the beginning of the content, which can look like, for instance, the two examples below. There is some variation in their properties and they might not capture all of the document's data, but they can be helpful.

```markdown
---
last updated: 2025-05-25
created_on: 2025-05-24
---
```

```markdown
---
author:
  - Greg McKeown
type:
  - reference
category:
  - book
created_on: 2025-05-08
last updated: 2025-05-14
source:
checked: false
---
```

# Architecture

## High-level System Design

```mermaid
flowchart TB
subgraph Frontend["Frontend Layer"]
	UI["Web Interface"]
end

subgraph API["API Gateway"]
	SERVER["FastAPI Server"]
end

subgraph Processing["Data Processing"]
	PIPELINE["Data Pipeline"]
	SERVICES["Core Services"]
end

subgraph AI["AI/LLM Layer"]
	LLM["Language Models"]
end

subgraph Storage["Storage Layer"]
	VECTOR_DB[("Vector Database")]
	FILE_STORE[("File Storage")]
end

subgraph External["External Sources"]
	FILES["Document Files"]
end

UI --> SERVER
FILES --> PIPELINE
PIPELINE --> VECTOR_DB
PIPELINE --> FILE_STORE
SERVER --> SERVICES
SERVICES --> VECTOR_DB
SERVICES --> LLM
LLM --> SERVICES

classDef frontend fill:#e1f5fe
classDef api fill:#f3e5f5
classDef processing fill:#e8f5e8
classDef storage fill:#fff3e0
classDef llm fill:#fce4ec
classDef external fill:#f1f8e9

class UI frontend
class SERVER api
class PIPELINE,SERVICES processing
class VECTOR_DB,FILE_STORE storage
class LLM llm
class FILES external
```

## Individual Component Structure

**FrontEnd and API**

```mermaid
flowchart TB
    subgraph subGraph0["Frontend Layer"]
        UI["Web Interface<br>Streamlit/Next.js"]
        API_CLIENT["API Client"]
    end

    subgraph subGraph1["API Gateway"]
        API["FastAPI Server<br>REST/WebSocket"]
        AUTH["Authentication<br>&amp; Authorization"]
    end

    %% Integration Points (External to this layer)
    CORE_SERVICES["Core Services Layer"]
    OBSERVABILITY["Observability Layer"]

    UI --> API_CLIENT
    API_CLIENT --> API
    API --> AUTH

    %% Integration with rest of system
    API --> CORE_SERVICES
    API --> OBSERVABILITY

    classDef frontend fill:#e1f5fe
    classDef api fill:#f3e5f5
    classDef integration fill:#f0f0f0,stroke-dasharray: 5 5

    class UI,API_CLIENT frontend
    class API,AUTH api
    class CORE_SERVICES,OBSERVABILITY integration
```

**Core Services Layer**

```mermaid
flowchart TB
    subgraph subGraph2["Core Services"]
        UPLOAD["File Upload<br>Service"]
        QUERY["Query Processing<br>Service"]
        INSIGHT["Insight Generation<br>Service"]
        PIPELINE["Data Pipeline<br>Controller"]
    end

    %% Integration Points (External to this layer)
    API_GATEWAY["API Gateway"]
    DATA_PIPELINE["Data Processing Pipeline"]
    STORAGE["Storage Layer"]
    LLM_LAYER["LLM Layer"]
    EXTERNAL_FILES["External Files"]
    OBSERVABILITY["Observability"]

    %% Internal flow
    UPLOAD --> PIPELINE
    PIPELINE --> QUERY
    PIPELINE --> INSIGHT
    QUERY -.-> INSIGHT

    %% Integration with rest of system
    API_GATEWAY --> UPLOAD
    API_GATEWAY --> QUERY
    API_GATEWAY --> INSIGHT
    EXTERNAL_FILES --> UPLOAD
    UPLOAD --> STORAGE
    PIPELINE --> DATA_PIPELINE
    QUERY --> STORAGE
    QUERY --> LLM_LAYER
    INSIGHT --> STORAGE
    INSIGHT --> LLM_LAYER
    UPLOAD --> OBSERVABILITY
    QUERY --> OBSERVABILITY
    INSIGHT --> OBSERVABILITY

    classDef processing fill:#e8f5e8
    classDef integration fill:#f0f0f0,stroke-dasharray: 5 5

    class UPLOAD,QUERY,INSIGHT,PIPELINE processing
    class API_GATEWAY,DATA_PIPELINE,STORAGE,LLM_LAYER,EXTERNAL_FILES,OBSERVABILITY integration
```

**Data Processing Pipeline**

```mermaid
flowchart TB
    subgraph subGraph3["Data Processing Pipeline"]
        INGEST["Data Ingestion"]
        PREPROCESS["Text Preprocessing<br>spaCy/NLTK"]
        CHUNK["Semantic Chunking<br>LangChain/LlamaIndex"]
        EMBED["Embedding Generation<br>OpenAI/Sentence-T"]
        METADATA["Metadata Extraction<br>Tags, Dates, Topics"]
    end

    %% Integration Points (External to this layer)
    CORE_SERVICES["Core Services Controller"]
    STORAGE_VECTOR["Vector Database"]
    STORAGE_METADATA["Metadata Database"]
    STORAGE_FILES["File Storage"]
    OBSERVABILITY["Observability"]

    %% Internal pipeline flow
    INGEST --> PREPROCESS
    PREPROCESS --> CHUNK
    CHUNK --> EMBED
    CHUNK --> METADATA

    %% Integration with rest of system
    CORE_SERVICES --> INGEST
    EMBED --> STORAGE_VECTOR
    METADATA --> STORAGE_METADATA
    INGEST --> STORAGE_FILES
    INGEST --> OBSERVABILITY
    EMBED --> OBSERVABILITY

    classDef processing fill:#e8f5e8
    classDef integration fill:#f0f0f0,stroke-dasharray: 5 5

    class INGEST,PREPROCESS,CHUNK,EMBED,METADATA processing
    class CORE_SERVICES,STORAGE_VECTOR,STORAGE_METADATA,STORAGE_FILES,OBSERVABILITY integration
```

**LLM Layer**

```mermaid
flowchart TB
    subgraph subGraph4["LLM Layer"]
        LLM_ROUTER["LLM Router"]
        OPENAI["OpenAI GPT-4"]
        CLAUDE["Claude API"]
        LOCAL["Local Models<br>Ollama/vLLM"]
        PROMPT_MGMT["Prompt Management<br>LangChain"]
    end

    %% Integration Points (External to this layer)
    CORE_SERVICES["Core Services"]
    OBSERVABILITY["Observability"]
    CACHE["Redis Cache"]

    %% Internal LLM flow
    LLM_ROUTER --> OPENAI
    LLM_ROUTER --> CLAUDE
    LLM_ROUTER --> LOCAL
    LLM_ROUTER --> PROMPT_MGMT

    %% Integration with rest of system
    CORE_SERVICES --> LLM_ROUTER
    LLM_ROUTER --> CORE_SERVICES
    LLM_ROUTER --> OBSERVABILITY
    LLM_ROUTER --> CACHE

    classDef llm fill:#fce4ec
    classDef integration fill:#f0f0f0,stroke-dasharray: 5 5

    class LLM_ROUTER,OPENAI,CLAUDE,LOCAL,PROMPT_MGMT llm
    class CORE_SERVICES,OBSERVABILITY,CACHE integration
```

**Storage Layer**

```mermaid
flowchart TB
    subgraph subGraph5["Storage Layer"]
        VECTOR_DB[("Vector Database<br>PostgreSQL + pgvector<br>or Pinecone")]
        METADATA_DB[("Metadata DB<br>PostgreSQL")]
        FILE_STORE[("File Storage<br>Local/S3")]
        CACHE[("Redis Cache<br>Embeddings &amp; Results")]
    end

    %% Integration Points (External to this layer)
    DATA_PIPELINE["Data Processing Pipeline"]
    CORE_SERVICES["Core Services"]
    LLM_LAYER["LLM Layer"]
    BACKGROUND_JOBS["Background Jobs"]
    EXTERNAL_FILES["External Files"]

    %% Internal storage relationships
    VECTOR_DB -.-> CACHE
    METADATA_DB -.-> CACHE

    %% Integration with rest of system
    DATA_PIPELINE --> VECTOR_DB
    DATA_PIPELINE --> METADATA_DB
    DATA_PIPELINE --> FILE_STORE
    EXTERNAL_FILES --> FILE_STORE
    CORE_SERVICES --> VECTOR_DB
    CORE_SERVICES --> METADATA_DB
    CORE_SERVICES --> CACHE
    LLM_LAYER --> CACHE
    BACKGROUND_JOBS --> VECTOR_DB
    BACKGROUND_JOBS --> METADATA_DB

    classDef storage fill:#fff3e0
    classDef integration fill:#f0f0f0,stroke-dasharray: 5 5

    class VECTOR_DB,METADATA_DB,FILE_STORE,CACHE storage
    class DATA_PIPELINE,CORE_SERVICES,LLM_LAYER,BACKGROUND_JOBS,EXTERNAL_FILES integration
```

**Background Jobs and Observability**

```mermaid
flowchart TB
    subgraph subGraph6["External Sources"]
        FILES["Notes Files<br>MD, TXT, PDF"]
        EXTERNAL_API["External APIs<br>Optional integrations"]
    end

    subgraph subGraph7["Background Jobs"]
        SCHEDULER["Job Scheduler<br>Celery/Airflow"]
        WORKER["Background Workers"]
        ANALYSIS["Periodic Analysis<br>Relationship Discovery"]
    end

    subgraph Observability["Observability"]
        LOGS["Logging"]
        METRICS["Metrics Collection"]
        MONITOR["Health Monitoring"]
    end

    %% Integration Points (External to these layers)
    CORE_SERVICES["Core Services"]
    STORAGE_LAYER["Storage Layer"]
    API_GATEWAY["API Gateway"]
    LLM_LAYER["LLM Layer"]
    DATA_PIPELINE["Data Pipeline"]

    %% Internal flows
    SCHEDULER --> WORKER
    WORKER --> ANALYSIS
    LOGS --> METRICS
    METRICS --> MONITOR

    %% Integration with rest of system
    FILES --> CORE_SERVICES
    EXTERNAL_API --> CORE_SERVICES
    ANALYSIS --> STORAGE_LAYER
    API_GATEWAY --> LOGS
    CORE_SERVICES --> LOGS
    LLM_LAYER --> METRICS
    DATA_PIPELINE --> LOGS

    classDef external fill:#f1f8e9
    classDef background fill:#e3f2fd
    classDef observability fill:#f9fbe7
    classDef integration fill:#f0f0f0,stroke-dasharray: 5 5

    class FILES,EXTERNAL_API external
    class SCHEDULER,WORKER,ANALYSIS background
    class LOGS,METRICS,MONITOR observability
    class CORE_SERVICES,STORAGE_LAYER,API_GATEWAY,LLM_LAYER,DATA_PIPELINE integration
```

## Comprehensive Low-level System Architecture

The below is better seem in the online Mermaid chart live editor.

```mermaid

flowchart TB
 subgraph subGraph0["Frontend Layer"]
        UI["Web Interface<br>Streamlit/Next.js"]
        API_CLIENT["API Client"]
  end
 subgraph subGraph1["API Gateway"]
        API["FastAPI Server<br>REST/WebSocket"]
        AUTH["Authentication<br>&amp; Authorization"]
  end
 subgraph subGraph2["Core Services"]
        UPLOAD["File Upload<br>Service"]
        QUERY["Query Processing<br>Service"]
        INSIGHT["Insight Generation<br>Service"]
        PIPELINE["Data Pipeline<br>Controller"]
  end
 subgraph subGraph3["Data Processing Pipeline"]
        INGEST["Data Ingestion"]
        PREPROCESS["Text Preprocessing<br>spaCy/NLTK"]
        CHUNK["Semantic Chunking<br>LangChain/LlamaIndex"]
        EMBED["Embedding Generation<br>OpenAI/Sentence-T"]
        METADATA["Metadata Extraction<br>Tags, Dates, Topics"]
  end
 subgraph subGraph4["LLM Layer"]
        LLM_ROUTER["LLM Router"]
        OPENAI["OpenAI GPT-4"]
        CLAUDE["Claude API"]
        LOCAL["Local Models<br>Ollama/vLLM"]
        PROMPT_MGMT["Prompt Management<br>LangChain"]
  end
 subgraph subGraph5["Storage Layer"]
        VECTOR_DB[("Vector Database<br>PostgreSQL + pgvector<br>or Pinecone")]
        METADATA_DB[("Metadata DB<br>PostgreSQL")]
        FILE_STORE[("File Storage<br>Local/S3")]
        CACHE[("Redis Cache<br>Embeddings &amp; Results")]
  end
 subgraph subGraph6["External Sources"]
        FILES["Notes Files<br>MD, TXT, PDF"]
        EXTERNAL_API["External APIs<br>Optional integrations"]
  end
 subgraph subGraph7["Background Jobs"]
        SCHEDULER["Job Scheduler<br>Celery/Airflow"]
        WORKER["Background Workers"]
        ANALYSIS["Periodic Analysis<br>Relationship Discovery"]
  end
 subgraph Observability["Observability"]
        LOGS["Logging"]
        METRICS["Metrics Collection"]
        MONITOR["Health Monitoring"]
  end
    UI --> API_CLIENT
    API_CLIENT --> API
    API --> AUTH & UPLOAD & QUERY & INSIGHT & LOGS & MONITOR
    FILES --> UPLOAD & FILE_STORE
    UPLOAD --> PIPELINE
    PIPELINE --> INGEST & LOGS
    INGEST --> PREPROCESS
    PREPROCESS --> CHUNK
    CHUNK --> EMBED & METADATA
    EMBED --> VECTOR_DB
    METADATA --> METADATA_DB
    QUERY --> VECTOR_DB & METADATA_DB & CACHE & LLM_ROUTER
    LLM_ROUTER --> OPENAI & CLAUDE & LOCAL & PROMPT_MGMT & METRICS
    INSIGHT --> VECTOR_DB & METADATA_DB & LLM_ROUTER
    SCHEDULER --> WORKER
    WORKER --> ANALYSIS
    ANALYSIS --> VECTOR_DB & METADATA_DB
     UI:::frontend
     API_CLIENT:::frontend
     API:::api
     AUTH:::api
     UPLOAD:::processing
     QUERY:::processing
     INSIGHT:::processing
     PIPELINE:::processing
     INGEST:::processing
     PREPROCESS:::processing
     CHUNK:::processing
     EMBED:::processing
     METADATA:::processing
     LLM_ROUTER:::llm
     OPENAI:::llm
     CLAUDE:::llm
     LOCAL:::llm
     PROMPT_MGMT:::llm
     VECTOR_DB:::storage
     METADATA_DB:::storage
     FILE_STORE:::storage
     CACHE:::storage
     FILES:::external
     EXTERNAL_API:::external
    classDef frontend fill:#e1f5fe
    classDef api fill:#f3e5f5
    classDef processing fill:#e8f5e8
    classDef storage fill:#fff3e0
    classDef llm fill:#fce4ec
    classDef external fill:#f1f8e9

```

# Data Schema

## Fully-fleshed

```mermaid
erDiagram
    documents ||--o{ document_chunks : "has many"
    document_chunks ||--o{ chunk_topics : "belongs to many"
    topics ||--o{ chunk_topics : "has many"
    topics ||--o{ topics : "parent-child"
    documents ||--o{ document_relationships : "source"
    documents ||--o{ document_relationships : "target"

    documents {
        uuid id PK
        text file_path UK "NOT NULL"
        text file_name "NOT NULL"
        varchar file_extension "NOT NULL"
        bigint file_size "NOT NULL"
        text content_hash UK "NOT NULL"
        text raw_content "NOT NULL"
        text processed_content
        text title
        text[] author
        varchar document_type
        text[] category
        text[] tags
        text source
        date created_on
        date last_updated
        timestamp content_created_at
        timestamp content_modified_at
        timestamp processed_at "DEFAULT NOW()"
        varchar processing_version "DEFAULT '1.0'"
        integer chunk_count "DEFAULT 0"
        boolean is_processed "DEFAULT FALSE"
        boolean is_indexed "DEFAULT FALSE"
        text[] processing_errors
        tsvector search_vector "GENERATED"
        timestamp created_at "DEFAULT NOW()"
        timestamp updated_at "DEFAULT NOW()"
    }

    document_chunks {
        uuid id PK
        uuid document_id FK "NOT NULL"
        text content "NOT NULL"
        text content_hash "NOT NULL"
        integer chunk_index "NOT NULL"
        varchar chunk_type "DEFAULT 'paragraph'"
        integer start_char
        integer end_char
        text parent_section
        integer token_count
        integer estimated_tokens
        vector embedding "vector(1536)"
        varchar embedding_model "DEFAULT 'text-embedding-ada-002'"
        timestamp embedding_created_at "DEFAULT NOW()"
        real semantic_similarity
        timestamp created_at "DEFAULT NOW()"
        timestamp updated_at "DEFAULT NOW()"
    }

    topics {
        uuid id PK
        varchar name UK "NOT NULL"
        text description
        varchar topic_type
        real confidence_score
        uuid parent_topic_id FK
        vector topic_embedding "vector(1536)"
        timestamp created_at "DEFAULT NOW()"
        timestamp updated_at "DEFAULT NOW()"
    }

    chunk_topics {
        uuid chunk_id PK,FK
        uuid topic_id PK,FK
        real relevance_score "NOT NULL"
        varchar extraction_method
    }

    document_relationships {
        uuid id PK
        uuid source_document_id FK "NOT NULL"
        uuid target_document_id FK "NOT NULL"
        varchar relationship_type "NOT NULL"
        real confidence_score "NOT NULL"
        text evidence
        varchar discovery_method
        timestamp created_at "DEFAULT NOW()"
    }

    query_sessions {
        uuid id PK
        text session_token
        text user_query "NOT NULL"
        text processed_query
        varchar query_intent
        vector query_embedding "vector(1536)"
        integer results_returned
        integer user_satisfaction_score
        uuid[] clicked_results
        timestamp created_at "DEFAULT NOW()"
    }

    computation_cache {
        uuid id PK
        text cache_key UK "NOT NULL"
        varchar cache_type "NOT NULL"
        text input_hash "NOT NULL"
        jsonb result "NOT NULL"
        integer access_count "DEFAULT 1"
        timestamp last_accessed_at "DEFAULT NOW()"
        timestamp expires_at
        timestamp created_at "DEFAULT NOW()"
    }
```

## MVP-scoped

# Tech Stack

The below structure roughly corresponds to the architectural requirements.

```text
personal-knowledge-ai/
├── README.md
├── .gitignore
├── docker-compose.yml
├── .env.example
├── Makefile
├── package.json           # Root JS dependencies
├── pyproject.toml         # Root Python config
├── requirements-dev.txt   # Python dev deps

├── apps/
│   ├── api/               # FastAPI backend
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── middleware/
│   │   ├── dependencies/
│   │   ├── models/
│   │   └── tests/
│   │
│   ├── web/               # React app with custom SSR
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │
│   │   ├── src/
│   │   │   ├── entry-client.tsx
│   │   │   ├── entry-server.tsx
│   │   │   ├── App.tsx
│   │   │   ├── components/
│   │   │   ├── pages/             # Route-based pages
│   │   │   ├── hooks/
│   │   │   └── lib/
│   │   └── tests/
│
│   └── worker/            # Background job processor
│       ├── main.py
│       ├── tasks/
│       └── tests/

├── libs/                  # Shared libraries
│   ├── core/              # Core business logic
│   ├── pipeline/          # Data processing pipeline
│   ├── llm/               # LLM abstraction layer
│   ├── storage/           # File/vector/meta stores
│   └── shared/            # Utilities, config, logging

├── scripts/               # Utility/setup scripts
├── docs/                  # Project documentation
└── tests/                 # High-level integration & E2E

```

- Considerations
  - A Monorepo is used in order to facilitate the iteration for a single developer, including the ability to update types during development over the OpenAPI standards
  - Turborepo will be used for build parallelisation if necessary once deploying the application in its entirety.
- Tooling Choices
  - Client-side
    - SSR React + Tanstack Router / Query
    - Zod for Validation
    - Vitest for testing
    - Vite as a build tool
    - CSS Styles for styng
  - Server Layer
    - FastApi (Python) as Web framewrok
    - Pydantic
    - Testing?
  - Data Pipeline
    - Langchain
    - Open Ai Embeddings and Open Ai models for chat initially, to be made swappable in case a different combination is decided.
  - Logging
    - structlog
    - Sentry
  - Storage
    - SQLAlchemy 2.0 - ORM for PostgreSQL
    - Alembic for Database migrations
    - asyncpg - Async PostgreSQL driver
    - pgvector - Vector extension
