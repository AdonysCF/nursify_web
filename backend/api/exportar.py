from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import json
import os

from backend.database import get_db
from backend.models import ReportePAE, Valoracion
from backend.utils.generador_documento import crear_documento_pae

router = APIRouter(prefix="/api/exportar", tags=["Exportación"])

@router.get("/word/{reporte_id}")
def descargar_word(reporte_id: int, db: Session = Depends(get_db)):
    """Genera y descarga el informe PAE en formato Word (.docx)."""
    reporte = db.query(ReportePAE).filter(ReportePAE.id == reporte_id).first()
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    valoracion = db.query(Valoracion).filter(Valoracion.paciente_id == reporte.paciente_id).first()
    plan_dict = json.loads(reporte.planificacion_json) if reporte.planificacion_json else {}

    ruta_word = crear_documento_pae(
        paciente=reporte.paciente,
        valoracion=valoracion,
        plan_pae_dict=plan_dict
    )

    if not os.path.exists(ruta_word):
        raise HTTPException(status_code=500, detail="Error al generar el archivo Word")

    return FileResponse(
        path=ruta_word,
        filename=os.path.basename(ruta_word),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )