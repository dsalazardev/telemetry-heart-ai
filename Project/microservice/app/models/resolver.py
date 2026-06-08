from logging import getLogger

from langchain.chat_models import init_chat_model
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

logger = getLogger(__name__)


def create_llm(settings) -> BaseChatModel:
    if settings.llm_provider == "lmstudio":
        logger.info("Usando LM Studio en %s", settings.llm_base_url)
        return ChatOpenAI(
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            api_key="lm-studio",
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout,
        )

    logger.info("Usando OpenAI: %s", settings.llm_model)
    return ChatOpenAI(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        timeout=settings.llm_timeout,
    )


def create_embeddings(settings) -> Embeddings:
    if settings.embedding_provider == "openai":
        logger.info("Usando OpenAI embeddings: %s", settings.embedding_model)
        return OpenAIEmbeddings(model=settings.embedding_model)

    if settings.embedding_provider == "huggingface":
        logger.info("Usando HuggingFace embeddings: %s", settings.embedding_model)
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            encode_kwargs={"normalize_embeddings": True},
        )

    logger.info("Usando FakeEmbeddings (modo demo)")
    from langchain_community.embeddings import FakeEmbeddings
    return FakeEmbeddings(size=settings.embedding_dimensions)
