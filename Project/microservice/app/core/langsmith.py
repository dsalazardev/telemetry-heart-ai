from logging import getLogger
from functools import wraps

from langsmith import Client
from langsmith.run_trees import RunTree

logger = getLogger(__name__)

_client: Client | None = None


def get_client() -> Client | None:
    global _client
    if _client is None:
        try:
            _client = Client()
        except Exception as e:
            logger.warning("LangSmith no disponible: %s", e)
    return _client


def trace_node(node_name: str):
    """Decorator que envuelve un nodo LangGraph con tracing LangSmith."""
    def decorator(func):
        @wraps(func)
        async def wrapper(state, **kwargs):
            client = get_client()
            if client is None:
                return await func(state, **kwargs)

            run = RunTree(
                name=node_name,
                run_type="chain",
                inputs={"state_keys": list(state.keys())},
            )
            try:
                result = await func(state, **kwargs)
                run.end(outputs=result)
                run.post()
                return result
            except Exception as e:
                run.end(error=str(e))
                run.post()
                raise
        return wrapper
    return decorator
