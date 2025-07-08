# 📋 MatEdu API - Guía Rápida para Frontend

## 🔗 URL Base
```
http://127.0.0.1:8000/api/v1
```

## 🔐 Autenticación

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "juan@estudiante.com",
  "password": "estudiante123"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Registro
```http
POST /auth/registro
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

## 👤 Headers Autenticados
```http
Authorization: Bearer YOUR_TOKEN_HERE
Content-Type: application/json
```

## 📚 Endpoints Principales

### Áreas Matemáticas
```http
GET /areas-matematicas
```

### Cursos
```http
GET /cursos                          # Todos los cursos
GET /cursos?area_id=1                # Cursos de un área
GET /cursos?nivel=basico             # Cursos por nivel
GET /cursos/{id}                     # Curso específico
POST /cursos/{id}/inscribirse        # Inscribirse (auth)
GET /usuarios/me/cursos              # Mis cursos (auth)
```

### Lecciones
```http
GET /cursos/{curso_id}/lecciones     # Lecciones de un curso
POST /lecciones/{id}/iniciar         # Iniciar lección (auth)
POST /lecciones/{id}/completar       # Completar lección (auth)
```

### Ejercicios
```http
GET /lecciones/{leccion_id}/ejercicios           # Ejercicios de lección
POST /ejercicios/{id}/responder                  # Responder ejercicio (auth)

Body para responder:
{
  "ejercicio_id": 1,
  "respuesta_usuario": "6x"
}
```

### Usuario y Progreso
```http
GET /usuarios/me                                 # Mi perfil (auth)
GET /usuarios/{id}/estadisticas                  # Estadísticas de usuario
GET /usuarios/me/progreso/{curso_id}             # Mi progreso en curso (auth)
```

## 🧪 Credenciales de Prueba

| Rol | Email | Password |
|-----|-------|----------|
| Admin | admin@edumath.com | admin123 |
| Profesor | maria@edumath.com | profesor123 |
| Estudiante | juan@estudiante.com | estudiante123 |
| Estudiante | ana@estudiante.com | estudiante123 |

## 📊 Tipos de Datos

### Usuario Types
- `estudiante`
- `profesor` 
- `admin`

### Niveles de Dificultad
- `basico`
- `intermedio`
- `avanzado`

### Tipos de Ejercicio
- `opcion_multiple`
- `desarrollo`
- `verdadero_falso`
- `completar`

### Estados de Progreso
- `no_iniciado`
- `en_progreso`
- `completado`

## 🎯 Flujo Típico de Usuario

1. **Login** → Obtener token
2. **Ver áreas** → GET /areas-matematicas
3. **Ver cursos** → GET /cursos?area_id=1
4. **Inscribirse** → POST /cursos/{id}/inscribirse
5. **Ver lecciones** → GET /cursos/{id}/lecciones
6. **Iniciar lección** → POST /lecciones/{id}/iniciar
7. **Ver ejercicios** → GET /lecciones/{id}/ejercicios
8. **Responder** → POST /ejercicios/{id}/responder
9. **Completar lección** → POST /lecciones/{id}/completar
10. **Ver progreso** → GET /usuarios/me/progreso/{curso_id}

## 🚀 Iniciar Backend

```bash
cd "C:\Users\kevin\Desktop\pfm back"
python run.py
```

API disponible en: http://127.0.0.1:8000
Documentación: http://127.0.0.1:8000/docs
