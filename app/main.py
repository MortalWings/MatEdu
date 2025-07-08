from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router
from app.database import engine
from app.models import Base

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Crear la aplicación FastAPI
app = FastAPI(
    title="Plataforma de Matemáticas - EduMath",
    description="API para plataforma educativa de matemáticas con cursos, ejercicios y seguimiento de progreso",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
origins = [
    "http://localhost:3000",  # React dev
    "http://localhost:5173",  # Vite dev
    "http://localhost:8080",  # Vue dev
    "https://*.vercel.app",   # Vercel deployments
    "https://*.netlify.app",  # Netlify deployments
    "*"  # Para desarrollo - en producción cambiar por dominios específicos
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir las rutas
app.include_router(router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {
        "message": "Bienvenido a EduMath - Plataforma de Matemáticas",
        "version": "1.0.0",
        "docs": "/docs",
        "features": [
            "Gestión de usuarios y autenticación",
            "Cursos de matemáticas por niveles",
            "Ejercicios interactivos",
            "Seguimiento de progreso",
            "Sistema de puntos y logros"
        ]
    }

@app.get("/health")
def health_check():
    return {"status": "OK", "message": "API funcionando correctamente"}

# Evento de inicio
@app.on_event("startup")
async def startup_event():
    print("🚀 EduMath API iniciada correctamente")
    print("📚 Base de datos configurada")
    print("🔐 Sistema de autenticación activo")
    print("📊 Documentación disponible en /docs")
