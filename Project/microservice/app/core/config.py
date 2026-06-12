from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "telemetry-heart-ai-microservice"
    host: str = "0.0.0.0"
    port: int = 8001
    environment: str = "dev"  # dev | demo | prod | evaluation

    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/telemetry_heart"

    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "http://localhost:1234/v1"
    llm_temperature: float = 0.0
    llm_timeout: int = 30

    embedding_provider: str = "fake"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 384

    vectorstore_path: str = "app/vectorstore/chroma"
    clinical_docs_path: str = "app/data/clinical_docs"
    weights_path: str = "app/data/optimized_weights.json"

    chunk_size: int = 800
    chunk_overlap: int = 120
    retrieval_k: int = 4
    retrieval_max_length: int = 2000
    chunk_separators: str = "\n## ,\n### ,\n\n,\n,. , "

    openai_api_key: str = ""

    langsmith_api_key: str = ""
    langsmith_project: str = "telemetry-heart-ai"
    langsmith_trace_v2: bool = True

    clinical_config_path: str = "app/config/clinical_params.yaml"
    internal_token: str = "dev-token-cambiar-en-prod"


settings = Settings()
