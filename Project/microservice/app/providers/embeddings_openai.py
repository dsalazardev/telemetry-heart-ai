from logging import getLogger

from langchain_openai import OpenAIEmbeddings
from langchain_core.embeddings import Embeddings

from app.core.registry import register

logger = getLogger(__name__)


@register("embeddings", "openai")
class OpenAIEmbeddingsProvider:
    def __init__(self, model: str = "text-embedding-3-small", **kwargs):
        self.model = model
        logger.info("OpenAI embeddings provider: model=%s", model)

    def get(self) -> Embeddings:
        return OpenAIEmbeddings(model=self.model)
