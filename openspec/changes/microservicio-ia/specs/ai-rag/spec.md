## ADDED Requirements

### Requirement: RAG pipeline retrieves clinical knowledge
The system SHALL implement a RAG (Retrieval-Augmented Generation) pipeline using ChromaDB and sentence-transformers to answer clinical knowledge queries.

#### Scenario: Knowledge retrieval
- **WHEN** the `search_knowledge` tool is called with a clinical query
- **THEN** the system embeds the query using `sentence-transformers/all-MiniLM-L6-v2`
- **AND** queries the ChromaDB collection for the top-5 most similar documents
- **AND** returns the retrieved documents as context to the agent

#### Scenario: Knowledge base initialization
- **WHEN** the microservice starts and the ChromaDB collection is empty
- **THEN** the system loads clinical knowledge documents from `data/knowledge_base/` into the vector store
- **AND** creates embeddings for each document

#### Scenario: Document addition
- **WHEN** a new clinical document is added to `data/knowledge_base/`
- **THEN** the system provides a mechanism to re-index the knowledge base
