"""
LLM y Embedding providers con auto-registro en ProviderRegistry.

Para agregar un provider:
  1. Crear archivo en app/providers/
  2. Decorar la clase con @register("llm", "nombre") o @register("embeddings", "nombre")
  3. Importar el módulo aquí o en app/models/__init__.py
"""

from app.providers import llm_openai
from app.providers import llm_lmstudio
from app.providers import embeddings_openai
from app.providers import embeddings_fake
from app.providers import embeddings_huggingface
