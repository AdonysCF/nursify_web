from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import json

from backend.database import get_db
from backend.models import Paciente, Valoracion, ReportePAE
from backend.schemas import (
    CasoClinicoExtraido, 
    DiagnosticosSugeridosResponse, 
    DiagnosticoNANDASchema, 
    PlanPAECompleto
)
from backend.ia.consulta_libros import (
    sugerir_diagnosticos_nanda, 
    generar_planificacion_pae
)
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/pae", tags=["PAE - Diagnósticos y Plan"])

class PlanRequest(BaseModel):
    paciente_datos: CasoClinicoExtraido
    diagnosticos_elegidos: List[DiagnosticoNANDASchema]

@router.post("/diagnosticos-sugeridos", response_model=DiagnosticosSugeridosResponse)
def obtener_diagnosticos(valoracion: CasoClinicoExtraido):
    """Recibe la valoración (revisada por el usuario) y sugiere diagnósticos NANDA."""
    try:
        resultado = sugerir_diagnosticos_nanda(valoracion)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sugiriendo diagnósticos: {str(e)}")

@router.post("/generar-plan", response_model=PlanPAECompleto)
def crear_plan(req: PlanRequest, db: Session = Depends(get_db)):
    """Genera las tablas NOC y NIC y guarda el registro en la base de datos SQL."""
    try:
        # 1. Generar con Gemini
        plan = generar_planificacion_pae(
            paciente_nombre=req.paciente_datos.nombre_paciente or "Paciente",
            valoracion=req.paciente_datos,
            diagnosticos_seleccionados=req.diagnosticos_elegidos
        )

        # 2. Guardar automáticamente en SQLite
        nuevo_paciente = Paciente(
            nombre=req.paciente_datos.nombre_paciente or "Sin nombre",
            edad=req.paciente_datos.edad,
            sexo=req.paciente_datos.sexo,
            cama=req.paciente_datos.cama_servicio
        )
        db.add(nuevo_paciente)
        db.commit()
        db.refresh(nuevo_paciente)

        nueva_val = Valoracion(
            paciente_id=nuevo_paciente.id,
            motivo_ingreso=req.paciente_datos.motivo_ingreso,
            signos_vitales=req.paciente_datos.signos_vitales.model_dump_json(),
            antecedentes=req.paciente_datos.antecedentes,
            datos_subjetivos=req.paciente_datos.datos_subjetivos,
            datos_objetivos=req.paciente_datos.datos_objetivos
        )
        db.add(nueva_val)

        nuevo_reporte = ReportePAE(
            paciente_id=nuevo_paciente.id,
            diagnosticos_json=json.dumps([d.model_dump() for d in req.diagnosticos_elegidos]),
            planificacion_json=plan.model_dump_json(),
            observaciones=plan.resumen_valoracion
        )
        db.add(nuevo_reporte)
        db.commit()

        return plan
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error generando plan PAE: {str(e)}")