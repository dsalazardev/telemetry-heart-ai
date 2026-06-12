from logging import getLogger

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from app.core.registry import register

logger = getLogger(__name__)


@register("llm", "lmstudio")
class LMStudioProvider:
    def __init__(self, model: str = "default", base_url: str = "http://localhost:1234/v1",
                 temperature: float = 0.0, timeout: int = 30, **kwargs):
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.timeout = timeout
        logger.info("LM Studio provider: url=%s model=%s", base_url, model)

    def get(self) -> BaseChatModel:
        return ChatOpenAI(
            model=self.model,
            base_url=self.base_url,
            api_key="lm-studio",
            temperature=self.temperature,
            timeout=self.timeout,
        )
