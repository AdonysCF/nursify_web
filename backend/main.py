from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # <-- Importante
import os

from backend.database import engine, Base
import backend.models

# Routers
from backend.api.casos import router as casos_router
from backend.api.pae import router as pae_router
from backend.api.reportes import router as reportes_router
from backend.api.exportar import router as exportar_router

os.makedirs("storage/indices", exist_ok=True)
os.makedirs("storage/casos_subidos", exist_ok=True)
os.makedirs("storage/reportes_generados", exist_ok=True)
os.makedirs("frontend", exist_ok=True)
os.makedirs("frontend/css", exist_ok=True)
os.makedirs("frontend/js", exist_ok=True)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PAE con IA", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectar las rutas de la API primero
app.include_router(casos_router)
app.include_router(pae_router)
app.include_router(reportes_router)
app.include_router(exportar_router)

# Servir la interfaz web (debe ir al final)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")