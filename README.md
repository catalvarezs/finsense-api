# FinSense API

> API REST para análisis inteligente de productos financieros con IA generativa (Google Gemini).

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Gemini](https://img.shields.io/badge/Powered%20by-Gemini%202.0%20Flash-orange)](https://ai.google.dev)
[![Tests](https://img.shields.io/badge/tests-10%20passing-brightgreen)]()

---

## ¿Qué hace?

FinSense recibe texto libre sobre cualquier producto financiero (seguros, créditos, inversiones) y devuelve un análisis estructurado con:

- **Categoría** detectada automáticamente
- **Nivel de riesgo** del 1 al 10
- **Resumen** claro del producto
- **Recomendación** personalizada
- **Alertas** clave para el consumidor
- **Público objetivo** ideal

```bash
POST /analyze
{
  "texto": "Seguro de auto cobertura total, prima $45/mes, deducible $200, sin cobertura en zonas inundables"
}

→ {
  "categoria": "seguro_auto",
  "nivel_riesgo": 3,
  "resumen": "Seguro de cobertura total con deducible moderado...",
  "recomendacion": "Conveniente para conductores con vehículo de valor medio...",
  "alertas": ["Exclusión en zonas inundables puede ser crítica...", ...],
  "publico_objetivo": "Conductores urbanos con vehículo de uso diario"
}
```

---

## Arquitectura

```
Cliente (curl / frontend / otro servicio)
        │
        │  POST /analyze  { texto, contexto? }
        ▼
┌─────────────────────────────────────────┐
│            FastAPI  (main.py)           │
│                                         │
│  1. Validación Pydantic (texto, rango)  │
│  2. Construcción de prompt dinámico     │
│  3. Llamada a Gemini 2.0 Flash          │
│  4. Parsing + validación de JSON        │
│  5. Clampeo de nivel_riesgo [1-10]      │
│  6. Response model AnalysisResult       │
└─────────────────────────────────────────┘
        │
        │  generate_content(prompt)
        ▼
┌─────────────────────────────────────────┐
│         Google Gemini 2.0 Flash         │
│                                         │
│  - Rol: analista financiero LATAM       │
│  - Output: JSON estructurado            │
│  - Sin dependencias externas de datos   │
└─────────────────────────────────────────┘
```

### Decisiones técnicas

**¿Por qué FastAPI?**
Tipado nativo con Pydantic, documentación automática en `/docs` (Swagger UI + ReDoc), rendimiento asíncrono comparable a Node.js, y validación de request/response con un solo modelo.

**¿Por qué Gemini 2.0 Flash?**
Mejor relación velocidad/costo para análisis de texto corto a medio. Flash tiene latencia ~1s vs ~3s de Pro, suficiente para este caso. Además, el JSON output de Gemini es más limpio que el de GPT-4 con prompts estructurados en español.

**¿Por qué JSON vía prompt y no function calling?**
El JSON schema vía prompt permite iterar el formato sin cambiar código. El modelo respeta la estructura con alta fidelidad cuando el prompt es explícito. Se incluye limpieza de markdown como fallback por si el modelo incluye bloques de código.

**¿Por qué Railway?**
Deploy desde GitHub en 1 click, variables de entorno seguras, tier gratuito con $5/mes de crédito, sin cold starts problemáticos para una API de bajo tráfico.

---

## Correr en local

### 1. Clonar e instalar
```bash
git clone https://github.com/catalvarezs/finsense-api
cd finsense-api

python -m venv venv
source venv/bin/activate      # Mac/Linux
# venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### 2. Configurar API key
```bash
cp .env.example .env
# Editar .env y pegar tu GEMINI_API_KEY
# Obtenerla en: https://aistudio.google.com/app/apikey
```

### 3. Ejecutar
```bash
uvicorn main:app --reload
```

La API corre en `http://localhost:8000`. Documentación interactiva en `http://localhost:8000/docs`.

### 4. Probar
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"texto": "Crédito de consumo a 36 meses, tasa 18% anual, sin garantía, aprobación en 24h"}'
```

---

## Tests

```bash
pytest tests/ -v
```

Cobertura de tests incluye:
- Health check
- Estructura completa del response
- Validación de nivel_riesgo dentro del rango [1, 10]
- Clamping de valores fuera de rango
- Rechazo de texto vacío o muy corto
- Contexto opcional
- Endpoint `/categories`
- Documentación `/docs`

---

## Deploy en Railway

1. Subir el repo a GitHub
2. Ir a [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Seleccionar el repositorio
4. En Variables de entorno: agregar `GEMINI_API_KEY`
5. Railway detecta el `Procfile` automáticamente y deploya

La API queda disponible en una URL tipo `finsense-api-production.up.railway.app`.

---

## Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `POST` | `/analyze` | Análisis de producto financiero |
| `GET` | `/categories` | Lista de categorías soportadas |
| `GET` | `/docs` | Swagger UI interactivo |
| `GET` | `/redoc` | Documentación ReDoc |

---

## Autor

Catalina Álvarez · [github.com/catalvarezs](https://github.com/catalvarezs)
