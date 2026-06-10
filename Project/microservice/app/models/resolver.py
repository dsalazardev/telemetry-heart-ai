from logging import getLogger

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from app.core.registry import registry
from app.providers import *  # noqa: F401, F403 — trigger @register decorators

logger = getLogger(__name__)


def create_llm(settings) -> BaseChatModel:
    provider_name = settings.llm_provider
    try:
        provider_cls = registry.create("llm", provider_name,
                                       model=settings.llm_model,
                                       temperature=settings.llm_temperature,
                                       timeout=settings.llm_timeout,
                                       base_url=getattr(settings, "llm_base_url", None))
        return provider_cls.get()
    except KeyError:
        logger.warning("LLM provider '%s' no registrado, usando OpenAI fallback", provider_name)
        return registry.create("llm", "openai",
                               model=settings.llm_model,
                               temperature=settings.llm_temperature,
                               timeout=settings.llm_timeout).get()


def create_embeddings(settings) -> Embeddings:
    provider_name = settings.embedding_provider
    try:
        provider_cls = registry.create("embeddings", provider_name,
                                       model=settings.embedding_model,
                                       size=settings.embedding_dimensions)
        return provider_cls.get()
    except KeyError:
        logger.warning("Embeddings provider '%s' no registrado, usando fake", provider_name)
        return registry.create("embeddings", "fake",
                               size=settings.embedding_dimensions).get()
