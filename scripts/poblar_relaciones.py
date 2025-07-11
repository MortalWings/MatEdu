"""
Script para poblar las nuevas tablas de relación profesor-estudiante
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import *
from datetime import datetime, timedelta

def poblar_relaciones():
    """Poblar las tablas de relación profesor-estudiante"""
    db = SessionLocal()
    
    try:
        print("🔧 Poblando relaciones profesor-estudiante...")
        
        # Verificar que los usuarios existen
        admin = db.query(Usuario).filter(Usuario.email == "admin@edumath.com").first()
        maria = db.query(Usuario).filter(Usuario.email == "maria@edumath.com").first()
        juan = db.query(Usuario).filter(Usuario.email == "juan@estudiante.com").first()
        
        if not admin or not maria or not juan:
            print("❌ Error: No se encontraron los usuarios básicos. Ejecuta primero poblar_db.py")
            return
        
        print(f"✅ Usuarios encontrados:")
        print(f"   - Admin: {admin.nombre} {admin.apellido} (ID: {admin.id})")
        print(f"   - Profesor: {maria.nombre} {maria.apellido} (ID: {maria.id})")
        print(f"   - Estudiante: {juan.nombre} {juan.apellido} (ID: {juan.id})")
        
        # 1. Crear relación profesor-estudiante
        print("📚 Creando relación profesor-estudiante...")
        
        relacion_existente = db.query(ProfesorEstudiante).filter(
            ProfesorEstudiante.profesor_id == maria.id,
            ProfesorEstudiante.estudiante_id == juan.id
        ).first()
        
        if not relacion_existente:
            relacion = ProfesorEstudiante(
                profesor_id=maria.id,
                estudiante_id=juan.id
            )
            db.add(relacion)
            print(f"   ✅ María (profesor) ahora tiene a Juan (estudiante)")
        else:
            print(f"   ⚠️ La relación ya existe")
        
        # 2. Verificar que hay cursos
        cursos = db.query(Curso).all()
        if not cursos:
            print("❌ Error: No hay cursos en la base de datos")
            return
        
        print(f"✅ Cursos disponibles: {len(cursos)}")
        for curso in cursos[:3]:  # Mostrar solo los primeros 3
            print(f"   - {curso.titulo} (ID: {curso.id})")
        
        # 3. Crear asignaciones de cursos
        print("🎯 Creando asignaciones de cursos...")
        
        for i, curso in enumerate(cursos[:2]):  # Asignar los primeros 2 cursos
            asignacion_existente = db.query(AsignacionCurso).filter(
                AsignacionCurso.profesor_id == maria.id,
                AsignacionCurso.estudiante_id == juan.id,
                AsignacionCurso.curso_id == curso.id
            ).first()
            
            if not asignacion_existente:
                asignacion = AsignacionCurso(
                    profesor_id=maria.id,
                    estudiante_id=juan.id,
                    curso_id=curso.id,
                    observaciones=f"Curso {i+1} asignado para reforzar conocimientos",
                    fecha_limite=datetime.now() + timedelta(days=90 + (i*30))
                )
                db.add(asignacion)
                print(f"   ✅ Curso '{curso.titulo}' asignado a Juan")
            else:
                print(f"   ⚠️ Curso '{curso.titulo}' ya estaba asignado")
        
        # 4. Commit de todos los cambios
        db.commit()
        print("💾 Cambios guardados en la base de datos")
        
        # 5. Verificar los datos creados
        print("\n📊 Resumen de datos creados:")
        
        relaciones = db.query(ProfesorEstudiante).all()
        print(f"   - Relaciones profesor-estudiante: {len(relaciones)}")
        
        asignaciones = db.query(AsignacionCurso).all()
        print(f"   - Asignaciones de cursos: {len(asignaciones)}")
        
        print("\n🎉 ¡Datos de relación creados exitosamente!")
        print("📋 Ahora puedes probar los endpoints:")
        print("   - GET /profesores/me/estudiantes (como María)")
        print("   - GET /estudiantes/me/cursos-asignados (como Juan)")
        print("   - GET /profesores/me/asignaciones (como María)")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    poblar_relaciones()
