from logging import getLogger

logger = getLogger(__name__)


class ProviderRegistry(dict):
    def register(self, category: str, name: str, cls: type):
        self.setdefault(category, {})[name] = cls
        logger.debug("Registrado %s/%s -> %s", category, name, cls.__name__)

    def create(self, category: str, name: str, **kwargs):
        providers = self.get(category, {})
        if name not in providers:
            raise KeyError(f"Provider '{name}' no registrado en categoría '{category}'. "
                           f"Disponibles: {list(providers.keys())}")
        return providers[name](**kwargs)

    def available(self, category: str | None = None) -> dict:
        if category:
            return dict(self.get(category, {}))
        return {cat: dict(provs) for cat, provs in self.items()}


registry = ProviderRegistry()


def register(category: str, name: str):
    def decorator(cls):
        registry.register(category, name, cls)
        return cls
    return decorator
