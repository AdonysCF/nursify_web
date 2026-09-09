from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from typing import List

from backend.database import get_db
from backend.models import Paciente, ReportePAE

router = APIRouter(prefix="/api/reportes", tags=["Historial de Reportes"])

@router.get("/")
def listar_reportes(db: Session = Depends(get_db)):
    """Lista todos los reportes generados con datos del paciente para el panel principal."""
    reportes = db.query(ReportePAE).join(Paciente).order_by(ReportePAE.fecha_creacion.desc()).all()
    
    resultado = []
    for r in reportes:
        resultado.append({
            "reporte_id": r.id,
            "paciente_id": r.paciente.id,
            "paciente_nombre": r.paciente.nombre,
            "edad": r.paciente.edad,
            "cama": r.paciente.cama,
            "fecha": r.fecha_creacion.strftime("%d/%m/%Y %H:%M"),
            "observaciones": r.observaciones
        })
    return resultado

@router.get("/{reporte_id}")
def obtener_detalle_reporte(reporte_id: int, db: Session = Depends(get_db)):
    """Obtiene el detalle completo de un reporte con sus diagnósticos y tablas NOC/NIC."""
    reporte = db.query(ReportePAE).filter(ReportePAE.id == reporte_id).first()
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    return {
        "reporte_id": reporte.id,
        "paciente": {
            "nombre": reporte.paciente.nombre,
            "edad": reporte.paciente.edad,
            "sexo": reporte.paciente.sexo,
            "cama": reporte.paciente.cama
        },
        "diagnosticos": json.loads(reporte.diagnosticos_json) if reporte.diagnosticos_json else [],
        "planificacion": json.loads(reporte.planificacion_json) if reporte.planificacion_json else {},
        "fecha": reporte.fecha_creacion.strftime("%d/%m/%Y %H:%M")
    }

@router.delete("/{reporte_id}")
def eliminar_reporte(reporte_id: int, db: Session = Depends(get_db)):
    """Elimina un reporte y su paciente asociado."""
    reporte = db.query(ReportePAE).filter(ReportePAE.id == reporte_id).first()
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    db.delete(reporte.paciente)
    db.commit()
    return {"mensaje": "Reporte y paciente eliminados correctamente"}