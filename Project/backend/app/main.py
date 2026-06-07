from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import create_db_and_tables
from app.routers import auth, pacientes, medicos, triajes, alertas, telemetria, eventos, patologias, dispositivos


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(title="Triaje Cardiovascular IoT", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(pacientes.router, prefix="/pacientes", tags=["pacientes"])
app.include_router(medicos.router, prefix="/medicos", tags=["medicos"])
app.include_router(triajes.router, prefix="/triajes", tags=["triajes"])
app.include_router(alertas.router, prefix="/alertas", tags=["alertas"])
app.include_router(telemetria.router, prefix="/telemetria", tags=["telemetria"])
app.include_router(eventos.router, prefix="/eventos", tags=["eventos"])
app.include_router(patologias.router, prefix="/patologias", tags=["patologias"])
app.include_router(dispositivos.router, prefix="/dispositivos", tags=["dispositivos"])


@app.get("/")
async def root():
    return {}


@app.get("/health")
async def health():
    return {"status": "ok"}
