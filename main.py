import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from google import genai
from dotenv import load_dotenv

load_dotenv()

# ── Gemini setup ──────────────────────────────────────────────────────────────
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY no está configurada en las variables de entorno.")

client = genai.Client(api_key=api_key)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="FinSense API",
    description=(
        "API REST para análisis inteligente de productos financieros con IA generativa (Gemini). "
        "Recibe texto libre sobre un producto financiero y devuelve categoría, nivel de riesgo, "
        "resumen, recomendación y alertas clave."
    ),
    version="1.0.0",
    contact={"name": "Catalina Álvarez", "url": "https://github.com/catalvarezs"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Schemas ───────────────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    texto: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Descripción o texto del producto financiero a analizar.",
        examples=["Seguro de auto con cobertura total, deducible $200, prima mensual $45."]
    )
    contexto: Optional[str] = Field(
        default=None,
        description="Contexto opcional: 'seguros', 'credito', 'inversion', 'ahorro'.",
        examples=["seguros"]
    )

class AnalysisResult(BaseModel):
    categoria: str = Field(description="Tipo de producto financiero detectado.")
    nivel_riesgo: int = Field(ge=1, le=10, description="Nivel de riesgo del 1 (bajo) al 10 (muy alto).")
    resumen: str = Field(description="Resumen claro en 1-2 oraciones de qué ofrece el producto.")
    recomendacion: str = Field(description="Recomendación personalizada sobre si conviene y para quién.")
    alertas: list[str] = Field(description="Puntos críticos o advertencias clave a considerar.")
    publico_objetivo: str = Field(description="Perfil ideal de usuario para este producto.")

SYSTEM_PROMPT = """Eres un analista financiero senior especializado en productos del mercado LATAM 
(seguros, créditos, inversiones, ahorro). Tu análisis es preciso, neutral y orientado a proteger 
al consumidor. Siempre detectas riesgos ocultos, letra chica y condiciones desventajosas."""

# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def health_check():
    """Verifica que la API está operativa."""
    return {"status": "ok", "service": "FinSense API", "version": "1.0.0"}


@app.post("/analyze", response_model=AnalysisResult, tags=["Análisis"])
async def analyze_product(req: AnalyzeRequest):
    """
    Analiza un producto financiero con IA generativa (Gemini).

    - **texto**: descripción del producto (mín. 10 caracteres)
    - **contexto**: tipo de producto para mejorar precisión (opcional)

    Retorna: categoría, riesgo (1-10), resumen, recomendación, alertas y público objetivo.
    """
    prompt = f"""{SYSTEM_PROMPT}

Analiza este producto financiero y responde ÚNICAMENTE con un JSON válido, sin markdown, sin texto adicional.

PRODUCTO: {req.texto}
{f"CONTEXTO: {req.contexto}" if req.contexto else ""}

Responde con exactamente este JSON:
{{
  "categoria": "tipo de producto (ej: seguro_auto, credito_hipotecario, inversion_fondos, tarjeta_credito, seguro_vida, credito_consumo)",
  "nivel_riesgo": <número entero del 1 al 10>,
  "resumen": "qué ofrece el producto en 1-2 oraciones directas",
  "recomendacion": "para quién conviene y en qué condiciones, en 2-3 oraciones",
  "alertas": ["alerta 1", "alerta 2", "alerta 3"],
  "publico_objetivo": "perfil del usuario ideal para este producto"
}}"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        raw = response.text.strip()

        # Limpiar posibles bloques de código markdown
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1])

        data = json.loads(raw)
        data["nivel_riesgo"] = max(1, min(10, int(data["nivel_riesgo"])))
        return AnalysisResult(**data)

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=422,
            detail=f"La IA devolvió una respuesta en formato inesperado: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/categories", tags=["Referencia"])
def list_categories():
    """Retorna las categorías de productos financieros soportadas."""
    return {
        "categorias": [
            "seguro_auto", "seguro_vida", "seguro_hogar", "seguro_salud",
            "credito_hipotecario", "credito_consumo", "credito_automotriz",
            "inversion_fondos", "inversion_acciones", "ahorro_plazo_fijo",
            "tarjeta_credito", "cuenta_corriente", "otro"
        ]
    }
