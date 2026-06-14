"""LangChain @tool registry para el microservicio.

Herramientas disponibles para los agentes LangGraph. Sólo `pso_tools` por
ahora: el PSO se ejecuta exclusivamente vía `optimize_triage_priority_tool`.
"""
from app.tools.pso_tools import optimize_triage_priority_tool

ALL_TOOLS = [optimize_triage_priority_tool]

__all__ = ["ALL_TOOLS", "optimize_triage_priority_tool"]
