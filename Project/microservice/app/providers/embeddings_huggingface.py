from logging import getLogger

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

from app.core.registry import register

logger = getLogger(__name__)


@register("embeddings", "huggingface")
class HuggingFaceEmbeddingsProvider:
    def __init__(self, model: str = "sentence-transformers/all-MiniLM-L6-v2", **kwargs):
        self.model = model
        logger.info("HuggingFace embeddings provider: model=%s", model)

    def get(self) -> Embeddings:
        return HuggingFaceEmbeddings(
            model_name=self.model,
            encode_kwargs={"normalize_embeddings": True},
        )
