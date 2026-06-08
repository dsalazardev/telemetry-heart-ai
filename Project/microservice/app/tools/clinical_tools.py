from langchain.tools import tool


def _make_tools(risk_engine, rag):
    @tool
    def predict_risk_tool(payload: dict) -> dict:
        """Calcula el riesgo cardiovascular para un paciente dado.

        Args:
            payload: Diccionario con datos fisiológicos (heart_rate, spo2, systolic_bp, etc.)
        """
        return risk_engine.predict(payload)

    @tool
    def retrieve_guidelines_tool(query: str) -> list[dict]:
        """Recupera fragmentos de guías clínicas relevantes para una consulta.

        Args:
            query: Texto de consulta sobre factores de riesgo o protocolos clínicos
        """
        return rag.retrieve(query)

    return [predict_risk_tool, retrieve_guidelines_tool]
