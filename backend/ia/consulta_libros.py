from google import genai
from google.genai import types
import time
from backend.config import GEMINI_API_KEY, MODELO_GEMINI
from backend.schemas import (
    CasoClinicoExtraido, 
    DiagnosticosSugeridosResponse, 
    PlanPAECompleto, 
    DiagnosticoNANDASchema
)
from backend.ia.buscador import buscar_fragmentos
from typing import List

cliente = genai.Client(api_key=GEMINI_API_KEY)

def _ejecutar_con_fallback(prompt: str, schema_salida):
    """
    Ejecuta la llamada con modelos válidos y desactiva el 'thinking_budget' 
    para que responda de inmediato en 5 segundos sin causar timeouts.
    """
    # Solo modelos oficiales que existen en la API
    modelos_candidatos = [
        MODELO_GEMINI, 
        "gemini-3-flash", 
        "gemini-2.5-flash", 
        "gemini-3.5-flash"
    ]
    modelos = list(dict.fromkeys(modelos_candidatos))

    ultimo_error = None
    for modelo in modelos:
        try:
            # Desactivamos el tiempo de pensamiento para respuesta ultrarrápida
            config_params = {
                "response_mime_type": "application/json",
                "response_schema": schema_salida,
                "temperature": 0.2
            }
            
            # Si el SDK soporta thinking_config, apagamos el gasto de tiempo
            try:
                config_params["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
            except Exception:
                pass

            return cliente.models.generate_content(
                model=modelo,
                contents=prompt,
                config=types.GenerateContentConfig(**config_params)
            )
        except Exception as e:
            ultimo_error = e
            msg = str(e).lower()
            print(f"Aviso en modelo {modelo}: {e}. Probando siguiente...")
            time.sleep(1)
            continue

    raise ultimo_error


def sugerir_diagnosticos_nanda(valoracion: CasoClinicoExtraido) -> DiagnosticosSugeridosResponse:
    consulta = f"{valoracion.motivo_ingreso} {valoracion.datos_subjetivos} {valoracion.datos_objetivos}"
    fragmentos_nanda = buscar_fragmentos("nanda", consulta, top_k=6)

    contexto_libros = "\n\n".join([
        f"[NANDA - Pág. {f.get('pagina')}]: {f.get('texto')}" 
        for f in fragmentos_nanda
    ])

    prompt = f"""
    Eres un enfermero especialista en diagnósticos de enfermería.
    A partir de la valoración y los fragmentos de referencia NANDA-I, sugiere de 3 a 6 diagnósticos de enfermería prioritarios.

    REGLAS:
    - Utiliza etiquetas y códigos oficiales NANDA presentes en los fragmentos o en la taxonomía NANDA-I.
    - Formato estrictamente PES:
      [Etiqueta NANDA] relacionado con (r/c) [Etiología/Causa] manifestado por (m/p) [Signos y Síntomas].

    FRAGMENTOS DE REFERENCIA NANDA:
    \"\"\"
    {contexto_libros if contexto_libros else "Usa la taxonomía oficial NANDA-I 2024-2026."}
    \"\"\"

    VALORACIÓN DEL PACIENTE:
    - Motivo de ingreso: {valoracion.motivo_ingreso}
    - Datos subjetivos: {valoracion.datos_subjetivos}
    - Datos objetivos: {valoracion.datos_objetivos}
    - Signos vitales: PA={valoracion.signos_vitales.presion_arterial}, FC={valoracion.signos_vitales.frecuencia_cardiaca}, FR={valoracion.signos_vitales.frecuencia_respiratoria}, Temp={valoracion.signos_vitales.temperatura}, SatO2={valoracion.signos_vitales.saturacion_oxigeno}
    - Antecedentes: {valoracion.antecedentes}
    """

    respuesta = _ejecutar_con_fallback(prompt, DiagnosticosSugeridosResponse)
    return DiagnosticosSugeridosResponse.model_validate_json(respuesta.text)


def generar_planificacion_pae(
    paciente_nombre: str,
    valoracion: CasoClinicoExtraido,
    diagnosticos_seleccionados: List[DiagnosticoNANDASchema]
) -> PlanPAECompleto:
    """Genera la planificación NOC/NIC optimizada y la nota SOAPIE estricta."""
    
    # Búsqueda ágil: top 2 fragmentos para no saturar tokens
    contexto_partes = []
    for diag in diagnosticos_seleccionados:
        frags_noc = buscar_fragmentos("noc", diag.etiqueta, top_k=2)
        frags_nic = buscar_fragmentos("nic", diag.etiqueta, top_k=2)
        for f in frags_noc:
            contexto_partes.append(f"[NOC Pág. {f.get('pagina')}]: {f.get('texto')[:600]}")
        for f in frags_nic:
            contexto_partes.append(f"[NIC Pág. {f.get('pagina')}]: {f.get('texto')[:600]}")

    contexto_libros = "\n".join(contexto_partes)

    sv = valoracion.signos_vitales
    sv_texto = f"PA: {sv.presion_arterial or 'N/E'}, FC: {sv.frecuencia_cardiaca or 'N/E'}, FR: {sv.frecuencia_respiratoria or 'N/E'}, Temp: {sv.temperatura or 'N/E'}, SpO2: {sv.saturacion_oxigeno or 'N/E'}"

    diagnosticos_texto = "\n".join([
        f"- Código {d.codigo} | {d.etiqueta}: {d.formato_pes}" for d in diagnosticos_seleccionados
    ])

    prompt = f"""
    Eres un especialista en Enfermería y PAE. Genera la planificación (NOC/NIC) y la nota de registro SOAPIE oficial.

    DATOS CLÍNICOS DEL PACIENTE:
    - Nombre: {paciente_nombre} | Edad: {valoracion.edad} | Cama: {valoracion.cama_servicio}
    - Motivo de consulta: {valoracion.motivo_ingreso}
    - Funciones Vitales: {sv_texto}
    - Datos Subjetivos: {valoracion.datos_subjetivos}
    - Datos Objetivos: {valoracion.datos_objetivos}
    - Antecedentes: {valoracion.antecedentes}

    DIAGNÓSTICOS SELECCIONADOS POR EL ENFERMERO:
    {diagnosticos_texto}

    TAXONOMÍAS DISPONIBLES:
    {contexto_libros}

    REGLAS ESTRICTAS PARA EL REGISTRO SOAPIE:
    - S: Párrafo continuo que DEBE iniciar con 'Paciente refiere:' describiendo molestias, síntomas y dolor sin viñetas (80-130 palabras).
    - O: Párrafo clínico continuo con examen físico y signos vitales ({sv_texto}) sin viñetas (90-150 palabras).
    - A: ÚNICAMENTE los diagnósticos seleccionados arriba, cada uno con viñeta '●' y estructura obligatoria '[Etiqueta] r/c [Causa] m/p [Signos/Síntomas]'.
    - P: Objetivos medibles, cada uno con viñeta '➔', e iniciando obligatoriamente con 'Paciente...' o 'El paciente...'.
    - I: Intervenciones de enfermería, cada una con viñeta '●', iniciando obligatoriamente con 'Se...' (ej: '● Se monitorizaron...', '● Se administró...'). Incluye entre 6 y 8 intervenciones.
    - E: Evaluación por problemas priorizados (ej: 'Dolor: Objetivo alcanzado...; Patrón respiratorio: Objetivo en proceso...').
    """

    respuesta = _ejecutar_con_fallback(prompt, PlanPAECompleto)
    return PlanPAECompleto.model_validate_json(respuesta.text)