from google import genai
from google.genai import types
from backend.config import GEMINI_API_KEY
from backend.schemas import CasoClinicoExtraido

# Inicializar el cliente de Gemini
cliente = genai.Client(api_key=GEMINI_API_KEY)

def analizar_caso_clinico(texto_caso: str) -> CasoClinicoExtraido:
    """Envía el caso clínico a Gemini y devuelve los datos estructurados."""
    prompt = f"""
    Eres un enfermero especialista en valoración clínica y Proceso de Atención de Enfermería (PAE).
    Analiza con detalle el siguiente caso clínico y extrae la información requerida.
    
    Identifica cuidadosamente:
    - Datos subjetivos (lo que el paciente manifiesta en sus propias palabras o quejas).
    - Datos objetivos (signos clínicos medibles, examen físico, escalas, laboratorios).
    - Signos vitales exactos.
    - Motivo de ingreso y antecedentes relevantes.

    CASO CLÍNICO:
    \"\"\"
    {texto_caso}
    \"\"\"
    """

    # Solicitamos la respuesta estructurada directamente según nuestro esquema Pydantic
    respuesta = cliente.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CasoClinicoExtraido,
            temperature=0.1  # Baja temperatura para máxima precisión y cero inventiva
        ),
    )

    return CasoClinicoExtraido.model_validate_json(respuesta.text)