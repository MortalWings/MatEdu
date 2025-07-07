# 🧮 EduMath - Plataforma de Matemáticas

Una plataforma educativa moderna desarrollada con **FastAPI** para el aprendizaje interactivo de matemáticas.

## 🌟 Características

### 👥 **Sistema de Usuarios**
- ✅ Registro y autenticación con JWT
- ✅ Roles: Estudiante, Profesor, Administrador
- ✅ Perfiles personalizados con avatares
- ✅ Sistema de puntos y niveles

### 📚 **Gestión de Contenido**
- ✅ Áreas matemáticas organizadas (Álgebra, Geometría, Cálculo, Estadística)
- ✅ Cursos por niveles de dificultad
- ✅ Lecciones con contenido en Markdown
- ✅ Videos educativos integrados

### ✏️ **Ejercicios Interactivos**
- ✅ Múltiples tipos: Opción múltiple, Desarrollo, Verdadero/Falso
- ✅ Soporte para fórmulas matemáticas (LaTeX)
- ✅ Evaluación automática con explicaciones
- ✅ Sistema de puntuación por dificultad

### 📊 **Seguimiento de Progreso**
- ✅ Progreso detallado por lección y curso
- ✅ Estadísticas completas de aprendizaje
- ✅ Tiempo dedicado al estudio
- ✅ Porcentaje de completitud

### 🏆 **Gamificación**
- ✅ Sistema de puntos por actividad
- ✅ Logros y medallas
- ✅ Niveles de usuario
- ✅ Racha de estudio (próximamente)

## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.8+
- pip

### 1. Clonar el repositorio
```bash
git clone <tu-repositorio>
cd pfm-back
```

### 2. Crear entorno virtual
```bash
python -m venv env
```

### 3. Activar entorno virtual
```bash
# Windows
.\\env\\Scripts\\activate

# Linux/Mac
source env/bin/activate
```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 5. Poblar base de datos con datos de ejemplo
```bash
python scripts/poblar_db.py
```

### 6. Ejecutar la aplicación
```bash
python run.py
```

## 📖 Uso de la API

### 🌐 **Endpoints Principales**

La aplicación estará disponible en: `http://127.0.0.1:8000`

#### Documentación Automática
- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

### 🔐 **Autenticación**

#### Registro de Usuario
```http
POST /api/v1/auth/registro
Content-Type: application/json

{
    "nombre": "Juan",
    "apellido": "Pérez",
    "email": "juan@ejemplo.com",
    "password": "mi_password_segura",
    "tipo_usuario": "estudiante",
    "fecha_nacimiento": "2000-01-15T00:00:00"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "email": "juan@ejemplo.com",
    "password": "mi_password_segura"
}
```

**Respuesta:**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
}
```

#### Usar Token en Requests
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 📚 **Gestión de Cursos**

#### Obtener Cursos
```http
GET /api/v1/cursos?area_id=1&nivel=basico
```

#### Inscribirse a un Curso
```http
POST /api/v1/cursos/{curso_id}/inscribirse
Authorization: Bearer <token>
```

#### Ver Mis Cursos
```http
GET /api/v1/usuarios/me/cursos
Authorization: Bearer <token>
```

### ✏️ **Ejercicios y Respuestas**

#### Obtener Ejercicios de una Lección
```http
GET /api/v1/lecciones/{leccion_id}/ejercicios
```

#### Responder Ejercicio
```http
POST /api/v1/ejercicios/{ejercicio_id}/responder
Authorization: Bearer <token>
Content-Type: application/json

{
    "ejercicio_id": 1,
    "respuesta_usuario": "6x"
}
```

### 📊 **Progreso y Estadísticas**

#### Ver Progreso en un Curso
```http
GET /api/v1/usuarios/me/progreso/{curso_id}
Authorization: Bearer <token>
```

#### Estadísticas del Usuario
```http
GET /api/v1/usuarios/{usuario_id}/estadisticas
```

## 🗄️ **Estructura de la Base de Datos**

### Tablas Principales

1. **usuarios** - Información de usuarios
2. **areas_matematicas** - Áreas temáticas (Álgebra, Geometría, etc.)
3. **cursos** - Cursos disponibles
4. **lecciones** - Lecciones dentro de cada curso
5. **ejercicios** - Ejercicios de cada lección
6. **inscripciones** - Relación usuario-curso
7. **progreso_lecciones** - Progreso del usuario por lección
8. **respuestas_ejercicios** - Respuestas de los usuarios
9. **logros** - Logros disponibles
10. **logros_usuario** - Logros obtenidos por usuario

### Relaciones Principales
```
Usuario 1:N Inscripcion N:1 Curso
Curso 1:N Leccion 1:N Ejercicio
Usuario 1:N ProgresoLeccion N:1 Leccion
Usuario 1:N RespuestaEjercicio N:1 Ejercicio
```

## 🧪 **Datos de Prueba**

Después de ejecutar `scripts/poblar_db.py`, tendrás:

### 👥 **Usuarios de Prueba**
| Email | Password | Rol | Descripción |
|-------|----------|-----|-------------|
| admin@edumath.com | admin123 | Admin | Administrador del sistema |
| maria@edumath.com | profesor123 | Profesor | Profesora de matemáticas |
| juan@estudiante.com | estudiante123 | Estudiante | Estudiante ejemplo 1 |
| ana@estudiante.com | estudiante123 | Estudiante | Estudiante ejemplo 2 |

### 📚 **Contenido de Ejemplo**
- 4 áreas matemáticas
- 3 cursos (Álgebra Básica, Geometría Plana, Álgebra Intermedia)
- 3 lecciones en Álgebra Básica
- 3 ejercicios variados
- 4 logros configurados

## 🔧 **Tecnologías Utilizadas**

- **FastAPI** - Framework web moderno y rápido
- **SQLAlchemy** - ORM para base de datos
- **Pydantic** - Validación de datos
- **SQLite** - Base de datos ligera
- **JWT** - Autenticación con tokens
- **Bcrypt** - Hash seguro de contraseñas
- **Uvicorn** - Servidor ASGI

## 📁 **Estructura del Proyecto**

```
pfm-back/
├── app/
│   ├── __init__.py
│   ├── main.py          # Aplicación principal
│   ├── database.py      # Configuración de BD
│   ├── models.py        # Modelos SQLAlchemy + Pydantic
│   ├── routes.py        # Endpoints de la API
│   └── auth.py          # Sistema de autenticación
├── scripts/
│   └── poblar_db.py     # Script para datos de ejemplo
├── env/                 # Entorno virtual
├── edumath.db          # Base de datos SQLite
├── requirements.txt     # Dependencias
├── run.py              # Script para ejecutar
└── README.md           # Este archivo
```

## 🚀 **Próximas Características**

- [ ] Sistema de chat en tiempo real
- [ ] Integración con LMS externos
- [ ] Generador automático de ejercicios
- [ ] Análisis de aprendizaje con IA
- [ ] Modo offline
- [ ] Aplicación móvil
- [ ] Dashboard para profesores
- [ ] Reportes avanzados
- [ ] Sistema de calificaciones
- [ ] Integración con calendarios

## 🤝 **Contribuir**

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 **Licencia**

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📞 **Contacto**

- **Desarrollador**: Tu Nombre
- **Email**: tu@email.com
- **Proyecto**: [https://github.com/tu-usuario/edumath](https://github.com/tu-usuario/edumath)

---

**¡Hecho con ❤️ y mucho ☕ para el aprendizaje de las matemáticas!** 🧮✨
