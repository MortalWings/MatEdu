from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import enum

# Enums para tipos de datos
class TipoUsuario(str, enum.Enum):
    ESTUDIANTE = "estudiante"
    PROFESOR = "profesor"
    ADMIN = "admin"

class NivelDificultad(str, enum.Enum):
    BASICO = "basico"
    INTERMEDIO = "intermedio"
    AVANZADO = "avanzado"

class TipoEjercicio(str, enum.Enum):
    OPCION_MULTIPLE = "opcion_multiple"
    DESARROLLO = "desarrollo"
    VERDADERO_FALSO = "verdadero_falso"
    COMPLETAR = "completar"

class EstadoProgreso(str, enum.Enum):
    NO_INICIADO = "no_iniciado"
    EN_PROGRESO = "en_progreso"
    COMPLETADO = "completado"

# ================================
# MODELOS SQLAlchemy (Base de Datos)
# ================================

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    tipo_usuario = Column(Enum(TipoUsuario), nullable=False)
    fecha_nacimiento = Column(DateTime)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)
    avatar_url = Column(String(255))
    
    # Estadísticas del usuario
    puntos_totales = Column(Integer, default=0)
    nivel_actual = Column(Integer, default=1)
    
    # Relaciones
    inscripciones = relationship("Inscripcion", back_populates="usuario")
    progreso_lecciones = relationship("ProgresoLeccion", back_populates="usuario")
    respuestas = relationship("RespuestaEjercicio", back_populates="usuario")
    logros_usuario = relationship("LogroUsuario", back_populates="usuario")
    cursos_creados = relationship("Curso", back_populates="profesor")

class AreaMatematica(Base):
    __tablename__ = "areas_matematicas"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    icono = Column(String(50))  # Nombre del icono
    color = Column(String(7))   # Color hexadecimal
    orden = Column(Integer, default=0)
    
    # Relaciones
    cursos = relationship("Curso", back_populates="area_matematica")

class Curso(Base):
    __tablename__ = "cursos"
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text)
    objetivos = Column(Text)
    nivel_dificultad = Column(Enum(NivelDificultad), nullable=False)
    duracion_estimada = Column(Integer)  # En horas
    imagen_portada = Column(String(255))
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    
    # Claves foráneas
    area_matematica_id = Column(Integer, ForeignKey("areas_matematicas.id"))
    profesor_id = Column(Integer, ForeignKey("usuarios.id"))
    
    # Relaciones
    area_matematica = relationship("AreaMatematica", back_populates="cursos")
    profesor = relationship("Usuario", back_populates="cursos_creados")
    lecciones = relationship("Leccion", back_populates="curso", order_by="Leccion.orden")
    inscripciones = relationship("Inscripcion", back_populates="curso")

class Leccion(Base):
    __tablename__ = "lecciones"
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text)
    contenido = Column(Text)  # Contenido en formato markdown
    video_url = Column(String(255))
    orden = Column(Integer, nullable=False)
    puntos_otorgados = Column(Integer, default=10)
    tiempo_estimado = Column(Integer)  # En minutos
    activa = Column(Boolean, default=True)
    
    # Clave foránea
    curso_id = Column(Integer, ForeignKey("cursos.id"))
    
    # Relaciones
    curso = relationship("Curso", back_populates="lecciones")
    ejercicios = relationship("Ejercicio", back_populates="leccion", order_by="Ejercicio.orden")
    progreso_lecciones = relationship("ProgresoLeccion", back_populates="leccion")

class Ejercicio(Base):
    __tablename__ = "ejercicios"
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    enunciado = Column(Text, nullable=False)
    tipo_ejercicio = Column(Enum(TipoEjercicio), nullable=False)
    nivel_dificultad = Column(Enum(NivelDificultad), nullable=False)
    puntos_otorgados = Column(Integer, default=5)
    tiempo_limite = Column(Integer)  # En minutos
    orden = Column(Integer, nullable=False)
    activo = Column(Boolean, default=True)
    
    # Campos específicos para diferentes tipos
    opciones_json = Column(Text)  # JSON con opciones para opción múltiple
    respuesta_correcta = Column(Text)
    explicacion = Column(Text)
    formula_latex = Column(Text)  # Para ejercicios con fórmulas matemáticas
    
    # Clave foránea
    leccion_id = Column(Integer, ForeignKey("lecciones.id"))
    
    # Relaciones
    leccion = relationship("Leccion", back_populates="ejercicios")
    respuestas = relationship("RespuestaEjercicio", back_populates="ejercicio")

class Inscripcion(Base):
    __tablename__ = "inscripciones"
    
    id = Column(Integer, primary_key=True, index=True)
    fecha_inscripcion = Column(DateTime, default=datetime.utcnow)
    fecha_completion = Column(DateTime)
    progreso_porcentaje = Column(Float, default=0.0)
    puntos_obtenidos = Column(Integer, default=0)
    activa = Column(Boolean, default=True)
    
    # Claves foráneas
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    curso_id = Column(Integer, ForeignKey("cursos.id"))
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="inscripciones")
    curso = relationship("Curso", back_populates="inscripciones")

class ProgresoLeccion(Base):
    __tablename__ = "progreso_lecciones"
    
    id = Column(Integer, primary_key=True, index=True)
    estado = Column(Enum(EstadoProgreso), default=EstadoProgreso.NO_INICIADO)
    fecha_inicio = Column(DateTime)
    fecha_completion = Column(DateTime)
    tiempo_dedicado = Column(Integer, default=0)  # En minutos
    puntos_obtenidos = Column(Integer, default=0)
    
    # Claves foráneas
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    leccion_id = Column(Integer, ForeignKey("lecciones.id"))
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="progreso_lecciones")
    leccion = relationship("Leccion", back_populates="progreso_lecciones")

class RespuestaEjercicio(Base):
    __tablename__ = "respuestas_ejercicios"
    
    id = Column(Integer, primary_key=True, index=True)
    respuesta_usuario = Column(Text, nullable=False)
    es_correcta = Column(Boolean, nullable=False)
    puntos_obtenidos = Column(Integer, default=0)
    tiempo_respuesta = Column(Integer)  # En segundos
    fecha_respuesta = Column(DateTime, default=datetime.utcnow)
    intentos = Column(Integer, default=1)
    
    # Claves foráneas
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    ejercicio_id = Column(Integer, ForeignKey("ejercicios.id"))
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="respuestas")
    ejercicio = relationship("Ejercicio", back_populates="respuestas")

class Logro(Base):
    __tablename__ = "logros"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    icono = Column(String(50))
    puntos_requeridos = Column(Integer)
    condicion_json = Column(Text)  # JSON con condiciones para obtener el logro
    activo = Column(Boolean, default=True)
    
    # Relaciones
    logros_usuario = relationship("LogroUsuario", back_populates="logro")

class LogroUsuario(Base):
    __tablename__ = "logros_usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    fecha_obtencion = Column(DateTime, default=datetime.utcnow)
    
    # Claves foráneas
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    logro_id = Column(Integer, ForeignKey("logros.id"))
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="logros_usuario")
    logro = relationship("Logro", back_populates="logros_usuario")

# ================================
# MODELOS PYDANTIC (API)
# ================================

class UsuarioBase(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    tipo_usuario: TipoUsuario
    fecha_nacimiento: Optional[datetime] = None

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioResponse(UsuarioBase):
    id: int
    fecha_registro: datetime
    puntos_totales: int
    nivel_actual: int
    activo: bool
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class AreaMatematicaBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    icono: Optional[str] = None
    color: Optional[str] = None

class AreaMatematicaCreate(AreaMatematicaBase):
    pass

class AreaMatematicaResponse(AreaMatematicaBase):
    id: int
    orden: int
    
    class Config:
        from_attributes = True

class CursoBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    objetivos: Optional[str] = None
    nivel_dificultad: NivelDificultad
    duracion_estimada: Optional[int] = None
    area_matematica_id: int

class CursoCreate(CursoBase):
    pass

class CursoResponse(CursoBase):
    id: int
    fecha_creacion: datetime
    activo: bool
    imagen_portada: Optional[str] = None
    area_matematica: Optional[AreaMatematicaResponse] = None
    profesor: Optional[UsuarioResponse] = None
    
    class Config:
        from_attributes = True

class LeccionBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    contenido: Optional[str] = None
    video_url: Optional[str] = None
    puntos_otorgados: int = 10
    tiempo_estimado: Optional[int] = None

class LeccionCreate(LeccionBase):
    curso_id: int
    orden: int

class LeccionResponse(LeccionBase):
    id: int
    orden: int
    activa: bool
    curso_id: int
    
    class Config:
        from_attributes = True

class EjercicioBase(BaseModel):
    titulo: str
    enunciado: str
    tipo_ejercicio: TipoEjercicio
    nivel_dificultad: NivelDificultad
    puntos_otorgados: int = 5
    tiempo_limite: Optional[int] = None
    respuesta_correcta: str
    explicacion: Optional[str] = None

class EjercicioCreate(EjercicioBase):
    leccion_id: int
    orden: int
    opciones_json: Optional[str] = None
    formula_latex: Optional[str] = None

class EjercicioResponse(EjercicioBase):
    id: int
    orden: int
    activo: bool
    leccion_id: int
    opciones_json: Optional[str] = None
    formula_latex: Optional[str] = None
    
    class Config:
        from_attributes = True

class RespuestaEjercicioCreate(BaseModel):
    ejercicio_id: int
    respuesta_usuario: str

class RespuestaEjercicioResponse(BaseModel):
    id: int
    respuesta_usuario: str
    es_correcta: bool
    puntos_obtenidos: int
    tiempo_respuesta: Optional[int] = None
    fecha_respuesta: datetime
    ejercicio_id: int
    
    class Config:
        from_attributes = True

class ProgresoLeccionResponse(BaseModel):
    id: int
    estado: EstadoProgreso
    fecha_inicio: Optional[datetime] = None
    fecha_completion: Optional[datetime] = None
    tiempo_dedicado: int
    puntos_obtenidos: int
    leccion: LeccionResponse
    
    class Config:
        from_attributes = True

class EstadisticasUsuario(BaseModel):
    usuario_id: int
    cursos_inscritos: int
    cursos_completados: int
    lecciones_completadas: int
    ejercicios_resueltos: int
    ejercicios_correctos: int
    puntos_totales: int
    tiempo_total_estudio: int  # En minutos
    racha_actual: int  # Días consecutivos estudiando
    logros_obtenidos: int
