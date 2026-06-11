from dotenv import load_dotenv
load_dotenv()

import os
import time
import PyPDF2
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import sqlite3
from datetime import datetime

PDF_FOLDER = "documentos"
COLLECTION_NAME = "ciberseguridad"
DB_PATH = "historial.db"

_embedder = None
_chroma_client = None
_deepseek_client = None


def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("paraphrase-MiniLM-L3-v2")
    return _embedder


def get_chroma():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.Client()
    return _chroma_client


def get_deepseek():
    global _deepseek_client
    if _deepseek_client is None:
        _deepseek_client = OpenAI(
            api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
            base_url="https://api.deepseek.com"
        )
    return _deepseek_client


def extraer_texto_pdf(ruta_pdf: str) -> list:
    """Extrae texto por página, retorna lista de (pagina, texto)"""
    paginas = []
    try:
        with open(ruta_pdf, "rb") as f:
            lector = PyPDF2.PdfReader(f)
            for num_pagina, pagina in enumerate(lector.pages, start=1):
                t = pagina.extract_text()
                if t and t.strip():
                    paginas.append((num_pagina, t))
    except Exception as e:
        print(f"Error leyendo {ruta_pdf}: {e}")
    return paginas


def dividir_en_fragmentos(texto: str, tamano: int = 500, overlap: int = 100) -> list:
    """Divide texto en fragmentos con solapamiento para no perder contexto"""
    palabras = texto.split()
    fragmentos = []
    paso = tamano - overlap
    for i in range(0, len(palabras), paso):
        fragmento = " ".join(palabras[i:i + tamano])
        if len(fragmento.strip()) > 30:
            fragmentos.append(fragmento)
    return fragmentos


def cargar_pdfs_en_bd() -> str:
    try:
        client = get_chroma()
        embedder = get_embedder()

        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

        coleccion = client.create_collection(COLLECTION_NAME)

        if not os.path.exists(PDF_FOLDER):
            os.makedirs(PDF_FOLDER)
            return "⚠️ Carpeta documentos/ creada. Agrega tus 5 PDFs."

        archivos = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]

        if not archivos:
            return "⚠️ No hay PDFs en la carpeta documentos/"

        id_contador = 0
        for archivo in archivos:
            ruta = os.path.join(PDF_FOLDER, archivo)
            print(f"Procesando: {archivo}")
            paginas = extraer_texto_pdf(ruta)
            if not paginas:
                print(f"Sin texto: {archivo}")
                continue
            for num_pagina, texto_pagina in paginas:
                fragmentos = dividir_en_fragmentos(texto_pagina)
                for idx, fragmento in enumerate(fragmentos):
                    embedding = embedder.encode(fragmento).tolist()
                    coleccion.add(
                        documents=[fragmento],
                        embeddings=[embedding],
                        metadatas=[{
                            "fuente": archivo,
                            "pagina": num_pagina,
                            "fragmento_id": f"{archivo}_pagina_{num_pagina}_frag_{idx}"
                        }],
                        ids=[f"doc_{id_contador}"]
                    )
                    id_contador += 1
            print(f"{archivo}: procesado")

        return f"✅ {len(archivos)} PDFs cargados — {id_contador} fragmentos indexados."

    except Exception as e:
        return f"❌ Error cargando PDFs: {str(e)}"


def generar_con_retry(cliente, prompt: str, reintentos: int = 3) -> str:
    for intento in range(reintentos):
        try:
            respuesta = cliente.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Eres un asistente experto en ciberseguridad. "
                            "Responde ÚNICAMENTE basándote en el contexto proporcionado. "
                            "No inventes información. "
                            "Si el contexto no es suficiente, indícalo claramente. "
                            "Responde siempre en español de forma clara y estructurada."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3,
            )
            return respuesta.choices[0].message.content
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate limit" in error_str.lower():
                if intento < reintentos - 1:
                    espera = 15 * (intento + 1)
                    print(f"Rate limit. Esperando {espera}s... (intento {intento+1}/{reintentos})")
                    time.sleep(espera)
                else:
                    return "❌ Límite de API alcanzado. Espera unos minutos e intenta de nuevo."
            else:
                return f"❌ Error al consultar IA: {error_str}"
    return "❌ No se pudo obtener respuesta."


def hacer_pregunta(pregunta: str) -> dict:
    """Retorna dict con respuesta, fuentes y timestamp"""
    try:
        client = get_chroma()
        embedder = get_embedder()
        deepseek = get_deepseek()

        try:
            coleccion = client.get_collection(COLLECTION_NAME)
        except Exception:
            return {
                "respuesta": "⚠️ Primero carga los PDFs.",
                "fuentes": [],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        embedding_pregunta = embedder.encode(pregunta).tolist()
        resultados = coleccion.query(
            query_embeddings=[embedding_pregunta],
            n_results=5
        )

        if not resultados["documents"] or not resultados["documents"][0]:
            return {
                "respuesta": "⚠️ No encontré información suficiente en los libros disponibles para responder con seguridad. Consulte a un profesional o incorpore fuentes adicionales al sistema.",
                "fuentes": [],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        fragmentos = resultados["documents"][0]
        metadatos = resultados["metadatas"][0]
        contexto = "\n\n---\n\n".join(fragmentos)

        # Fuentes con nombre y página
        fuentes_vistas = set()
        fuentes = []
        for m in metadatos:
            clave = f"{m['fuente']}_p{m['pagina']}"
            if clave not in fuentes_vistas:
                fuentes_vistas.add(clave)
                fuentes.append({
                    "archivo": m["fuente"],
                    "pagina": m["pagina"]
                })

        prompt = f"""Contexto extraído de los documentos de ciberseguridad:

{contexto}

Pregunta del usuario: {pregunta}

Responde únicamente usando el contexto proporcionado. 
No inventes información.
Cuando el contexto no sea suficiente, indícalo claramente.
Menciona las fuentes cuando estén disponibles."""

        texto_respuesta = generar_con_retry(deepseek, prompt)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        guardar_pregunta(pregunta, texto_respuesta, fuentes, timestamp)

        return {
            "respuesta": texto_respuesta,
            "fuentes": fuentes,
            "timestamp": timestamp
        }

    except Exception as e:
        return {
            "respuesta": f"❌ Ocurrió un error al procesar la consulta: {str(e)}",
            "fuentes": [],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }


# ── Base de datos SQLite ───────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pregunta TEXT NOT NULL,
            respuesta TEXT NOT NULL,
            fuentes TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def guardar_pregunta(pregunta: str, respuesta: str, fuentes: list, timestamp: str):
    try:
        import json
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO historial (pregunta, respuesta, fuentes, timestamp) VALUES (?, ?, ?, ?)",
            (pregunta, respuesta, json.dumps(fuentes), timestamp)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error guardando en BD: {e}")


def obtener_historial_bd(limite: int = 50) -> list:
    try:
        import json
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT pregunta, respuesta, fuentes, timestamp FROM historial ORDER BY id DESC LIMIT ?",
            (limite,)
        )
        filas = cursor.fetchall()
        conn.close()
        return [
            {
                "pregunta": f[0],
                "respuesta": f[1],
                "fuentes": json.loads(f[2]),
                "timestamp": f[3]
            }
            for f in filas
        ]
    except Exception as e:
        print(f"Error leyendo BD: {e}")
        return []