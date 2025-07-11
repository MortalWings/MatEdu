from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, timedelta
import json

from app.database import get_db
from app.models import *
from app.auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()

# ================================
# AUTENTICACIÓN
# ================================

@router.post("/auth/registro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """Registrar un nuevo usuario"""
    # Verificar si el usuario ya existe
    db_usuario = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(
            status_code=400,
            detail="El email ya está registrado"
        )
    
    # Crear nuevo usuario
    hashed_password = get_password_hash(usuario.password)
    db_usuario = Usuario(
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        password_hash=hashed_password,
        tipo_usuario=usuario.tipo_usuario,
        fecha_nacimiento=usuario.fecha_nacimiento
    )
    
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@router.post("/auth/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Autenticar usuario y devolver token"""
    usuario = db.query(Usuario).filter(Usuario.email == login_data.email).first()
    
    if not usuario or not verify_password(login_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# ================================
# USUARIOS
# ================================

@router.get("/usuarios/me", response_model=UsuarioResponse)
def obtener_perfil(current_user: Usuario = Depends(get_current_active_user)):
    """Obtener perfil del usuario actual"""
    return current_user

@router.get("/usuarios/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Obtener información de un usuario específico"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@router.get("/usuarios/{usuario_id}/estadisticas", response_model=EstadisticasUsuario)
def obtener_estadisticas_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Obtener estadísticas de un usuario"""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Calcular estadísticas
    inscripciones = db.query(Inscripcion).filter(Inscripcion.usuario_id == usuario_id).all()
    cursos_inscritos = len(inscripciones)
    cursos_completados = len([i for i in inscripciones if i.progreso_porcentaje == 100.0])
    
    progreso_lecciones = db.query(ProgresoLeccion).filter(ProgresoLeccion.usuario_id == usuario_id).all()
    lecciones_completadas = len([p for p in progreso_lecciones if p.estado == EstadoProgreso.COMPLETADO])
    
    respuestas = db.query(RespuestaEjercicio).filter(RespuestaEjercicio.usuario_id == usuario_id).all()
    ejercicios_resueltos = len(respuestas)
    ejercicios_correctos = len([r for r in respuestas if r.es_correcta])
    
    tiempo_total = sum([p.tiempo_dedicado for p in progreso_lecciones])
    
    logros = db.query(LogroUsuario).filter(LogroUsuario.usuario_id == usuario_id).count()
    
    return EstadisticasUsuario(
        usuario_id=usuario_id,
        cursos_inscritos=cursos_inscritos,
        cursos_completados=cursos_completados,
        lecciones_completadas=lecciones_completadas,
        ejercicios_resueltos=ejercicios_resueltos,
        ejercicios_correctos=ejercicios_correctos,
        puntos_totales=usuario.puntos_totales,
        tiempo_total_estudio=tiempo_total,
        racha_actual=0,  # TODO: Implementar lógica de racha
        logros_obtenidos=logros
    )

# ================================
# ÁREAS MATEMÁTICAS
# ================================

@router.post("/areas-matematicas", response_model=AreaMatematicaResponse, status_code=status.HTTP_201_CREATED)
def crear_area_matematica(area: AreaMatematicaCreate, db: Session = Depends(get_db)):
    """Crear una nueva área matemática"""
    db_area = AreaMatematica(**area.dict())
    db.add(db_area)
    db.commit()
    db.refresh(db_area)
    return db_area

@router.get("/areas-matematicas", response_model=List[AreaMatematicaResponse])
def obtener_areas_matematicas(db: Session = Depends(get_db)):
    """Obtener todas las áreas matemáticas"""
    return db.query(AreaMatematica).order_by(AreaMatematica.orden).all()

# ================================
# CURSOS
# ================================

@router.post("/cursos", response_model=CursoResponse, status_code=status.HTTP_201_CREATED)
def crear_curso(
    curso: CursoCreate, 
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear un nuevo curso"""
    # Verificar que el área matemática existe
    area = db.query(AreaMatematica).filter(AreaMatematica.id == curso.area_matematica_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Área matemática no encontrada")
    
    db_curso = Curso(**curso.dict(), profesor_id=current_user.id)
    db.add(db_curso)
    db.commit()
    db.refresh(db_curso)
    return db_curso

@router.get("/cursos", response_model=List[CursoResponse])
def obtener_cursos(
    area_id: int = None,
    nivel: NivelDificultad = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Obtener cursos con filtros opcionales"""
    query = db.query(Curso).filter(Curso.activo == True)
    
    if area_id:
        query = query.filter(Curso.area_matematica_id == area_id)
    if nivel:
        query = query.filter(Curso.nivel_dificultad == nivel)
    
    return query.offset(skip).limit(limit).all()

@router.get("/cursos/{curso_id}", response_model=CursoResponse)
def obtener_curso(curso_id: int, db: Session = Depends(get_db)):
    """Obtener un curso específico"""
    curso = db.query(Curso).filter(Curso.id == curso_id, Curso.activo == True).first()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return curso

# ================================
# INSCRIPCIONES
# ================================

@router.post("/cursos/{curso_id}/inscribirse", status_code=status.HTTP_201_CREATED)
def inscribirse_curso(
    curso_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Inscribirse a un curso"""
    # Verificar que el curso existe
    curso = db.query(Curso).filter(Curso.id == curso_id, Curso.activo == True).first()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    # Verificar si ya está inscrito
    inscripcion_existente = db.query(Inscripcion).filter(
        Inscripcion.usuario_id == current_user.id,
        Inscripcion.curso_id == curso_id,
        Inscripcion.activa == True
    ).first()
    
    if inscripcion_existente:
        raise HTTPException(status_code=400, detail="Ya estás inscrito en este curso")
    
    # Crear inscripción
    inscripcion = Inscripcion(usuario_id=current_user.id, curso_id=curso_id)
    db.add(inscripcion)
    db.commit()
    
    return {"message": "Inscripción exitosa"}

@router.get("/usuarios/me/cursos", response_model=List[CursoResponse])
def obtener_mis_cursos(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener cursos en los que está inscrito el usuario"""
    inscripciones = db.query(Inscripcion).filter(
        Inscripcion.usuario_id == current_user.id,
        Inscripcion.activa == True
    ).all()
    
    cursos = []
    for inscripcion in inscripciones:
        if inscripcion.curso.activo:
            cursos.append(inscripcion.curso)
    
    return cursos

# ================================
# LECCIONES
# ================================

@router.post("/lecciones", response_model=LeccionResponse, status_code=status.HTTP_201_CREATED)
def crear_leccion(
    leccion: LeccionCreate,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear una nueva lección"""
    # Verificar que el curso existe y el usuario es el profesor
    curso = db.query(Curso).filter(Curso.id == leccion.curso_id).first()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    if curso.profesor_id != current_user.id and current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear lecciones en este curso")
    
    db_leccion = Leccion(**leccion.dict())
    db.add(db_leccion)
    db.commit()
    db.refresh(db_leccion)
    return db_leccion

@router.get("/cursos/{curso_id}/lecciones", response_model=List[LeccionResponse])
def obtener_lecciones_curso(curso_id: int, db: Session = Depends(get_db)):
    """Obtener todas las lecciones de un curso"""
    curso = db.query(Curso).filter(Curso.id == curso_id).first()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    return db.query(Leccion).filter(
        Leccion.curso_id == curso_id,
        Leccion.activa == True
    ).order_by(Leccion.orden).all()

# ================================
# EJERCICIOS
# ================================

@router.post("/ejercicios", response_model=EjercicioResponse, status_code=status.HTTP_201_CREATED)
def crear_ejercicio(
    ejercicio: EjercicioCreate,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear un nuevo ejercicio"""
    # Verificar que la lección existe
    leccion = db.query(Leccion).filter(Leccion.id == ejercicio.leccion_id).first()
    if not leccion:
        raise HTTPException(status_code=404, detail="Lección no encontrada")
    
    # Verificar permisos
    if leccion.curso.profesor_id != current_user.id and current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para crear ejercicios en esta lección")
    
    db_ejercicio = Ejercicio(**ejercicio.dict())
    db.add(db_ejercicio)
    db.commit()
    db.refresh(db_ejercicio)
    return db_ejercicio

@router.get("/lecciones/{leccion_id}/ejercicios", response_model=List[EjercicioResponse])
def obtener_ejercicios_leccion(leccion_id: int, db: Session = Depends(get_db)):
    """Obtener todos los ejercicios de una lección"""
    leccion = db.query(Leccion).filter(Leccion.id == leccion_id).first()
    if not leccion:
        raise HTTPException(status_code=404, detail="Lección no encontrada")
    
    return db.query(Ejercicio).filter(
        Ejercicio.leccion_id == leccion_id,
        Ejercicio.activo == True
    ).order_by(Ejercicio.orden).all()

# ================================
# RESPUESTAS Y EVALUACIÓN
# ================================

@router.post("/ejercicios/{ejercicio_id}/responder", response_model=RespuestaEjercicioResponse)
def responder_ejercicio(
    ejercicio_id: int,
    respuesta_data: RespuestaEjercicioCreate,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Responder un ejercicio"""
    # Verificar que el ejercicio existe
    ejercicio = db.query(Ejercicio).filter(Ejercicio.id == ejercicio_id).first()
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    
    # Evaluar respuesta
    es_correcta = ejercicio.respuesta_correcta.lower().strip() == respuesta_data.respuesta_usuario.lower().strip()
    puntos_obtenidos = ejercicio.puntos_otorgados if es_correcta else 0
    
    # Guardar respuesta
    db_respuesta = RespuestaEjercicio(
        usuario_id=current_user.id,
        ejercicio_id=ejercicio_id,
        respuesta_usuario=respuesta_data.respuesta_usuario,
        es_correcta=es_correcta,
        puntos_obtenidos=puntos_obtenidos
    )
    
    db.add(db_respuesta)
    
    # Actualizar puntos del usuario si es correcta
    if es_correcta:
        current_user.puntos_totales += puntos_obtenidos
    
    db.commit()
    db.refresh(db_respuesta)
    
    return db_respuesta

# ================================
# PROGRESO
# ================================

@router.post("/lecciones/{leccion_id}/iniciar")
def iniciar_leccion(
    leccion_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Marcar una lección como iniciada"""
    # Verificar que la lección existe
    leccion = db.query(Leccion).filter(Leccion.id == leccion_id).first()
    if not leccion:
        raise HTTPException(status_code=404, detail="Lección no encontrada")
    
    # Verificar si ya existe progreso
    progreso = db.query(ProgresoLeccion).filter(
        ProgresoLeccion.usuario_id == current_user.id,
        ProgresoLeccion.leccion_id == leccion_id
    ).first()
    
    if not progreso:
        progreso = ProgresoLeccion(
            usuario_id=current_user.id,
            leccion_id=leccion_id,
            estado=EstadoProgreso.EN_PROGRESO,
            fecha_inicio=datetime.utcnow()
        )
        db.add(progreso)
    elif progreso.estado == EstadoProgreso.NO_INICIADO:
        progreso.estado = EstadoProgreso.EN_PROGRESO
        progreso.fecha_inicio = datetime.utcnow()
    
    db.commit()
    return {"message": "Lección iniciada"}

@router.post("/lecciones/{leccion_id}/completar")
def completar_leccion(
    leccion_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Marcar una lección como completada"""
    # Verificar que la lección existe
    leccion = db.query(Leccion).filter(Leccion.id == leccion_id).first()
    if not leccion:
        raise HTTPException(status_code=404, detail="Lección no encontrada")
    
    # Obtener o crear progreso
    progreso = db.query(ProgresoLeccion).filter(
        ProgresoLeccion.usuario_id == current_user.id,
        ProgresoLeccion.leccion_id == leccion_id
    ).first()
    
    if not progreso:
        progreso = ProgresoLeccion(
            usuario_id=current_user.id,
            leccion_id=leccion_id,
            fecha_inicio=datetime.utcnow()
        )
        db.add(progreso)
    
    # Marcar como completada
    progreso.estado = EstadoProgreso.COMPLETADO
    progreso.fecha_completion = datetime.utcnow()
    progreso.puntos_obtenidos = leccion.puntos_otorgados
    
    # Agregar puntos al usuario
    current_user.puntos_totales += leccion.puntos_otorgados
    
    db.commit()
    return {"message": "Lección completada", "puntos_obtenidos": leccion.puntos_otorgados}

@router.get("/usuarios/me/progreso/{curso_id}")
def obtener_progreso_curso(
    curso_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener el progreso del usuario en un curso"""
    # Verificar inscripción
    inscripcion = db.query(Inscripcion).filter(
        Inscripcion.usuario_id == current_user.id,
        Inscripcion.curso_id == curso_id,
        Inscripcion.activa == True
    ).first()
    
    if not inscripcion:
        raise HTTPException(status_code=404, detail="No estás inscrito en este curso")
    
    # Obtener lecciones del curso
    lecciones = db.query(Leccion).filter(
        Leccion.curso_id == curso_id,
        Leccion.activa == True
    ).all()
    
    # Obtener progreso de cada lección
    progreso_lecciones = []
    for leccion in lecciones:
        progreso = db.query(ProgresoLeccion).filter(
            ProgresoLeccion.usuario_id == current_user.id,
            ProgresoLeccion.leccion_id == leccion.id
        ).first()
        
        if progreso:
            progreso_lecciones.append(progreso)
        else:
            # Crear progreso vacío
            progreso_vacio = ProgresoLeccion(
                usuario_id=current_user.id,
                leccion_id=leccion.id,
                estado=EstadoProgreso.NO_INICIADO
            )
            progreso_lecciones.append(progreso_vacio)
    
    # Calcular porcentaje de progreso
    lecciones_completadas = len([p for p in progreso_lecciones if p.estado == EstadoProgreso.COMPLETADO])
    porcentaje_progreso = (lecciones_completadas / len(lecciones)) * 100 if lecciones else 0
    
    # Actualizar inscripción
    inscripcion.progreso_porcentaje = porcentaje_progreso
    db.commit()
    
    return {
        "curso_id": curso_id,
        "progreso_porcentaje": porcentaje_progreso,
        "lecciones_totales": len(lecciones),
        "lecciones_completadas": lecciones_completadas,
        "puntos_obtenidos": inscripcion.puntos_obtenidos,
        "progreso_lecciones": progreso_lecciones
    }

# ================================
# EJEMPLO SIMPLE - RUTA DE PRUEBA
# ================================

@router.get("/hola")
def saludar():
    """Ruta simple de ejemplo"""
    return {"mensaje": "¡Hola! Esta es una ruta de prueba"}

@router.get("/hola/{nombre}")
def saludar_persona(nombre: str):
    """Ruta con parámetro - ejemplo"""
    return {"mensaje": f"¡Hola {nombre}! ¿Cómo estás?"}

# ================================
# PROFESORES - ASIGNACIÓN DE CURSOS
# ================================

@router.post("/profesores/asignar-curso", response_model=List[AsignacionCursoResponse])
def asignar_curso_estudiantes(
    asignacion: AsignarCursoRequest, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Profesor asigna un curso a uno o varios estudiantes"""
    # Verificar que el usuario sea profesor
    if current_user.tipo_usuario != TipoUsuario.PROFESOR:
        raise HTTPException(status_code=403, detail="Solo los profesores pueden asignar cursos")
    
    # Verificar que el curso existe
    curso = db.query(Curso).filter(Curso.id == asignacion.curso_id).first()
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    asignaciones_creadas = []
    
    for estudiante_id in asignacion.estudiantes_ids:
        # Verificar que el estudiante existe
        estudiante = db.query(Usuario).filter(
            Usuario.id == estudiante_id,
            Usuario.tipo_usuario == TipoUsuario.ESTUDIANTE
        ).first()
        
        if not estudiante:
            continue  # Saltar estudiantes no válidos
        
        # Verificar si ya existe la asignación
        asignacion_existente = db.query(AsignacionCurso).filter(
            AsignacionCurso.profesor_id == current_user.id,
            AsignacionCurso.estudiante_id == estudiante_id,
            AsignacionCurso
        ).first()
        
        if asignacion_existente:
            continue  # Saltar si ya está asignado
        
        # Crear nueva asignación
        nueva_asignacion = AsignacionCurso(
            profesor_id=current_user.id,
            estudiante_id=estudiante_id,
            curso_id=asignacion.curso_id,
            fecha_limite=asignacion.fecha_limite,
            observaciones=asignacion.observaciones
        )
        
        db.add(nueva_asignacion)
        db.commit()
        db.refresh(nueva_asignacion)
        asignaciones_creadas.append(nueva_asignacion)
    
    return asignaciones_creadas

@router.get("/profesores/me/estudiantes", response_model=List[UsuarioResponse])
def obtener_mis_estudiantes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtener estudiantes asignados al profesor actual"""
    if current_user.tipo_usuario != TipoUsuario.PROFESOR:
        raise HTTPException(status_code=403, detail="Solo profesores pueden acceder")
    
    estudiantes = db.query(Usuario).join(
        ProfesorEstudiante, Usuario.id == ProfesorEstudiante.estudiante_id
    ).filter(
        ProfesorEstudiante.profesor_id == current_user.id,
        ProfesorEstudiante.activo == True,
        Usuario.tipo_usuario == TipoUsuario.ESTUDIANTE
    ).all()
    
    return estudiantes

@router.get("/profesores/me/asignaciones", response_model=List[AsignacionCursoResponse])
def obtener_mis_asignaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtener todas las asignaciones realizadas por el profesor"""
    if current_user.tipo_usuario != TipoUsuario.PROFESOR:
        raise HTTPException(status_code=403, detail="Solo profesores pueden acceder")
    
    asignaciones = db.query(AsignacionCurso).options(
        joinedload(AsignacionCurso.curso),
        joinedload(AsignacionCurso.profesor),
        joinedload(AsignacionCurso.estudiante)
    ).filter(
        AsignacionCurso.profesor_id == current_user.id
    ).all()
    
    return asignaciones

@router.delete("/profesores/asignar-curso/{asignacion_id}")
def remover_asignacion_curso(
    asignacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Remover asignación de curso"""
    if current_user.tipo_usuario != TipoUsuario.PROFESOR:
        raise HTTPException(status_code=403, detail="Solo profesores pueden remover asignaciones")
    
    asignacion = db.query(AsignacionCurso).filter(
        AsignacionCurso.id == asignacion_id,
        AsignacionCurso.profesor_id == current_user.id
    ).first()
    
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    
    db.delete(asignacion)
    db.commit()
    
    return {"message": "Asignación removida exitosamente"}

# ================================
# ESTUDIANTES - CURSOS ASIGNADOS
# ================================

@router.get("/estudiantes/me/cursos-asignados", response_model=List[CursoAsignadoResponse])
def obtener_cursos_asignados(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtener cursos asignados al estudiante actual"""
    if current_user.tipo_usuario != TipoUsuario.ESTUDIANTE:
        raise HTTPException(status_code=403, detail="Solo estudiantes pueden acceder")
    
    asignaciones = db.query(AsignacionCurso).options(
        joinedload(AsignacionCurso.curso),
        joinedload(AsignacionCurso.profesor),
        joinedload(AsignacionCurso.estudiante)
    ).filter(
        AsignacionCurso.estudiante_id == current_user.id
    ).all()
    
    return asignaciones

@router.post("/estudiantes/iniciar-curso-asignado/{asignacion_id}")
def iniciar_curso_asignado(
    asignacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Estudiante inicia un curso que le fue asignado"""
    if current_user.tipo_usuario != TipoUsuario.ESTUDIANTE:
        raise HTTPException(status_code=403, detail="Solo estudiantes pueden iniciar cursos")
    
    asignacion = db.query(AsignacionCurso).filter(
        AsignacionCurso.id == asignacion_id,
        AsignacionCurso.estudiante_id == current_user.id
    ).first()
    
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    
    # Actualizar estado y fecha de inicio
    if asignacion.estado == EstadoAsignacion.ASIGNADO:
        asignacion.estado = EstadoAsignacion.EN_PROGRESO
        asignacion.fecha_inicio = datetime.utcnow()
        
        # Crear inscripción tradicional para compatibilidad
        inscripcion_existente = db.query(Inscripcion).filter(
            Inscripcion.usuario_id == current_user.id,
            Inscripcion.curso_id == asignacion.curso_id
        ).first()
        
        if not inscripcion_existente:
            nueva_inscripcion = Inscripcion(
                usuario_id=current_user.id,
                curso_id=asignacion.curso_id
            )
            db.add(nueva_inscripcion)
        
        db.commit()
    
    return {"message": "Curso iniciado exitosamente", "asignacion": asignacion}

@router.get("/estudiantes/me/profesor", response_model=UsuarioResponse)
def obtener_mi_profesor(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtener el profesor asignado al estudiante"""
    if current_user.tipo_usuario != TipoUsuario.ESTUDIANTE:
        raise HTTPException(status_code=403, detail="Solo estudiantes pueden acceder")
    
    relacion = db.query(ProfesorEstudiante).filter(
        ProfesorEstudiante.estudiante_id == current_user.id,
        ProfesorEstudiante.activo == True
    ).first()
    
    if not relacion:
        raise HTTPException(status_code=404, detail="No tienes profesor asignado")
    
    profesor = db.query(Usuario).filter(Usuario.id == relacion.profesor_id).first()
    return profesor

# ================================
# ADMIN - GESTIÓN PROFESOR-ESTUDIANTE
# ================================

@router.post("/admin/asignar-estudiante-profesor")
def asignar_estudiante_profesor(
    asignacion: AsignarEstudianteProfesorRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Admin asigna estudiante a profesor"""
    if current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo administradores pueden hacer esta asignación")
    
    # Verificar que el profesor existe
    profesor = db.query(Usuario).filter(
        Usuario.id == asignacion.profesor_id,
        Usuario.tipo_usuario == TipoUsuario.PROFESOR
    ).first()
    
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")
    
    # Verificar que el estudiante existe
    estudiante = db.query(Usuario).filter(
        Usuario.id == asignacion.estudiante_id,
        Usuario.tipo_usuario == TipoUsuario.ESTUDIANTE
    ).first()
    
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Verificar si ya existe la relación
    relacion_existente = db.query(ProfesorEstudiante).filter(
        ProfesorEstudiante.profesor_id == asignacion.profesor_id,
        ProfesorEstudiante.estudiante_id == asignacion.estudiante_id,
        ProfesorEstudiante.activo == True
    ).first()
    
    if relacion_existente:
        raise HTTPException(status_code=400, detail="El estudiante ya está asignado a este profesor")
    
    # Crear nueva relación
    nueva_relacion = ProfesorEstudiante(
        profesor_id=asignacion.profesor_id,
        estudiante_id=asignacion.estudiante_id
    )
    
    db.add(nueva_relacion)
    db.commit()
    
    return {"message": "Estudiante asignado al profesor exitosamente"}

# ================================
# ADMIN - GESTIÓN DE USUARIOS (CRUD)
# ================================

@router.get("/admin/usuarios", response_model=List[UsuarioResponse])
def listar_usuarios(
    tipo_usuario: TipoUsuario = None,
    activo: bool = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Admin obtiene lista de todos los usuarios con filtros"""
    if current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo administradores pueden listar usuarios")
    
    query = db.query(Usuario)
    
    if tipo_usuario:
        query = query.filter(Usuario.tipo_usuario == tipo_usuario)
    if activo is not None:
        query = query.filter(Usuario.activo == activo)
    
    return query.offset(skip).limit(limit).all()

@router.post("/admin/usuarios", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario_admin(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Admin crea un nuevo usuario"""
    if current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear usuarios")
    
    # Verificar si el email ya existe
    db_usuario = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if db_usuario:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Crear nuevo usuario
    hashed_password = get_password_hash(usuario.password)
    db_usuario = Usuario(
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        email=usuario.email,
        password_hash=hashed_password,
        tipo_usuario=usuario.tipo_usuario,
        fecha_nacimiento=usuario.fecha_nacimiento
    )
    
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@router.put("/admin/usuarios/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario_admin(
    usuario_id: int,
    usuario_update: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Admin actualiza información de un usuario"""
    if current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo administradores pueden actualizar usuarios")
    
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Actualizar campos si se proporcionan
    update_data = usuario_update.dict(exclude_unset=True)
    
    # Si se actualiza el password, hashearlo
    if 'password' in update_data:
        update_data['password_hash'] = get_password_hash(update_data.pop('password'))
    
    for field, value in update_data.items():
        setattr(db_usuario, field, value)
    
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@router.delete("/admin/usuarios/{usuario_id}")
def eliminar_usuario_admin(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Admin elimina (desactiva) un usuario"""
    if current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar usuarios")
    
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Marcar como inactivo en lugar de eliminar físicamente
    db_usuario.activo = False
    db.commit()
    
    return {"message": "Usuario desactivado exitosamente"}

@router.put("/admin/usuarios/{usuario_id}/activar")
def activar_usuario_admin(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Admin reactiva un usuario desactivado"""
    if current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo administradores pueden activar usuarios")
    
    db_usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db_usuario.activo = True
    db.commit()
    
    return {"message": "Usuario activado exitosamente"}

# ================================
# ADMIN - GESTIÓN DE CURSOS
# ================================

@router.get("/admin/cursos", response_model=List[CursoResponse])
def listar_cursos_admin(
    activo: bool = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Admin obtiene lista de todos los cursos"""
    if current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo administradores pueden listar todos los cursos")
    
    query = db.query(Curso)
    
    if activo is not None:
        query = query.filter(Curso.activo == activo)
    
    return query.offset(skip).limit(limit).all()

@router.put("/admin/cursos/{curso_id}", response_model=CursoResponse)
def actualizar_curso_admin(
    curso_id: int,
    curso_update: CursoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Admin actualiza información de un curso"""
    if current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo administradores pueden actualizar cursos")
    
    db_curso = db.query(Curso).filter(Curso.id == curso_id).first()
    if not db_curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    # Actualizar campos si se proporcionan
    update_data = curso_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_curso, field, value)
    
    db.commit()
    db.refresh(db_curso)
    return db_curso

@router.delete("/admin/cursos/{curso_id}")
def eliminar_curso_admin(
    curso_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Admin elimina (desactiva) un curso"""
    if current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar cursos")
    
    db_curso = db.query(Curso).filter(Curso.id == curso_id).first()
    if not db_curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    # Marcar como inactivo
    db_curso.activo = False
    db.commit()
    
    return {"message": "Curso desactivado exitosamente"}

# ================================
# ESTUDIANTES - ENDPOINTS CRUD DE PRIORIDAD ALTA
# ================================

@router.get("/estudiantes/me/lecciones/{leccion_id}/detalle", response_model=LeccionResponse)
def obtener_detalle_leccion(
    leccion_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Estudiante obtiene el detalle completo de una lección"""
    if current_user.tipo_usuario != TipoUsuario.ESTUDIANTE:
        raise HTTPException(status_code=403, detail="Solo estudiantes pueden acceder")
    
    leccion = db.query(Leccion).filter(Leccion.id == leccion_id, Leccion.activa == True).first()
    if not leccion:
        raise HTTPException(status_code=404, detail="Lección no encontrada")
    
    # Verificar que el estudiante esté inscrito en el curso
    inscripcion = db.query(Inscripcion).filter(
        Inscripcion.usuario_id == current_user.id,
        Inscripcion.curso_id == leccion.curso_id,
        Inscripcion.activa == True
    ).first()
    
    if not inscripcion:
        raise HTTPException(status_code=403, detail="No estás inscrito en este curso")
    
    return leccion

@router.get("/estudiantes/me/lecciones/{leccion_id}/ejercicios", response_model=List[EjercicioResponse])
def obtener_ejercicios_leccion_estudiante(
    leccion_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Estudiante obtiene ejercicios de una lección"""
    if current_user.tipo_usuario != TipoUsuario.ESTUDIANTE:
        raise HTTPException(status_code=403, detail="Solo estudiantes pueden acceder")
    
    leccion = db.query(Leccion).filter(Leccion.id == leccion_id, Leccion.activa == True).first()
    if not leccion:
        raise HTTPException(status_code=404, detail="Lección no encontrada")
    
    # Verificar inscripción
    inscripcion = db.query(Inscripcion).filter(
        Inscripcion.usuario_id == current_user.id,
        Inscripcion.curso_id == leccion.curso_id,
        Inscripcion.activa == True
    ).first()
    
    if not inscripcion:
        raise HTTPException(status_code=403, detail="No estás inscrito en este curso")
    
    ejercicios = db.query(Ejercicio).filter(
        Ejercicio.leccion_id == leccion_id,
        Ejercicio.activo == True
    ).order_by(Ejercicio.orden).all()
    
    return ejercicios

@router.post("/estudiantes/me/ejercicios/{ejercicio_id}/intentar", response_model=RespuestaEjercicioResponse)
def intentar_ejercicio(
    ejercicio_id: int,
    respuesta_data: RespuestaEjercicioCreate,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Estudiante intenta resolver un ejercicio"""
    if current_user.tipo_usuario != TipoUsuario.ESTUDIANTE:
        raise HTTPException(status_code=403, detail="Solo estudiantes pueden responder ejercicios")
    
    ejercicio = db.query(Ejercicio).filter(Ejercicio.id == ejercicio_id).first()
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    
    # Verificar inscripción en el curso
    inscripcion = db.query(Inscripcion).filter(
        Inscripcion.usuario_id == current_user.id,
        Inscripcion.curso_id == ejercicio.leccion.curso_id,
        Inscripcion.activa == True
    ).first()
    
    if not inscripcion:
        raise HTTPException(status_code=403, detail="No estás inscrito en este curso")
    
    # Evaluar respuesta (simplificado - podrías agregar lógica más compleja)
    es_correcta = ejercicio.respuesta_correcta.lower().strip() == respuesta_data.respuesta_usuario.lower().strip()
    puntos_obtenidos = ejercicio.puntos_otorgados if es_correcta else 0
    
    # Guardar respuesta
    db_respuesta = RespuestaEjercicio(
        usuario_id=current_user.id,
        ejercicio_id=ejercicio_id,
        respuesta_usuario=respuesta_data.respuesta_usuario,
        es_correcta=es_correcta,
        puntos_obtenidos=puntos_obtenidos
    )
    
    db.add(db_respuesta)
    
    # Actualizar puntos del usuario si es correcta
    if es_correcta:
        current_user.puntos_totales += puntos_obtenidos
    
    db.commit()
    db.refresh(db_respuesta)
    
    return db_respuesta

@router.get("/estudiantes/me/respuestas/{ejercicio_id}")
def obtener_mis_respuestas_ejercicio(
    ejercicio_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Estudiante obtiene sus respuestas anteriores para un ejercicio"""
    if current_user.tipo_usuario != TipoUsuario.ESTUDIANTE:
        raise HTTPException(status_code=403, detail="Solo estudiantes pueden acceder")
    
    respuestas = db.query(RespuestaEjercicio).filter(
        RespuestaEjercicio.usuario_id == current_user.id,
        RespuestaEjercicio.ejercicio_id == ejercicio_id
    ).order_by(RespuestaEjercicio.fecha_respuesta.desc()).all()
    
    return respuestas

# ================================
# PROFESORES - ENDPOINTS CRUD DE PRIORIDAD ALTA
# ================================

@router.get("/profesores/me/cursos", response_model=List[CursoResponse])
def obtener_mis_cursos_profesor(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Profesor obtiene sus cursos creados"""
    if current_user.tipo_usuario != TipoUsuario.PROFESOR:
        raise HTTPException(status_code=403, detail="Solo profesores pueden acceder")
    
    cursos = db.query(Curso).filter(
        Curso.profesor_id == current_user.id,
        Curso.activo == True
    ).all()
    
    return cursos

@router.put("/profesores/cursos/{curso_id}", response_model=CursoResponse)
def actualizar_mi_curso(
    curso_id: int,
    curso_update: CursoUpdate,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Profesor actualiza su propio curso"""
    if current_user.tipo_usuario != TipoUsuario.PROFESOR:
        raise HTTPException(status_code=403, detail="Solo profesores pueden actualizar cursos")
    
    db_curso = db.query(Curso).filter(
        Curso.id == curso_id,
        Curso.profesor_id == current_user.id
    ).first()
    
    if not db_curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado o no tienes permisos")
    
    # Actualizar campos si se proporcionan
    update_data = curso_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_curso, field, value)
    
    db.commit()
    db.refresh(db_curso)
    return db_curso

@router.put("/profesores/lecciones/{leccion_id}", response_model=LeccionResponse)
def actualizar_mi_leccion(
    leccion_id: int,
    leccion_update: LeccionUpdate,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Profesor actualiza una lección de su curso"""
    if current_user.tipo_usuario != TipoUsuario.PROFESOR:
        raise HTTPException(status_code=403, detail="Solo profesores pueden actualizar lecciones")
    
    leccion = db.query(Leccion).filter(Leccion.id == leccion_id).first()
    if not leccion:
        raise HTTPException(status_code=404, detail="Lección no encontrada")
    
    # Verificar que la lección pertenece a un curso del profesor
    if leccion.curso.profesor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos para actualizar esta lección")
    
    # Actualizar campos si se proporcionan
    update_data = leccion_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(leccion, field, value)
    
    db.commit()
    db.refresh(leccion)
    return leccion

@router.put("/profesores/ejercicios/{ejercicio_id}", response_model=EjercicioResponse)
def actualizar_mi_ejercicio(
    ejercicio_id: int,
    ejercicio_update: EjercicioUpdate,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Profesor actualiza un ejercicio"""
    if current_user.tipo_usuario != TipoUsuario.PROFESOR:
        raise HTTPException(status_code=403, detail="Solo profesores pueden actualizar ejercicios")
    
    ejercicio = db.query(Ejercicio).filter(Ejercicio.id == ejercicio_id).first()
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    
    # Verificar permisos
    if ejercicio.leccion.curso.profesor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos para actualizar este ejercicio")
    
    # Actualizar campos si se proporcionan
    update_data = ejercicio_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(ejercicio, field, value)
    
    db.commit()
    db.refresh(ejercicio)
    return ejercicio

@router.get("/profesores/curso/{curso_id}/estudiantes-progreso")
def obtener_progreso_estudiantes_curso(
    curso_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Profesor obtiene el progreso de estudiantes en su curso"""
    if current_user.tipo_usuario != TipoUsuario.PROFESOR:
        raise HTTPException(status_code=403, detail="Solo profesores pueden acceder")
    
    # Verificar que el curso pertenece al profesor
    curso = db.query(Curso).filter(
        Curso.id == curso_id,
        Curso.profesor_id == current_user.id
    ).first()
    
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado o no tienes permisos")
    
    # Obtener inscripciones del curso
    inscripciones = db.query(Inscripcion).options(
        joinedload(Inscripcion.usuario)
    ).filter(
        Inscripcion.curso_id == curso_id,
        Inscripcion.activa == True
    ).all()
    
    estudiantes_progreso = []
    for inscripcion in inscripciones:
        # Obtener progreso detallado
        progreso_lecciones = db.query(ProgresoLeccion).filter(
            ProgresoLeccion.usuario_id == inscripcion.usuario_id,
            ProgresoLeccion.leccion_id.in_(
                db.query(Leccion.id).filter(Leccion.curso_id == curso_id)
            )
        ).all()
        
        lecciones_completadas = len([p for p in progreso_lecciones if p.estado == EstadoProgreso.COMPLETADO])
        total_lecciones = len(curso.lecciones)
        
        estudiantes_progreso.append({
            "estudiante": inscripcion.usuario,
            "fecha_inscripcion": inscripcion.fecha_inscripcion,
            "progreso_porcentaje": inscripcion.progreso_porcentaje,
            "lecciones_completadas": lecciones_completadas,
            "total_lecciones": total_lecciones,
            "puntos_obtenidos": inscripcion.puntos_obtenidos,
            "ultima_actividad": max([p.fecha_completion for p in progreso_lecciones if p.fecha_completion], default=None)
        })
    
    return {
        "curso": curso,
        "total_estudiantes": len(estudiantes_progreso),
        "estudiantes_progreso": estudiantes_progreso
    }

@router.put("/profesores/asignacion/{asignacion_id}/actualizar")
def actualizar_asignacion_curso(
    asignacion_id: int,
    fecha_limite: Optional[datetime] = None,
    observaciones: Optional[str] = None,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Profesor actualiza una asignación de curso"""
    if current_user.tipo_usuario != TipoUsuario.PROFESOR:
        raise HTTPException(status_code=403, detail="Solo profesores pueden actualizar asignaciones")
    
    asignacion = db.query(AsignacionCurso).filter(
        AsignacionCurso.id == asignacion_id,
        AsignacionCurso.profesor_id == current_user.id
    ).first()
    
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    
    if fecha_limite is not None:
        asignacion.fecha_limite = fecha_limite
    if observaciones is not None:
        asignacion.observaciones = observaciones
    
    db.commit()
    db.refresh(asignacion)
    
    return {"message": "Asignación actualizada exitosamente", "asignacion": asignacion}

# ================================
# ENDPOINTS CRUD ADICIONALES - LECCIONES Y EJERCICIOS
# ================================

@router.delete("/profesores/lecciones/{leccion_id}")
def eliminar_mi_leccion(
    leccion_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Profesor desactiva una lección de su curso"""
    if current_user.tipo_usuario != TipoUsuario.PROFESOR:
        raise HTTPException(status_code=403, detail="Solo profesores pueden eliminar lecciones")
    
    leccion = db.query(Leccion).filter(Leccion.id == leccion_id).first()
    if not leccion:
        raise HTTPException(status_code=404, detail="Lección no encontrada")
    
    # Verificar permisos
    if leccion.curso.profesor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar esta lección")
    
    # Marcar como inactiva
    leccion.activa = False
    db.commit()
    
    return {"message": "Lección eliminada exitosamente"}

@router.delete("/profesores/ejercicios/{ejercicio_id}")
def eliminar_mi_ejercicio(
    ejercicio_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Profesor desactiva un ejercicio"""
    if current_user.tipo_usuario != TipoUsuario.PROFESOR:
        raise HTTPException(status_code=403, detail="Solo profesores pueden eliminar ejercicios")
    
    ejercicio = db.query(Ejercicio).filter(Ejercicio.id == ejercicio_id).first()
    if not ejercicio:
        raise HTTPException(status_code=404, detail="Ejercicio no encontrado")
    
    # Verificar permisos
    if ejercicio.leccion.curso.profesor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permisos para eliminar este ejercicio")
    
    # Marcar como inactivo
    ejercicio.activo = False
    db.commit()
    
    return {"message": "Ejercicio eliminado exitosamente"}

# ================================
# ENDPOINTS PARA REPORTES Y ESTADÍSTICAS
# ================================

@router.get("/profesores/me/estadisticas")
def obtener_estadisticas_profesor(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Profesor obtiene sus estadísticas generales"""
    if current_user.tipo_usuario != TipoUsuario.PROFESOR:
        raise HTTPException(status_code=403, detail="Solo profesores pueden acceder")
    
    # Contar cursos creados
    cursos_creados = db.query(Curso).filter(
        Curso.profesor_id == current_user.id,
        Curso.activo == True
    ).count()
    
    # Contar estudiantes asignados
    estudiantes_asignados = db.query(ProfesorEstudiante).filter(
        ProfesorEstudiante.profesor_id == current_user.id,
        ProfesorEstudiante.activo == True
    ).count()
    
    # Contar asignaciones de cursos
    asignaciones_activas = db.query(AsignacionCurso).filter(
        AsignacionCurso.profesor_id == current_user.id
    ).count()
    
    # Calcular inscripciones totales en cursos del profesor
    inscripciones_totales = db.query(Inscripcion).join(Curso).filter(
        Curso.profesor_id == current_user.id,
        Inscripcion.activa == True
    ).count()
    
    return {
        "profesor_id": current_user.id,
        "cursos_creados": cursos_creados,
        "estudiantes_asignados": estudiantes_asignados,
        "asignaciones_activas": asignaciones_activas,
        "inscripciones_totales": inscripciones_totales
    }

@router.get("/admin/estadisticas-plataforma")
def obtener_estadisticas_plataforma(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Admin obtiene estadísticas generales de la plataforma"""
    if current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo administradores pueden acceder")
    
    # Contar usuarios por tipo
    total_estudiantes = db.query(Usuario).filter(
        Usuario.tipo_usuario == TipoUsuario.ESTUDIANTE,
        Usuario.activo == True
    ).count()
    
    total_profesores = db.query(Usuario).filter(
        Usuario.tipo_usuario == TipoUsuario.PROFESOR,
        Usuario.activo == True
    ).count()
    
    total_admins = db.query(Usuario).filter(
        Usuario.tipo_usuario == TipoUsuario.ADMIN,
        Usuario.activo == True
    ).count()
    
    # Contar cursos y lecciones
    total_cursos = db.query(Curso).filter(Curso.activo == True).count()
    total_lecciones = db.query(Leccion).filter(Leccion.activa == True).count()
    total_ejercicios = db.query(Ejercicio).filter(Ejercicio.activo == True).count()
    
    # Contar inscripciones y asignaciones
    total_inscripciones = db.query(Inscripcion).filter(Inscripcion.activa == True).count()
    total_asignaciones = db.query(AsignacionCurso).count()
    
    # Contar respuestas de ejercicios
    total_respuestas = db.query(RespuestaEjercicio).count()
    respuestas_correctas = db.query(RespuestaEjercicio).filter(
        RespuestaEjercicio.es_correcta == True
    ).count()
    
    return {
        "usuarios": {
            "estudiantes": total_estudiantes,
            "profesores": total_profesores,
            "administradores": total_admins,
            "total": total_estudiantes + total_profesores + total_admins
        },
        "contenido": {
            "cursos": total_cursos,
            "lecciones": total_lecciones,
            "ejercicios": total_ejercicios
        },
        "actividad": {
            "inscripciones": total_inscripciones,
            "asignaciones": total_asignaciones,
            "respuestas_totales": total_respuestas,
            "respuestas_correctas": respuestas_correctas,
            "tasa_acierto": round((respuestas_correctas / total_respuestas * 100), 2) if total_respuestas > 0 else 0
        }
    }

# ================================
# ENDPOINTS PARA BUSCAR Y FILTRAR
# ================================

@router.get("/buscar/usuarios")
def buscar_usuarios(
    q: str,
    tipo_usuario: TipoUsuario = None,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Buscar usuarios por nombre, apellido o email (solo Admin)"""
    if current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo administradores pueden buscar usuarios")
    
    query = db.query(Usuario).filter(Usuario.activo == True)
    
    # Filtrar por tipo si se especifica
    if tipo_usuario:
        query = query.filter(Usuario.tipo_usuario == tipo_usuario)
    
    # Buscar en nombre, apellido o email
    search_filter = (
        Usuario.nombre.ilike(f"%{q}%") |
        Usuario.apellido.ilike(f"%{q}%") |
        Usuario.email.ilike(f"%{q}%")
    )
    
    return query.filter(search_filter).limit(20).all()

@router.get("/buscar/cursos")
def buscar_cursos(
    q: str,
    area_id: int = None,
    nivel: NivelDificultad = None,
    db: Session = Depends(get_db)
):
    """Buscar cursos por título o descripción"""
    query = db.query(Curso).filter(Curso.activo == True)
    
    # Filtros opcionales
    if area_id:
        query = query.filter(Curso.area_matematica_id == area_id)
    if nivel:
        query = query.filter(Curso.nivel_dificultad == nivel)
    
    # Buscar en título o descripción
    search_filter = (
        Curso.titulo.ilike(f"%{q}%") |
        Curso.descripcion.ilike(f"%{q}%")
    )
    
    return query.filter(search_filter).limit(20).all()

# ================================
# ENDPOINTS DE NOTIFICACIONES Y ACTIVIDAD RECIENTE
# ================================

@router.get("/estudiantes/me/actividad-reciente")
def obtener_actividad_reciente_estudiante(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """Estudiante obtiene su actividad reciente"""
    if current_user.tipo_usuario != TipoUsuario.ESTUDIANTE:
        raise HTTPException(status_code=403, detail="Solo estudiantes pueden acceder")
    
    # Obtener respuestas recientes
    respuestas_recientes = db.query(RespuestaEjercicio).options(
        joinedload(RespuestaEjercicio.ejercicio).joinedload(Ejercicio.leccion).joinedload(Leccion.curso)
    ).filter(
        RespuestaEjercicio.usuario_id == current_user.id
    ).order_by(RespuestaEjercicio.fecha_respuesta.desc()).limit(limit).all()
    
    # Obtener progreso reciente de lecciones
    progreso_reciente = db.query(ProgresoLeccion).options(
        joinedload(ProgresoLeccion.leccion).joinedload(Leccion.curso)
    ).filter(
        ProgresoLeccion.usuario_id == current_user.id,
        ProgresoLeccion.fecha_completion.isnot(None)
    ).order_by(ProgresoLeccion.fecha_completion.desc()).limit(limit).all()
    
    return {
        "respuestas_recientes": respuestas_recientes,
        "lecciones_completadas_recientes": progreso_reciente
    }

@router.get("/profesores/me/actividad-estudiantes")
def obtener_actividad_estudiantes(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 20
):
    """Profesor obtiene actividad reciente de sus estudiantes"""
    if current_user.tipo_usuario != TipoUsuario.PROFESOR:
        raise HTTPException(status_code=403, detail="Solo profesores pueden acceder")
    
    # Obtener IDs de cursos del profesor
    cursos_ids = db.query(Curso.id).filter(
        Curso.profesor_id == current_user.id,
        Curso.activo == True
    ).subquery()
    
    # Obtener actividad reciente en los cursos del profesor
    actividad_reciente = db.query(ProgresoLeccion).options(
        joinedload(ProgresoLeccion.usuario),
        joinedload(ProgresoLeccion.leccion).joinedload(Leccion.curso)
    ).join(Leccion).filter(
        Leccion.curso_id.in_(cursos_ids),
        ProgresoLeccion.fecha_completion.isnot(None)
    ).order_by(ProgresoLeccion.fecha_completion.desc()).limit(limit).all()
    
    return {
        "actividad_reciente": actividad_reciente
    }

# ================================
# ENDPOINTS DE LOGROS Y GAMIFICACIÓN
# ================================

@router.get("/usuarios/{usuario_id}/logros", response_model=List[dict])
def obtener_logros_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener logros de un usuario"""
    # Verificar permisos - el usuario puede ver sus propios logros, admin puede ver todos
    if current_user.id != usuario_id and current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver estos logros")
    
    # Verificar que el usuario existe
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Obtener logros del usuario
    logros_usuario = db.query(LogroUsuario).options(
        joinedload(LogroUsuario.logro)
    ).filter(LogroUsuario.usuario_id == usuario_id).all()
    
    logros_data = []
    for logro_usuario in logros_usuario:
        logros_data.append({
            "id": logro_usuario.logro.id,
            "nombre": logro_usuario.logro.nombre,
            "descripcion": logro_usuario.logro.descripcion,
            "icono": logro_usuario.logro.icono,
            "fecha_obtencion": logro_usuario.fecha_obtencion,
            "puntos_requeridos": logro_usuario.logro.puntos_requeridos
        })
    
    return logros_data

@router.get("/logros", response_model=List[dict])
def obtener_todos_logros(db: Session = Depends(get_db)):
    """Obtener todos los logros disponibles"""
    logros = db.query(Logro).filter(Logro.activo == True).all()
    
    logros_data = []
    for logro in logros:
        logros_data.append({
            "id": logro.id,
            "nombre": logro.nombre,
            "descripcion": logro.descripcion,
            "icono": logro.icono,
            "puntos_requeridos": logro.puntos_requeridos
        })
    
    return logros_data

@router.get("/usuarios/{usuario_id}/ranking")
def obtener_ranking_usuario(
    usuario_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener posición del usuario en el ranking global"""
    # Verificar permisos
    if current_user.id != usuario_id and current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver este ranking")
    
    # Verificar que el usuario existe
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Obtener ranking global (ordenado por puntos totales)
    usuarios_ordenados = db.query(Usuario).filter(
        Usuario.activo == True,
        Usuario.tipo_usuario == TipoUsuario.ESTUDIANTE
    ).order_by(Usuario.puntos_totales.desc()).all()
    
    # Encontrar posición del usuario
    posicion = None
    for i, u in enumerate(usuarios_ordenados):
        if u.id == usuario_id:
            posicion = i + 1
            break
    
    return {
        "usuario_id": usuario_id,
        "puntos_totales": usuario.puntos_totales,
        "posicion_ranking": posicion,
        "total_estudiantes": len(usuarios_ordenados),
        "nivel_actual": usuario.nivel_actual
    }

@router.get("/ranking/global")
def obtener_ranking_global(
    limit: int = 20,
    skip: int = 0,
    db: Session = Depends(get_db)
):
    """Obtener ranking global de estudiantes"""
    usuarios_ranking = db.query(Usuario).filter(
        Usuario.activo == True,
        Usuario.tipo_usuario == TipoUsuario.ESTUDIANTE
    ).order_by(Usuario.puntos_totales.desc()).offset(skip).limit(limit).all()
    
    ranking_data = []
    for i, usuario in enumerate(usuarios_ranking):
        ranking_data.append({
            "posicion": skip + i + 1,
            "usuario": {
                "id": usuario.id,
                "nombre": usuario.nombre,
                "apellido": usuario.apellido,
                "avatar_url": usuario.avatar_url
            },
            "puntos_totales": usuario.puntos_totales,
            "nivel_actual": usuario.nivel_actual
        })
    
    return ranking_data

@router.post("/admin/logros", response_model=dict, status_code=status.HTTP_201_CREATED)
def crear_logro(
    logro_data: dict,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Admin crea un nuevo logro"""
    if current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo administradores pueden crear logros")
    
    nuevo_logro = Logro(
        nombre=logro_data.get("nombre"),
        descripcion=logro_data.get("descripcion"),
        icono=logro_data.get("icono"),
        puntos_requeridos=logro_data.get("puntos_requeridos", 0),
        condicion_json=logro_data.get("condicion_json")
    )
    
    db.add(nuevo_logro)
    db.commit()
    db.refresh(nuevo_logro)
    
    return {
        "id": nuevo_logro.id,
        "nombre": nuevo_logro.nombre,
        "descripcion": nuevo_logro.descripcion,
        "icono": nuevo_logro.icono,
        "puntos_requeridos": nuevo_logro.puntos_requeridos
    }

@router.post("/admin/usuarios/{usuario_id}/otorgar-logro")
def otorgar_logro_usuario(
    usuario_id: int,
    logro_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Admin otorga un logro a un usuario"""
    if current_user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Solo administradores pueden otorgar logros")
    
    # Verificar que el usuario y logro existen
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    logro = db.query(Logro).filter(Logro.id == logro_id).first()
    if not logro:
        raise HTTPException(status_code=404, detail="Logro no encontrado")
    
    # Verificar si ya tiene el logro
    logro_existente = db.query(LogroUsuario).filter(
        LogroUsuario.usuario_id == usuario_id,
        LogroUsuario.logro_id == logro_id
    ).first()
    
    if logro_existente:
        raise HTTPException(status_code=400, detail="El usuario ya tiene este logro")
    
    # Otorgar logro
    nuevo_logro_usuario = LogroUsuario(
        usuario_id=usuario_id,
        logro_id=logro_id
    )
    
    db.add(nuevo_logro_usuario)
    db.commit()
    
    return {"message": "Logro otorgado exitosamente"}

# ================================
# ENDPOINTS DE ESTADÍSTICAS DETALLADAS
# ================================

@router.get("/usuarios/{usuario_id}/estadisticas-detalladas")
def obtener_estadisticas_detalladas(
    usuario_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas detalladas de un usuario"""
    # Verificar permisos
    if current_user.id != usuario_id and current_user.tipo_usuario not in [TipoUsuario.ADMIN, TipoUsuario.PROFESOR]:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver estas estadísticas")
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Si es profesor, verificar que el estudiante le está asignado
    if current_user.tipo_usuario == TipoUsuario.PROFESOR and current_user.id != usuario_id:
        relacion = db.query(ProfesorEstudiante).filter(
            ProfesorEstudiante.profesor_id == current_user.id,
            ProfesorEstudiante.estudiante_id == usuario_id,
            ProfesorEstudiante.activo == True
        ).first()
        
        if not relacion:
            raise HTTPException(status_code=403, detail="No tienes permisos para ver este estudiante")
    
    # Obtener estadísticas detalladas
    inscripciones = db.query(Inscripcion).filter(Inscripcion.usuario_id == usuario_id).all()
    progreso_lecciones = db.query(ProgresoLeccion).filter(ProgresoLeccion.usuario_id == usuario_id).all()
    respuestas = db.query(RespuestaEjercicio).filter(RespuestaEjercicio.usuario_id == usuario_id).all()
    logros = db.query(LogroUsuario).filter(LogroUsuario.usuario_id == usuario_id).count()
    
    # Calcular estadísticas por área matemática
    estadisticas_areas = {}
    
    # Obtener cursos por área
    for inscripcion in inscripciones:
        curso = inscripcion.curso
        area_id = curso.area_matematica_id
        
        if area_id not in estadisticas_areas:
            estadisticas_areas[area_id] = {
                "area_nombre": curso.area_matematica.nombre if curso.area_matematica else "Sin área",
                "cursos_inscritos": 0,
                "cursos_completados": 0,
                "progreso_promedio": 0.0
            }
        
        estadisticas_areas[area_id]["cursos_inscritos"] += 1
        if inscripcion.progreso_porcentaje == 100:
            estadisticas_areas[area_id]["cursos_completados"] += 1
    
    return {
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "email": usuario.email
        },
        "resumen": {
            "puntos_totales": usuario.puntos_totales,
            "nivel_actual": usuario.nivel_actual,
            "cursos_inscritos": len(inscripciones),
            "cursos_completados": len([i for i in inscripciones if i.progreso_porcentaje == 100]),
            "lecciones_completadas": len([p for p in progreso_lecciones if p.estado == EstadoProgreso.COMPLETADO]),
            "ejercicios_resueltos": len(respuestas),
            "ejercicios_correctos": len([r for r in respuestas if r.es_correcta]),
            "logros_obtenidos": logros
        },
        "estadisticas_por_area": list(estadisticas_areas.values()),
        "actividad_reciente": {
            "ultima_respuesta": max([r.fecha_respuesta for r in respuestas], default=None),
            "ultima_leccion_completada": max([p.fecha_completion for p in progreso_lecciones if p.fecha_completion], default=None)
        }
    }
