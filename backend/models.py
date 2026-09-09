from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    edad = Column(Integer, nullable=True)
    sexo = Column(String(20), nullable=True)
    cama = Column(String(50), nullable=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    valoraciones = relationship("Valoracion", back_populates="paciente", cascade="all, delete-orphan")
    reportes = relationship("ReportePAE", back_populates="paciente", cascade="all, delete-orphan")


class Valoracion(Base):
    __tablename__ = "valoraciones"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    
    motivo_ingreso = Column(Text, nullable=True)
    signos_vitales = Column(Text, nullable=True)       # En formato JSON o texto libre
    antecedentes = Column(Text, nullable=True)
    datos_subjetivos = Column(Text, nullable=True)   # Lo que refiere el paciente
    datos_objetivos = Column(Text, nullable=True)     # Lo observado/medido en examen físico
    fecha = Column(DateTime, default=datetime.utcnow)

    paciente = relationship("Paciente", back_populates="valoraciones")


class ReportePAE(Base):
    __tablename__ = "reportes_pae"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    
    # Aquí se guardan los diagnósticos NANDA elegidos y las tablas NOC/NIC en formato JSON
    diagnosticos_json = Column(Text, nullable=True)
    planificacion_json = Column(Text, nullable=True)
    
    # Observaciones o conclusiones del informe
    observaciones = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    paciente = relationship("Paciente", back_populates="reportes")