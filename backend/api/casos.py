from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from backend.utils.lector_pdf import extraer_texto_pdf
from backend.ia.extractor import analizar_caso_clinico
from backend.schemas import CasoClinicoExtraido

router = APIRouter(prefix="/api/casos", tags=["Casos Clínicos"])

@router.post("/extraer", response_model=CasoClinicoExtraido)
async def extraer_datos(
    archivo: Optional[UploadFile] = File(None),
    texto_manual: Optional[str] = Form(None)
):
    """
    Recibe un caso clínico por archivo PDF o texto directo en formulario,
    lo procesa con Gemini y devuelve los datos estructurados.
    """
    texto_a_procesar = ""

    if archivo:
        if not archivo.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Por ahora solo se admiten archivos PDF.")
        contenido = await archivo.read()
        texto_a_procesar = extraer_texto_pdf(contenido)
    elif texto_manual:
        texto_a_procesar = texto_manual.strip()
    else:
        raise HTTPException(status_code=400, detail="Debes proporcionar un archivo PDF o ingresar el texto del caso.")

    if not texto_a_procesar or len(texto_a_procesar) < 20:
        raise HTTPException(status_code=400, detail="El texto del caso clínico está vacío o es demasiado corto.")

    try:
        resultado = analizar_caso_clinico(texto_a_procesar)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar con IA: {str(e)}")