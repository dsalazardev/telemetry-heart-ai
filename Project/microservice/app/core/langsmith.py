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
            logger.info("LangSmith conectado: proyecto %s", _client._project_name if hasattr(_client, "_project_name") else "default")
        except Exception as e:
            logger.warning("LangSmith no disponible: %s", e)
    return _client


def trace_node(node_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            client = get_client()
            if client is None:
                return await func(*args, **kwargs)

            state = args[-1] if args else {}
            run = RunTree(
                name=node_name,
                run_type="chain",
                inputs={
                    "state_keys": list(state.keys()) if isinstance(state, dict) else [],
                    "node": node_name,
                },
                client=client,
            )
            try:
                result = await func(*args, **kwargs)
                output_keys = list(result.keys()) if isinstance(result, dict) else ["result"]
                run.end(outputs={"output_keys": output_keys, "node": node_name})
                run.post()
                return result
            except Exception as e:
                run.end(error=str(e))
                run.post()
                raise
        return wrapper
    return decorator
