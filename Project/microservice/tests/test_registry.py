from app.core.registry import ProviderRegistry, registry, register


def test_registry_register_and_create():
    r = ProviderRegistry()

    @register("test", "dummy")
    class DummyProvider:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def get(self):
            return self.kwargs

    # Since @register uses the global registry, not `r`
    r.register("test", "my_provider", DummyProvider)
    instance = r.create("test", "my_provider", foo="bar")
    assert instance.get() == {"foo": "bar"}


def test_registry_available():
    assert "llm" in registry
    assert "embeddings" in registry
    assert "openai" in registry["llm"]
    assert "fake" in registry["embeddings"]


def test_registry_missing_provider():
    try:
        registry.create("llm", "nonexistent")
        assert False, "Should raise KeyError"
    except KeyError:
        pass
