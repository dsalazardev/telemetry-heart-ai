## ADDED Requirements

### Requirement: RAG pipeline retrieves clinical knowledge
The system SHALL implement a RAG (Retrieval-Augmented Generation) pipeline using ChromaDB `PersistentClient` and `SentenceTransformer` embeddings to answer clinical knowledge queries.

#### Scenario: Knowledge retrieval
- **WHEN** the `search_knowledge` tool is called with a clinical query
- **THEN** the system embeds the query using `SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2').encode()`
- **AND** queries the ChromaDB collection `clinical_knowledge` with `n_results=5` and `hnsw:space=cosine`
- **AND** returns the retrieved documents as context to the agent

#### Scenario: Knowledge base initialization
- **WHEN** the microservice starts and the ChromaDB collection is empty
- **THEN** the system loads clinical knowledge documents from `data/knowledge_base/` into the vector store
- **AND** creates embeddings for each document using `SentenceTransformer`
- **AND** stores documents with `titulo`, `contenido`, `embedding` (ARRAY Float(384) via SentenceTransformer), `fuente`, `fechaIndexacion`, `activo` metadata

#### Scenario: Document addition
- **WHEN** a new clinical document is added to `data/knowledge_base/`
- **THEN** the system provides a mechanism to re-index the knowledge base via `POST /agent/train` or direct script
