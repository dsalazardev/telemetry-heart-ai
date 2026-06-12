from logging import getLogger

from langsmith import Client

logger = getLogger(__name__)

_client: Client | None = None


def get_client() -> Client | None:
    global _client
    if _client is None:
        try:
            _client = Client()
            logger.info("LangSmith conectado: proyecto %s",
                        _client._project_name if hasattr(_client, "_project_name") else "default")
        except Exception as e:
            logger.warning("LangSmith no disponible: %s", e)
    return _client
