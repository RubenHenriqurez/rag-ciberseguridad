import reflex as rx
from pydantic import BaseModel as Base
import httpx

FASTAPI_URL = "http://localhost:8001"

BG_DARK    = "#0F1117"
BG_PANEL   = "#161B27"
BG_CARD    = "#1E2535"
BG_INPUT   = "#252D3D"
BORDER     = "#2E3A50"
ACCENT     = "#00C9A7"
USER_COLOR = "#F59E0B"
IA_COLOR   = "#00C9A7"
TEXT_MAIN  = "#E8EDF5"
TEXT_SUB   = "#8892A4"
TEXT_DIM   = "#4A5568"
DANGER     = "#EF4444"
SUCCESS    = "#10B981"


class Fuente(Base):
    archivo: str = ""
    pagina: int = 0

class Mensaje(Base):
    rol: str = ""
    texto: str = ""
    fuentes: list[Fuente] = []
    timestamp: str = ""

class HistorialItem(Base):
    pregunta: str = ""
    respuesta: str = ""
    fuentes: list[Fuente] = []
    timestamp: str = ""

class State(rx.State):
    pregunta: str = ""
    estado_carga: str = ""
    cargando: bool = False
    pdfs_listos: bool = False
    historial: list[Mensaje] = []
    mostrar_historial_bd: bool = False
    historial_bd: list[HistorialItem] = []

    def cargar_pdfs(self):
        self.cargando = True
        self.estado_carga = "⏳ Indexando documentos..."
        yield
        try:
            r = httpx.post(f"{FASTAPI_URL}/cargar", timeout=120)
            resultado = r.json().get("resultado", "❌ Sin respuesta del servidor")
        except Exception as e:
            resultado = f"❌ No fue posible conectar con el servidor: {str(e)}"
        self.estado_carga = resultado
        self.pdfs_listos = "✅" in resultado
        self.cargando = False

    def enviar_pregunta(self):
        pregunta_limpia = self.pregunta.strip()
        if not pregunta_limpia:
            self.historial = self.historial + [
                Mensaje(rol="ia", texto="⚠️ Debe escribir una pregunta antes de realizar la consulta.", fuentes=[], timestamp="")
            ]
            return
        if not self.pdfs_listos:
            self.historial = self.historial + [
                Mensaje(rol="ia", texto="⚠️ Primero carga los PDFs usando el botón del panel izquierdo.", fuentes=[], timestamp="")
            ]
            return
        self.cargando = True
        self.historial = self.historial + [
            Mensaje(rol="usuario", texto=pregunta_limpia, fuentes=[], timestamp="")
        ]
        self.pregunta = ""
        yield
        try:
            r = httpx.post(
                f"{FASTAPI_URL}/consultar",
                json={"pregunta": pregunta_limpia},
                timeout=60
            )
            data = r.json()
            respuesta = data.get("respuesta", "❌ Sin respuesta")
            fuentes_raw = data.get("fuentes", [])
            timestamp = data.get("timestamp", "")
            fuentes = [Fuente(archivo=f["archivo"], pagina=f["pagina"]) for f in fuentes_raw]
        except Exception as e:
            respuesta = f"❌ No fue posible conectar con el servidor: {str(e)}"
            fuentes = []
            timestamp = ""
        self.historial = self.historial + [
            Mensaje(rol="ia", texto=respuesta, fuentes=fuentes, timestamp=timestamp)
        ]
        self.cargando = False

    def set_pregunta(self, valor: str):
        self.pregunta = valor

    def limpiar_chat(self):
        self.historial = []

    def toggle_historial_bd(self):
        self.mostrar_historial_bd = not self.mostrar_historial_bd
        if self.mostrar_historial_bd:
            try:
                r = httpx.get(f"{FASTAPI_URL}/historial", timeout=10)
                items = r.json().get("historial", [])
                self.historial_bd = [
                    HistorialItem(
                        pregunta=i["pregunta"],
                        respuesta=i["respuesta"],
                        fuentes=[Fuente(archivo=f["archivo"], pagina=f["pagina"]) for f in i.get("fuentes", [])],
                        timestamp=i["timestamp"]
                    )
                    for i in items
                ]
            except Exception:
                self.historial_bd = []


def fuente_tag(fuente: Fuente) -> rx.Component:
    return rx.box(
        rx.text(
            "📄 ",
            fuente.archivo,
            " — Página ",
            fuente.pagina.to_string(),
            font_size="0.75em",
            color=ACCENT,
        ),
        background="rgba(0,201,167,0.08)",
        border="1px solid rgba(0,201,167,0.2)",
        border_radius="6px",
        padding="4px 10px",
        margin_right="6px",
        margin_top="6px",
        display="inline-block",
    )


def burbuja(msg: Mensaje) -> rx.Component:
    es_usuario = msg.rol == "usuario"
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(
                    rx.cond(es_usuario, "U", "AI"),
                    font_size="0.7em",
                    font_weight="800",
                    color=rx.cond(es_usuario, USER_COLOR, IA_COLOR),
                ),
                width="34px",
                height="34px",
                border_radius="8px",
                background=rx.cond(
                    es_usuario,
                    "rgba(245,158,11,0.12)",
                    "rgba(0,201,167,0.12)"
                ),
                border=rx.cond(
                    es_usuario,
                    "1px solid rgba(245,158,11,0.3)",
                    "1px solid rgba(0,201,167,0.3)"
                ),
                display="flex",
                align_items="center",
                justify_content="center",
                flex_shrink="0",
                margin_right="12px",
                margin_top="2px",
            ),
            rx.box(
                rx.text(
                    rx.cond(es_usuario, "TÚ", "ASISTENTE IA"),
                    font_size="0.68em",
                    font_weight="700",
                    color=rx.cond(es_usuario, USER_COLOR, IA_COLOR),
                    letter_spacing="1.5px",
                    margin_bottom="6px",
                ),
                rx.text(
                    msg.texto,
                    font_size="0.95em",
                    color=TEXT_MAIN,
                    white_space="pre-wrap",
                    line_height="1.8",
                ),
                rx.cond(
                    msg.timestamp != "",
                    rx.text(
                        msg.timestamp,
                        font_size="0.68em",
                        color=TEXT_DIM,
                        margin_top="6px",
                    ),
                ),
                rx.cond(
                    msg.fuentes.length() > 0,
                    rx.box(
                        rx.text(
                            "Fuentes consultadas:",
                            font_size="0.75em",
                            color=TEXT_SUB,
                            margin_top="10px",
                            margin_bottom="4px",
                            font_weight="600",
                        ),
                        rx.foreach(msg.fuentes, fuente_tag),
                    ),
                ),
                flex="1",
            ),
            align_items="flex-start",
        ),
        background=rx.cond(
            es_usuario,
            "rgba(245,158,11,0.05)",
            "rgba(0,201,167,0.04)"
        ),
        border=rx.cond(
            es_usuario,
            "1px solid rgba(245,158,11,0.15)",
            "1px solid rgba(0,201,167,0.12)"
        ),
        border_left=rx.cond(
            es_usuario,
            f"3px solid {USER_COLOR}",
            f"3px solid {IA_COLOR}"
        ),
        padding="16px 18px",
        border_radius="10px",
        margin_bottom="12px",
        width="100%",
    )


def item_historial_bd(item: HistorialItem) -> rx.Component:
    return rx.box(
        rx.text(
            item.timestamp,
            font_size="0.68em",
            color=TEXT_DIM,
            margin_bottom="4px",
        ),
        rx.text(
            "❓ ",
            item.pregunta,
            font_size="0.82em",
            color=USER_COLOR,
            font_weight="600",
            margin_bottom="4px",
            white_space="pre-wrap",
        ),
        rx.text(
            item.respuesta,
            font_size="0.78em",
            color=TEXT_SUB,
            line_height="1.5",
        ),
        background=BG_CARD,
        border="1px solid " + BORDER,
        border_radius="8px",
        padding="12px",
        margin_bottom="8px",
    )


def panel_izquierdo() -> rx.Component:
    return rx.box(
        rx.box(
            rx.text("🛡️", font_size="1.8em"),
            rx.text(
                "CiberRAG",
                font_size="1.1em",
                font_weight="800",
                color=TEXT_MAIN,
                letter_spacing="2px",
            ),
            rx.text(
                "Security Intelligence",
                font_size="0.68em",
                color=ACCENT,
                letter_spacing="2px",
            ),
            padding="20px 16px 16px",
            border_bottom="1px solid " + BORDER,
        ),

        rx.box(
            rx.text(
                "⚠️ AVISO IMPORTANTE",
                font_size="0.65em",
                color="#F59E0B",
                letter_spacing="1.5px",
                font_weight="700",
                margin_bottom="6px",
            ),
            rx.text(
                "Esta herramienta proporciona orientación general basada en documentos cargados. "
                "No sustituye la atención ni el criterio de un profesional calificado en ciberseguridad.",
                font_size="0.75em",
                color=TEXT_SUB,
                line_height="1.5",
            ),
            background="rgba(245,158,11,0.06)",
            border="1px solid rgba(245,158,11,0.2)",
            border_radius="8px",
            padding="12px",
            margin="12px 16px",
        ),

        rx.box(
            rx.text(
                "DOCUMENTOS",
                font_size="0.65em",
                color=TEXT_DIM,
                letter_spacing="2px",
                font_weight="700",
                margin_bottom="10px",
            ),
            rx.button(
                rx.cond(
                    State.cargando,
                    "⏳  Indexando...",
                    rx.cond(State.pdfs_listos, "✅  PDFs Listos", "⚡  Cargar PDFs")
                ),
                on_click=State.cargar_pdfs,
                background=rx.cond(
                    State.pdfs_listos,
                    f"linear-gradient(135deg, {SUCCESS}, #059669)",
                    f"linear-gradient(135deg, {ACCENT}, #00A88A)"
                ),
                color="#0F1117",
                width="100%",
                padding="12px",
                border_radius="8px",
                font_size="0.88em",
                font_weight="700",
                cursor="pointer",
                border="none",
                margin_bottom="10px",
            ),
            rx.cond(
                State.estado_carga != "",
                rx.box(
                    rx.text(
                        State.estado_carga,
                        font_size="0.78em",
                        color=TEXT_SUB,
                        line_height="1.5",
                        white_space="pre-wrap",
                    ),
                    background=BG_CARD,
                    border="1px solid " + BORDER,
                    border_radius="8px",
                    padding="10px 12px",
                ),
            ),
            padding="16px",
            border_bottom="1px solid " + BORDER,
        ),

        rx.box(
            rx.text(
                "GUÍA RÁPIDA",
                font_size="0.65em",
                color=TEXT_DIM,
                letter_spacing="2px",
                font_weight="700",
                margin_bottom="12px",
            ),
            *[
                rx.flex(
                    rx.box(
                        rx.text(str(n), font_size="0.7em", font_weight="800", color=ACCENT),
                        width="22px",
                        height="22px",
                        border_radius="50%",
                        background="rgba(0,201,167,0.12)",
                        border="1px solid rgba(0,201,167,0.3)",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        flex_shrink="0",
                        margin_right="10px",
                    ),
                    rx.text(paso, font_size="0.8em", color=TEXT_SUB, line_height="1.4"),
                    align_items="center",
                    margin_bottom="10px",
                )
                for n, paso in [
                    (1, "Activa el entorno .venv"),
                    (2, "Inicia FastAPI: uvicorn main:app --port 8001"),
                    (3, "Inicia Reflex: reflex run"),
                    (4, "Presiona Cargar PDFs"),
                    (5, "Escribe tu pregunta"),
                ]
            ],
            padding="16px",
            border_bottom="1px solid " + BORDER,
        ),

        rx.box(
            rx.text(
                "BASE DE DATOS",
                font_size="0.65em",
                color=TEXT_DIM,
                letter_spacing="2px",
                font_weight="700",
                margin_bottom="10px",
            ),
            rx.button(
                rx.cond(
                    State.mostrar_historial_bd,
                    "🔼  Ocultar Historial",
                    "🗄️  Ver Preguntas Guardadas"
                ),
                on_click=State.toggle_historial_bd,
                background="transparent",
                color=ACCENT,
                width="100%",
                padding="10px",
                border_radius="8px",
                font_size="0.8em",
                font_weight="600",
                cursor="pointer",
                border=f"1px solid rgba(0,201,167,0.3)",
            ),
            rx.cond(
                State.mostrar_historial_bd,
                rx.box(
                    rx.cond(
                        State.historial_bd.length() == 0,
                        rx.text(
                            "Sin preguntas guardadas aún.",
                            font_size="0.78em",
                            color=TEXT_DIM,
                            margin_top="10px",
                        ),
                        rx.box(
                            rx.foreach(State.historial_bd, item_historial_bd),
                            margin_top="10px",
                            max_height="300px",
                            overflow_y="auto",
                        ),
                    ),
                ),
            ),
            padding="16px",
        ),

        width="270px",
        min_width="250px",
        background=BG_PANEL,
        border_right="1px solid " + BORDER,
        height="100vh",
        overflow_y="auto",
        flex_shrink="0",
    )


def panel_chat() -> rx.Component:
    return rx.flex(
        rx.box(
            rx.flex(
                rx.box(
                    rx.text(
                        "CHAT",
                        font_size="0.65em",
                        color=TEXT_DIM,
                        letter_spacing="3px",
                        font_weight="700",
                    ),
                    rx.text(
                        rx.cond(
                            State.pdfs_listos,
                            "● Documentos indexados — listo para consultas",
                            "○ Carga los PDFs para comenzar",
                        ),
                        font_size="0.78em",
                        color=rx.cond(State.pdfs_listos, ACCENT, TEXT_DIM),
                    ),
                ),
                rx.button(
                    "🗑️ Limpiar",
                    on_click=State.limpiar_chat,
                    background="transparent",
                    color=TEXT_DIM,
                    border=f"1px solid {BORDER}",
                    border_radius="6px",
                    padding="6px 12px",
                    font_size="0.78em",
                    cursor="pointer",
                ),
                justify_content="space-between",
                align_items="center",
            ),
            padding="14px 20px",
            border_bottom="1px solid " + BORDER,
            background=BG_PANEL,
        ),

        rx.box(
            rx.cond(
                State.historial.length() == 0,
                rx.box(
                    rx.text("🛡️", font_size="3em", margin_bottom="16px"),
                    rx.text(
                        "Bienvenido a CiberRAG",
                        font_size="1.3em",
                        font_weight="700",
                        color=TEXT_MAIN,
                        margin_bottom="8px",
                    ),
                    rx.text(
                        "Asistente virtual de ciberseguridad basado en documentos PDF.",
                        font_size="0.9em",
                        color=TEXT_SUB,
                        text_align="center",
                        line_height="1.7",
                    ),
                    rx.box(
                        rx.text(
                            "⚠️ Esta herramienta proporciona orientación general basada en los documentos cargados. "
                            "No sustituye el criterio de un profesional calificado en ciberseguridad.",
                            font_size="0.8em",
                            color="#F59E0B",
                            text_align="center",
                            line_height="1.6",
                        ),
                        background="rgba(245,158,11,0.06)",
                        border="1px solid rgba(245,158,11,0.2)",
                        border_radius="8px",
                        padding="12px 16px",
                        margin_top="16px",
                        max_width="500px",
                    ),
                    display="flex",
                    flex_direction="column",
                    align_items="center",
                    justify_content="center",
                    height="100%",
                ),
                rx.box(
                    rx.foreach(State.historial, burbuja),
                    rx.cond(
                        State.cargando,
                        rx.flex(
                            rx.box(
                                rx.text("AI", font_size="0.7em", font_weight="800", color=IA_COLOR),
                                width="34px",
                                height="34px",
                                border_radius="8px",
                                background="rgba(0,201,167,0.12)",
                                border="1px solid rgba(0,201,167,0.3)",
                                display="flex",
                                align_items="center",
                                justify_content="center",
                                flex_shrink="0",
                                margin_right="12px",
                            ),
                            rx.text(
                                "Buscando información en los documentos...",
                                font_size="0.88em",
                                color=TEXT_SUB,
                                font_style="italic",
                            ),
                            align_items="center",
                            padding="12px 0",
                        ),
                    ),
                    padding_bottom="20px",
                ),
            ),
            flex="1",
            overflow_y="auto",
            padding="20px 24px",
            background=BG_DARK,
        ),

        rx.box(
            rx.flex(
                rx.text_area(
                    placeholder="Escribe tu pregunta sobre ciberseguridad...\n(Presiona el botón Enviar)",
                    value=State.pregunta,
                    on_change=State.set_pregunta,
                    flex="1",
                    min_height="90px",
                    max_height="200px",
                    padding="14px 16px",
                    border=f"1px solid {BORDER}",
                    border_radius="10px",
                    font_size="0.95em",
                    color=TEXT_MAIN,
                    background=BG_INPUT,
                    resize="vertical",
                    line_height="1.6",
                    _focus={
                        "border_color": ACCENT,
                        "outline": "none",
                        "box_shadow": "0 0 0 2px rgba(0,201,167,0.15)",
                    },
                    _placeholder={"color": TEXT_DIM},
                ),
                rx.flex(
                    rx.button(
                        "Enviar ➤",
                        on_click=State.enviar_pregunta,
                        background=f"linear-gradient(135deg, {ACCENT}, #00A88A)",
                        color="#0F1117",
                        padding="14px 24px",
                        border_radius="10px",
                        font_size="0.9em",
                        font_weight="700",
                        cursor="pointer",
                        border="none",
                        is_disabled=State.cargando,
                        white_space="nowrap",
                    ),
                    flex_direction="column",
                    align_items="flex-end",
                    justify_content="flex_end",
                    margin_left="12px",
                ),
                align_items="flex-end",
            ),
            rx.text(
                rx.cond(
                    State.cargando,
                    "🔍 Procesando consulta...",
                    rx.cond(
                        State.pdfs_listos,
                        "✅ PDFs indexados y listos",
                        "⚠️ Carga los PDFs antes de preguntar",
                    )
                ),
                font_size="0.72em",
                color=rx.cond(
                    State.cargando,
                    ACCENT,
                    rx.cond(State.pdfs_listos, TEXT_DIM, USER_COLOR)
                ),
                margin_top="8px",
            ),
            padding="16px 20px 20px",
            background=BG_PANEL,
            border_top="1px solid " + BORDER,
        ),

        direction="column",
        flex="1",
        height="100vh",
        overflow="hidden",
    )


def index() -> rx.Component:
    return rx.flex(
        panel_izquierdo(),
        panel_chat(),
        direction="row",
        height="100vh",
        overflow="hidden",
        background=BG_DARK,
        font_family="'Inter', 'Segoe UI', system-ui, sans-serif",
    )


app = rx.App(
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
    ]
)
app.add_page(index)