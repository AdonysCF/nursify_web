from pydantic import BaseModel, Field
from typing import Optional
from typing import List

class SignosVitalesSchema(BaseModel):
    presion_arterial: Optional[str] = Field(None, description="Ejemplo: 120/80 mmHg")
    frecuencia_cardiaca: Optional[str] = Field(None, description="Latidos por minuto")
    frecuencia_respiratoria: Optional[str] = Field(None, description="Respiraciones por minuto")
    temperatura: Optional[str] = Field(None, description="En grados Celsius")
    saturacion_oxigeno: Optional[str] = Field(None, description="Porcentaje de SpO2")

class CasoClinicoExtraido(BaseModel):
    nombre_paciente: Optional[str] = Field("Paciente No Identificado", description="Nombre del paciente si aparece")
    edad: Optional[int] = Field(None, description="Edad en años")
    sexo: Optional[str] = Field(None, description="Masculino, Femenino o No especificado")
    cama_servicio: Optional[str] = Field(None, description="Cama, sala o servicio de hospitalización")
    motivo_ingreso: str = Field(..., description="Razón principal de consulta o ingreso")
    antecedentes: Optional[str] = Field(None, description="Antecedentes médicos, quirúrgicos o alergias")
    signos_vitales: SignosVitalesSchema
    datos_subjetivos: str = Field(..., description="Lo que el paciente o familiar refiere sentir (dolor, angustia, mareo)")
    datos_objetivos: str = Field(..., description="Hallazgos del examen físico, sondas, heridas, laboratorio relevante")

class DiagnosticoNANDASchema(BaseModel):
    codigo: str = Field(..., description="Código oficial NANDA, ej: 00132")
    etiqueta: str = Field(..., description="Nombre del diagnóstico NANDA")
    dominio: str = Field(..., description="Dominio NANDA")
    clase: str = Field(..., description="Clase NANDA")
    formato_pes: str = Field(..., description="Enunciado completo: Problema r/c Etiología m/p Manifestaciones")
    justificacion: str = Field(..., description="Por qué aplica a este paciente según los datos objetivos/subjetivos")

class DiagnosticosSugeridosResponse(BaseModel):
    diagnosticos: List[DiagnosticoNANDASchema]

class IndicadorNOCSchema(BaseModel):
    nombre: str
    escala: str = Field("1 a 5", description="Escala de Likert")
    puntuacion_actual: int = Field(..., ge=1, le=5)
    puntuacion_diana: int = Field(..., ge=1, le=5)

class ResultadoNOCSchema(BaseModel):
    codigo: str
    nombre: str
    indicadores: List[IndicadorNOCSchema]

class IntervencionNICSchema(BaseModel):
    codigo: str
    nombre: str
    actividades: List[str] = Field(..., description="Lista de acciones específicas que realizará enfermería")

class PlanCuidadoItem(BaseModel):
    diagnostico_nanda: DiagnosticoNANDASchema
    resultados_noc: List[ResultadoNOCSchema]
    intervenciones_nic: List[IntervencionNICSchema]
    evaluacion_esperada: str

class SOAPIESchema(BaseModel):
    s: str = Field(..., description="Subjetivo: Párrafo académico de 80-130 palabras que inicia obligatoriamente con 'Paciente refiere:' y describe síntomas, dolor EVA, etc.")
    o: str = Field(..., description="Objetivo: Párrafo clínico de 90-150 palabras con estado general, examen físico y signos vitales completos con valores numéricos.")
    a: str = Field(..., description="Análisis: Diagnósticos NANDA seleccionados, cada uno con viñeta '●' y formato estricto 'r/c' y 'm/p'.")
    p: str = Field(..., description="Planificación: Objetivos medibles, cada uno con viñeta '➔' e iniciando con 'Paciente' o 'El paciente'.")
    i: str = Field(..., description="Intervenciones: Acciones de enfermería, cada una con viñeta '●' e iniciando con 'Se...' (ej: Se monitorizaron, Se administró).")
    e: str = Field(..., description="Evaluación: Logro por problema priorizado (ej: Dolor: Objetivo alcanzado; Termorregulación: En proceso).")

class PlanPAECompleto(BaseModel):
    paciente_nombre: str
    resumen_valoracion: str
    planes: List[PlanCuidadoItem]
    soapie: SOAPIESchema