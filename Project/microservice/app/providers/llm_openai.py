from logging import getLogger

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from app.core.registry import register

logger = getLogger(__name__)


@register("llm", "openai")
class OpenAIProvider:
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.0, timeout: int = 30, **kwargs):
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        logger.info("OpenAI provider: model=%s", model)

    def get(self) -> BaseChatModel:
        return ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            timeout=self.timeout,
        )
