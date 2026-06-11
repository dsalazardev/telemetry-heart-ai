from typing import List, Dict, Optional
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import InMemorySaver
from app.core.settings import settings
from app.services.predictor_service import PredictorService
from app.services.rag_service import RAGService

# Initialize services
predictor = PredictorService()
rag = RAGService()

@tool
def predict_cardiac_risk(features: List[float]) -> str:
    """Predict cardiac risk from 13 features. Input: list of 13 floats [age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal]"""
    try:
        result = predictor.predict(features)
        return f"Riesgo {result['clasificacion']}: {result['probabilidad']:.1%}. {result['explicacionClinica']}"
    except Exception as e:
        return f"Error en predicción: {str(e)}"

@tool
def evaluate_triage(patient_data: Dict) -> str:
    """Evaluate triage priority for a patient. Input: dict with patient info"""
    risk_level = patient_data.get("risk_level", "desconocido")
    return f"Evaluación de triaje: Prioridad {risk_level.upper()}. Requiere atención médica."

@tool
def generate_document(patient_id: int, doc_type: str) -> str:
    """Generate a clinical document. Input: patient_id (int), doc_type (str)"""
    return f"Documento {doc_type} generado para paciente {patient_id}."

@tool
def search_knowledge(query: str) -> str:
    """Search clinical knowledge base. Input: query (str)"""
    try:
        results = rag.query(query, n_results=3)
        if results:
            texts = [r["content"] for r in results]
            return "\n\n".join(texts)
        return "No se encontraron resultados en la base de conocimiento."
    except Exception as e:
        return f"Error en búsqueda: {str(e)}"

class AgentService:
    def __init__(self):
        self.tools = [
            predict_cardiac_risk,
            evaluate_triage,
            generate_document,
            search_knowledge
        ]
        self.agent = None
        self.memory = None
        self._init_agent()
    
    def _init_agent(self):
        """Initialize LangChain agent with create_agent"""
        try:
            # LLM
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.1
            )
            
            # Prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Eres un asistente médico especializado en cardiología. Ayudas a médicos a evaluar riesgos cardiovasculares y a interpretar resultados de telemetría."),
                ("human", "{input}"),
            ])
            
            # Memory
            self.memory = InMemorySaver()
            
            # Create agent
            self.agent = create_agent(
                llm,
                self.tools,
                prompt=prompt,
                checkpointer=self.memory
            )
            print("[OK] LangChain agent initialized with create_agent()")
        except Exception as e:
            print(f"[WARN] Agent initialization error: {e}")
            self.agent = None
    
    def query(self, question: str, session_id: str = "default") -> Dict:
        """Query the agent with a question"""
        if not self.agent:
            return {
                "response": "Agent not initialized. Please check OPENAI_API_KEY.",
                "tool_used": "none",
                "confidence": 0.0
            }
        
        try:
            result = self.agent.invoke(
                {"input": question},
                config={"configurable": {"thread_id": session_id}}
            )
            
            return {
                "response": result.get("output", "No response"),
                "tool_used": result.get("tool_calls", [{}])[0].get("name", "none") if result.get("tool_calls") else "none",
                "confidence": 0.8  # Simplified
            }
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "tool_used": "none",
                "confidence": 0.0
            }
    
    def get_memory(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        return []
