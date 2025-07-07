"""
Script para poblar la base de datos con datos de ejemplo
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import *
from app.auth import get_password_hash
import json

def crear_datos_ejemplo():
    db = SessionLocal()
    
    try:
        print("🔧 Creando datos de ejemplo...")
        
        # 1. Crear áreas matemáticas
        areas = [
            AreaMatematica(
                nombre="Álgebra",
                descripcion="Operaciones algebraicas, ecuaciones y sistemas",
                icono="algebra",
                color="#FF6B6B",
                orden=1
            ),
            AreaMatematica(
                nombre="Geometría",
                descripcion="Figuras geométricas, área, perímetro y volumen",
                icono="geometry",
                color="#4ECDC4",
                orden=2
            ),
            AreaMatematica(
                nombre="Cálculo",
                descripcion="Derivadas, integrales y límites",
                icono="calculus",
                color="#45B7D1",
                orden=3
            ),
            AreaMatematica(
                nombre="Estadística",
                descripcion="Probabilidad, estadística descriptiva y inferencial",
                icono="statistics",
                color="#FFA07A",
                orden=4
            )
        ]
        
        for area in areas:
            db.add(area)
        db.commit()
        print("✅ Áreas matemáticas creadas")
        
        # 2. Crear usuarios de ejemplo
        usuarios = [
            Usuario(
                nombre="Admin",
                apellido="Sistema",
                email="admin@edumath.com",
                password_hash=get_password_hash("admin123"),
                tipo_usuario=TipoUsuario.ADMIN,
                puntos_totales=1000,
                nivel_actual=5
            ),
            Usuario(
                nombre="Prof. María",
                apellido="González",
                email="maria@edumath.com",
                password_hash=get_password_hash("profesor123"),
                tipo_usuario=TipoUsuario.PROFESOR,
                puntos_totales=500,
                nivel_actual=3
            ),
            Usuario(
                nombre="Juan",
                apellido="Pérez",
                email="juan@estudiante.com",
                password_hash=get_password_hash("estudiante123"),
                tipo_usuario=TipoUsuario.ESTUDIANTE,
                puntos_totales=150,
                nivel_actual=2
            ),
            Usuario(
                nombre="Ana",
                apellido="López",
                email="ana@estudiante.com",
                password_hash=get_password_hash("estudiante123"),
                tipo_usuario=TipoUsuario.ESTUDIANTE,
                puntos_totales=200,
                nivel_actual=2
            )
        ]
        
        for usuario in usuarios:
            db.add(usuario)
        db.commit()
        print("✅ Usuarios creados")
        
        # 3. Crear cursos
        algebra = db.query(AreaMatematica).filter(AreaMatematica.nombre == "Álgebra").first()
        geometria = db.query(AreaMatematica).filter(AreaMatematica.nombre == "Geometría").first()
        profesor = db.query(Usuario).filter(Usuario.email == "maria@edumath.com").first()
        
        cursos = [
            Curso(
                titulo="Álgebra Básica",
                descripcion="Introducción al álgebra: variables, expresiones y ecuaciones lineales",
                objetivos="Dominar las operaciones algebraicas básicas y resolver ecuaciones de primer grado",
                nivel_dificultad=NivelDificultad.BASICO,
                duracion_estimada=20,
                area_matematica_id=algebra.id,
                profesor_id=profesor.id
            ),
            Curso(
                titulo="Geometría Plana",
                descripcion="Estudio de figuras geométricas en el plano: triángulos, cuadriláteros y círculos",
                objetivos="Calcular áreas, perímetros y resolver problemas geométricos básicos",
                nivel_dificultad=NivelDificultad.BASICO,
                duracion_estimada=25,
                area_matematica_id=geometria.id,
                profesor_id=profesor.id
            ),
            Curso(
                titulo="Álgebra Intermedia",
                descripcion="Ecuaciones cuadráticas, sistemas de ecuaciones y funciones",
                objetivos="Resolver problemas más complejos utilizando técnicas algebraicas avanzadas",
                nivel_dificultad=NivelDificultad.INTERMEDIO,
                duracion_estimada=30,
                area_matematica_id=algebra.id,
                profesor_id=profesor.id
            )
        ]
        
        for curso in cursos:
            db.add(curso)
        db.commit()
        print("✅ Cursos creados")
        
        # 4. Crear lecciones para Álgebra Básica
        algebra_basica = db.query(Curso).filter(Curso.titulo == "Álgebra Básica").first()
        
        lecciones_algebra = [
            Leccion(
                titulo="Introducción a las Variables",
                descripcion="¿Qué son las variables y cómo se usan en matemáticas?",
                contenido="""
# Introducción a las Variables

Una **variable** es un símbolo (generalmente una letra) que representa un número desconocido.

## Ejemplos:
- x, y, z son variables comunes
- En la expresión 2x + 3, 'x' es la variable

## ¿Por qué usamos variables?
- Para resolver problemas generales
- Para representar cantidades desconocidas
- Para crear fórmulas reutilizables
                """,
                orden=1,
                puntos_otorgados=10,
                tiempo_estimado=15,
                curso_id=algebra_basica.id
            ),
            Leccion(
                titulo="Operaciones con Variables",
                descripcion="Suma, resta, multiplicación y división con expresiones algebraicas",
                contenido="""
# Operaciones con Variables

## Suma y Resta
- 2x + 3x = 5x (términos semejantes)
- 5y - 2y = 3y
- x + 2y no se puede simplificar (términos diferentes)

## Multiplicación
- 2x × 3y = 6xy
- x × x = x²

## División
- 6x ÷ 2 = 3x
- x² ÷ x = x
                """,
                orden=2,
                puntos_otorgados=15,
                tiempo_estimado=20,
                curso_id=algebra_basica.id
            ),
            Leccion(
                titulo="Ecuaciones Lineales",
                descripcion="Resolución de ecuaciones de primer grado",
                contenido="""
# Ecuaciones Lineales

Una ecuación lineal tiene la forma: ax + b = c

## Pasos para resolver:
1. Aislar el término con la variable
2. Aplicar operaciones inversas
3. Verificar la solución

## Ejemplo:
2x + 5 = 13
2x = 13 - 5
2x = 8
x = 4
                """,
                orden=3,
                puntos_otorgados=20,
                tiempo_estimado=30,
                curso_id=algebra_basica.id
            )
        ]
        
        for leccion in lecciones_algebra:
            db.add(leccion)
        db.commit()
        print("✅ Lecciones creadas")
        
        # 5. Crear ejercicios
        leccion_variables = db.query(Leccion).filter(Leccion.titulo == "Introducción a las Variables").first()
        leccion_operaciones = db.query(Leccion).filter(Leccion.titulo == "Operaciones con Variables").first()
        
        ejercicios = [
            Ejercicio(
                titulo="Identificar Variables",
                enunciado="¿Cuál de las siguientes es una variable en la expresión 3x + 7?",
                tipo_ejercicio=TipoEjercicio.OPCION_MULTIPLE,
                nivel_dificultad=NivelDificultad.BASICO,
                puntos_otorgados=5,
                orden=1,
                opciones_json=json.dumps(["3", "x", "7", "+"]),
                respuesta_correcta="x",
                explicacion="La variable es 'x' porque representa un valor desconocido.",
                leccion_id=leccion_variables.id
            ),
            Ejercicio(
                titulo="Términos Semejantes",
                enunciado="Simplifica la expresión: 4x + 2x",
                tipo_ejercicio=TipoEjercicio.DESARROLLO,
                nivel_dificultad=NivelDificultad.BASICO,
                puntos_otorgados=10,
                orden=1,
                respuesta_correcta="6x",
                explicacion="4x + 2x = (4+2)x = 6x",
                leccion_id=leccion_operaciones.id
            ),
            Ejercicio(
                titulo="Multiplicación de Variables",
                enunciado="¿Cuál es el resultado de 3x × 2y?",
                tipo_ejercicio=TipoEjercicio.OPCION_MULTIPLE,
                nivel_dificultad=NivelDificultad.BASICO,
                puntos_otorgados=5,
                orden=2,
                opciones_json=json.dumps(["5xy", "6xy", "6x", "6y"]),
                respuesta_correcta="6xy",
                explicacion="3x × 2y = 3 × 2 × x × y = 6xy",
                leccion_id=leccion_operaciones.id
            )
        ]
        
        for ejercicio in ejercicios:
            db.add(ejercicio)
        db.commit()
        print("✅ Ejercicios creados")
        
        # 6. Crear logros
        logros = [
            Logro(
                nombre="Primer Paso",
                descripcion="Completar tu primera lección",
                icono="first_step",
                puntos_requeridos=10,
                condicion_json=json.dumps({"tipo": "lecciones_completadas", "cantidad": 1})
            ),
            Logro(
                nombre="Estudiante Dedicado",
                descripcion="Completar 5 lecciones",
                icono="dedicated",
                puntos_requeridos=50,
                condicion_json=json.dumps({"tipo": "lecciones_completadas", "cantidad": 5})
            ),
            Logro(
                nombre="Maestro del Álgebra",
                descripcion="Completar un curso de álgebra",
                icono="algebra_master",
                puntos_requeridos=100,
                condicion_json=json.dumps({"tipo": "curso_completado", "area": "Álgebra"})
            ),
            Logro(
                nombre="Coleccionista de Puntos",
                descripcion="Obtener 500 puntos",
                icono="point_collector",
                puntos_requeridos=500,
                condicion_json=json.dumps({"tipo": "puntos_totales", "cantidad": 500})
            )
        ]
        
        for logro in logros:
            db.add(logro)
        db.commit()
        print("✅ Logros creados")
        
        print("\n🎉 ¡Datos de ejemplo creados exitosamente!")
        print("\n📋 Resumen:")
        print(f"   👥 {len(usuarios)} usuarios creados")
        print(f"   📚 {len(areas)} áreas matemáticas")
        print(f"   🎓 {len(cursos)} cursos")
        print(f"   📖 {len(lecciones_algebra)} lecciones")
        print(f"   ✏️ {len(ejercicios)} ejercicios")
        print(f"   🏆 {len(logros)} logros")
        
        print("\n🔐 Credenciales de prueba:")
        print("   Admin: admin@edumath.com / admin123")
        print("   Profesor: maria@edumath.com / profesor123")
        print("   Estudiante: juan@estudiante.com / estudiante123")
        print("   Estudiante: ana@estudiante.com / estudiante123")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    crear_datos_ejemplo()
