"""
Script para verificar usuarios en la base de datos
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Usuario
from passlib.context import CryptContext

def verificar_usuarios():
    """Verificar usuarios y sus contraseñas"""
    db = SessionLocal()
    
    try:
        usuarios = db.query(Usuario).all()
        print(f"👥 Usuarios encontrados: {len(usuarios)}")
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        for usuario in usuarios:
            print(f"\n📧 Email: {usuario.email}")
            print(f"👤 Nombre: {usuario.nombre} {usuario.apellido}")
            print(f"🎭 Rol: {usuario.tipo_usuario}")
            print(f"✅ Activo: {usuario.activo}")
            
            # Verificar contraseñas
            contraseñas_test = ["123456", "admin123", "password"]
            for pwd in contraseñas_test:
                if pwd_context.verify(pwd, usuario.password_hash):
                    print(f"🔑 Contraseña correcta: {pwd}")
                    break
            else:
                print(f"🔐 Hash: {usuario.password_hash[:50]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verificar_usuarios()
