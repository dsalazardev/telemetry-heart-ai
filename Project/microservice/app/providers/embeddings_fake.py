from logging import getLogger

from langchain_community.embeddings import FakeEmbeddings
from langchain_core.embeddings import Embeddings

from app.core.registry import register

logger = getLogger(__name__)


@register("embeddings", "fake")
class FakeEmbeddingsProvider:
    def __init__(self, size: int = 384, **kwargs):
        self.size = size
        logger.info("Fake embeddings provider: size=%d (modo demo)", size)

    def get(self) -> Embeddings:
        return FakeEmbeddings(size=self.size)
