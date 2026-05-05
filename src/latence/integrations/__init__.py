"""Drop-in adapters for popular RAG / agent frameworks.

Each adapter is in its own module so importing the integration package
never imports a framework you don't have installed:

- ``latence.integrations.langchain`` -> ``LatenceTraceCallback``
- ``latence.integrations.llama_index`` -> ``LatenceTracePostProcessor``
- ``latence.integrations.openai`` -> ``wrap_openai_chat``

Each module raises a helpful ``ImportError`` at import time if its
optional extras are missing, so users see a clear "install
``latence[langchain]``" message instead of a cryptic
attribute error halfway through a chain run.
"""

__all__: tuple[str, ...] = ()
