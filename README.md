#  Asistente Virtual de Ciberseguridad con RAG

Asistente virtual inteligente capaz de responder preguntas sobre ciberseguridad consultando una colección de libros en formato PDF, desarrollado como proyecto universitario de Inteligencia Artificial.

##  Descripción

El sistema utiliza una arquitectura **RAG (Retrieval-Augmented Generation)** que permite:
- Consultar documentos PDF antes de generar una respuesta
- Recuperar fragmentos relevantes mediante búsqueda semántica
- Generar respuestas fundamentadas usando DeepSeek AI
- Mostrar las fuentes y páginas consultadas en cada respuesta

El asistente **no sustituye** el criterio de un profesional calificado en ciberseguridad.


##  Arquitectura
```text
┌─────────────────────┐
│ Usuario             │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Interfaz Reflex     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ FastAPI :8001       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Embeddings          │
│ sentence-transform. │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ ChromaDB            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ DeepSeek AI         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Respuesta + Fuentes │
└─────────────────────┘
```

##  Stack Tecnológico

| Tecnología | Uso |
|---|---|
| Python 3.14 | Lenguaje principal |
| Reflex | Interfaz web interactiva |
| FastAPI | API REST del backend |
| Uvicorn | Servidor web del backend |
| ChromaDB | Base de datos vectorial |
| sentence-transformers | Generación de embeddings |
| pypdf | Extracción de texto de PDFs |
| DeepSeek API | Generación de respuestas con IA |
| SQLite | Historial persistente de consultas |
| python-dotenv | Gestión de variables de entorno |
| httpx | Comunicación Reflex → FastAPI |

##  Estructura del Proyecto

```text
rag_ciberseguridad/
├── documentos/              # 7 libros PDF de ciberseguridad
├── rag_ciberseguridad/
│   └── rag_ciberseguridad.py # Frontend Reflex
├── main.py                  # Backend FastAPI
├── rag_engine.py            # Motor RAG + BD SQLite
├── requirements.txt         # Dependencias
├── rxconfig.py              # Configuración Reflex
└── .env                     # API keys (no incluido)
```

### 1. Crear entorno virtual
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
Crea un archivo `.env` en la raíz:

DEEPSEEK_API_KEY="tu_api_key_aqui"

### 4 Agregar los PDFs
Coloca tus libros PDF dentro de la carpeta `documentos/`

### 5. Ejecutar el proyecto
Abre **dos terminales**:

**Terminal 1 — Backend FastAPI:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 — Frontend Reflex:**
```bash
reflex run
```

### 6. Abrir en el navegador

##  Uso de la aplicación

1. Presiona **  Cargar PDFs** y espera el ✅
2. Escribe tu pregunta en el campo de texto
3. Presiona **Enviar**
4. La respuesta aparece con las **fuentes y páginas** consultadas
5. El historial se guarda automáticamente en la base de datos

##  Documentos incluidos

- Libro 01 — Dialnet Ciberseguridad
- Libro 02 — Dialnet Ciberseguridad Enfocada en el Futuro Digital
- Libro 03 — Dialnet Importancia de la Ciberseguridad en la Investigación
- Libro 04 — La Ciberseguridad en el Mundo Contemporáneo
- Libro 05 — Dialnet Ciberseguridad en los Sistemas de Información
- Libro 06 — Fortalecimiento de la Ciberseguridad en Entornos Académicos
- Libro 07 — Libro Blanco de Ciberseguridad

## ✅ Requerimientos Funcionales Implementados

- RF-01 ✅ 7 libros PDF organizados en carpeta documentos/
- RF-02 ✅ Extracción de texto con pypdf página por página
- RF-03 ✅ División en fragmentos con solapamiento de 100 palabras
- RF-04 ✅ Embeddings con sentence-transformers
- RF-05 ✅ Almacenamiento en ChromaDB con metadatos completos
- RF-06 ✅ Consulta en lenguaje natural desde Reflex
- RF-07 ✅ Recuperación de 5 fragmentos relevantes por consulta
- RF-08 ✅ Generación de respuestas con DeepSeek AI
- RF-09 ✅ Fuentes con nombre del libro y número de página
- RF-10 ✅ Historial de consultas en sesión y BD SQLite
- RF-11 ✅ Mensaje de alcance y limitaciones visible
- RF-12 ✅ Manejo de respuestas insuficientes
- RF-13 ✅ Indicador de procesamiento
- RF-14 ✅ Validación de preguntas vacías
- RF-15 ✅ Manejo de errores técnicos

