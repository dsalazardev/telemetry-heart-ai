from abc import ABC, abstractmethod
from typing import Any

from fastapi import APIRouter


class BaseAgent(ABC):
    name: str = ""

    @abstractmethod
    async def run(self, **kwargs) -> Any:
        ...

    @property
    def router(self) -> APIRouter | None:
        return None
