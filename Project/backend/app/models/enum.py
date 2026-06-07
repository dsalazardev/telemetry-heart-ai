from enum import Enum


class NivelUrgencia(str, Enum):
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"


class TipoEvento(str, Enum):
    ANOMALIA_CRITICA = "anomalia_critica"
    REPORTE_PERIODICO = "reporte_periodico"
    UMBRAL_SUPERADO = "umbral_superado"


class EstadoProcesamiento(str, Enum):
    RECIBIDA = "recibida"
    VALIDADA = "validada"
    ENRIQUECIDA = "enriquecida"
    PROCESADA = "procesada"
    ERROR = "error"
    TIMEOUT_MICROSERVICIO = "timeout_microservicio"
