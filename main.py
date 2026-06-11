from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_engine import cargar_pdfs_en_bd, hacer_pregunta, obtener_historial_bd

app = FastAPI(title="RAG Ciberseguridad API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PreguntaRequest(BaseModel):
    pregunta: str


@app.get("/")
def root():
    return {"mensaje": "API RAG Ciberseguridad funcionando"}


@app.post("/cargar")
def cargar():
    resultado = cargar_pdfs_en_bd()
    return {"resultado": resultado}


@app.post("/consultar")
def consultar(request: PreguntaRequest):
    if not request.pregunta.strip():
        return {
            "respuesta": "⚠️ Debe escribir una pregunta antes de realizar la consulta.",
            "fuentes": [],
            "timestamp": ""
        }
    return hacer_pregunta(request.pregunta)


@app.get("/historial")
def historial():
    return {"historial": obtener_historial_bd(50)}