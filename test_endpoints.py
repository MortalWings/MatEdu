"""
Script para probar los endpoints de la lógica de negocio
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def login_user(email, password):
    """Login y obtener token"""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        data = response.json()
        return data["access_token"]
    else:
        print(f"❌ Error en login: {response.status_code} - {response.text}")
        return None

def test_profesor_endpoints():
    """Probar endpoints del profesor María"""
    print("👩‍🏫 === PRUEBAS PROFESOR MARÍA ===")
    
    # Login como María (profesor)
    token = login_user("maria@edumath.com", "profesor123")
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Ver mis estudiantes
    print("\n1️⃣ Consultando estudiantes asignados...")
    response = requests.get(f"{BASE_URL}/profesores/me/estudiantes", headers=headers)
    if response.status_code == 200:
        estudiantes = response.json()
        print(f"✅ Estudiantes encontrados: {len(estudiantes)}")
        for est in estudiantes:
            print(f"   - {est['nombre']} {est['apellido']} ({est['email']})")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
    
    # 2. Ver mis asignaciones de cursos
    print("\n2️⃣ Consultando asignaciones de cursos...")
    response = requests.get(f"{BASE_URL}/profesores/me/asignaciones", headers=headers)
    if response.status_code == 200:
        asignaciones = response.json()
        print(f"✅ Asignaciones encontradas: {len(asignaciones)}")
        for asig in asignaciones:
            print(f"   - Curso: {asig['curso']['titulo']}")
            print(f"     Estudiante: {asig['estudiante']['nombre']} {asig['estudiante']['apellido']}")
            print(f"     Fecha límite: {asig['fecha_limite']}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
    
    # 3. Ver todos los cursos disponibles
    print("\n3️⃣ Consultando cursos disponibles...")
    response = requests.get(f"{BASE_URL}/cursos", headers=headers)
    if response.status_code == 200:
        cursos = response.json()
        print(f"✅ Cursos disponibles: {len(cursos)}")
        for curso in cursos:
            print(f"   - {curso['titulo']} (Nivel: {curso['nivel_dificultad']})")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

def test_estudiante_endpoints():
    """Probar endpoints del estudiante Juan"""
    print("\n\n👨‍🎓 === PRUEBAS ESTUDIANTE JUAN ===")
    
    # Login como Juan (estudiante)
    token = login_user("juan@estudiante.com", "estudiante123")
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Ver mis cursos asignados
    print("\n1️⃣ Consultando cursos asignados...")
    response = requests.get(f"{BASE_URL}/estudiantes/me/cursos-asignados", headers=headers)
    if response.status_code == 200:
        cursos = response.json()
        print(f"✅ Cursos asignados: {len(cursos)}")
        for curso in cursos:
            print(f"   - {curso['curso']['titulo']}")
            print(f"     Profesor: {curso['profesor']['nombre']} {curso['profesor']['apellido']}")
            print(f"     Fecha límite: {curso['fecha_limite']}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
    
    # 2. Ver todos los cursos (debe estar restringido a los asignados)
    print("\n2️⃣ Consultando cursos disponibles...")
    response = requests.get(f"{BASE_URL}/cursos", headers=headers)
    if response.status_code == 200:
        cursos = response.json()
        print(f"✅ Cursos visibles para estudiante: {len(cursos)}")
        for curso in cursos:
            print(f"   - {curso['titulo']} (Nivel: {curso['nivel_dificultad']})")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

def test_admin_endpoints():
    """Probar endpoints del administrador"""
    print("\n\n👑 === PRUEBAS ADMINISTRADOR ===")
    
    # Login como Admin
    token = login_user("admin@edumath.com", "admin123")
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Ver mi perfil como admin
    print("\n1️⃣ Consultando mi perfil de admin...")
    response = requests.get(f"{BASE_URL}/usuarios/me", headers=headers)
    if response.status_code == 200:
        admin_data = response.json()
        print(f"✅ Admin: {admin_data['nombre']} {admin_data['apellido']} ({admin_data['tipo_usuario']})")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
    
    # 2. Ver todos los cursos
    print("\n2️⃣ Consultando todos los cursos...")
    response = requests.get(f"{BASE_URL}/cursos", headers=headers)
    if response.status_code == 200:
        cursos = response.json()
        print(f"✅ Cursos totales: {len(cursos)}")
        for curso in cursos:
            print(f"   - {curso['titulo']} (Nivel: {curso['nivel_dificultad']})")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

def main():
    """Ejecutar todas las pruebas"""
    print("🧪 === PRUEBAS DE ENDPOINTS EDUMATH ===")
    print("🌐 Conectando a:", BASE_URL)
    
    try:
        # Verificar que el servidor esté activo
        response = requests.get("http://localhost:8000/")
        if response.status_code != 200:
            print("❌ El servidor no está activo")
            return
        
        print("✅ Servidor activo")
        
        # Ejecutar pruebas
        test_profesor_endpoints()
        test_estudiante_endpoints()
        test_admin_endpoints()
        
        print("\n🎉 === PRUEBAS COMPLETADAS ===")
        
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor. ¿Está FastAPI ejecutándose?")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()
