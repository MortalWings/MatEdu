from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List
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
