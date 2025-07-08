// apiService.js - Servicio para conectar con tu backend MatEdu

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

// Clase para manejar la API
class MatEduAPI {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.token = localStorage.getItem('access_token');
  }

  // Método genérico para hacer requests
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Agregar token si está disponible
    if (this.token) {
      config.headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Error en la API');
      }

      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // ================================
  // AUTENTICACIÓN
  // ================================

  async login(email, password) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    if (response.access_token) {
      this.token = response.access_token;
      localStorage.setItem('access_token', this.token);
    }

    return response;
  }

  async register(userData) {
    return await this.request('/auth/registro', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  logout() {
    this.token = null;
    localStorage.removeItem('access_token');
  }

  // ================================
  // USUARIOS
  // ================================

  async getMyProfile() {
    return await this.request('/usuarios/me');
  }

  async getUserStats(userId) {
    return await this.request(`/usuarios/${userId}/estadisticas`);
  }

  // ================================
  // ÁREAS MATEMÁTICAS
  // ================================

  async getAreas() {
    return await this.request('/areas-matematicas');
  }

  // ================================
  // CURSOS
  // ================================

  async getCursos(filters = {}) {
    const params = new URLSearchParams(filters);
    return await this.request(`/cursos?${params}`);
  }

  async getCurso(id) {
    return await this.request(`/cursos/${id}`);
  }

  async enrollInCourse(courseId) {
    return await this.request(`/cursos/${courseId}/inscribirse`, {
      method: 'POST',
    });
  }

  async getMyCourses() {
    return await this.request('/usuarios/me/cursos');
  }

  // ================================
  // LECCIONES
  // ================================

  async getCourseLessons(courseId) {
    return await this.request(`/cursos/${courseId}/lecciones`);
  }

  async startLesson(lessonId) {
    return await this.request(`/lecciones/${lessonId}/iniciar`, {
      method: 'POST',
    });
  }

  async completeLesson(lessonId) {
    return await this.request(`/lecciones/${lessonId}/completar`, {
      method: 'POST',
    });
  }

  // ================================
  // EJERCICIOS
  // ================================

  async getLessonExercises(lessonId) {
    return await this.request(`/lecciones/${lessonId}/ejercicios`);
  }

  async submitAnswer(exerciseId, answer) {
    return await this.request(`/ejercicios/${exerciseId}/responder`, {
      method: 'POST',
      body: JSON.stringify({
        ejercicio_id: exerciseId,
        respuesta_usuario: answer,
      }),
    });
  }

  // ================================
  // PROGRESO
  // ================================

  async getCourseProgress(courseId) {
    return await this.request(`/usuarios/me/progreso/${courseId}`);
  }
}

// Exportar instancia única
export const api = new MatEduAPI();

// También exportar la clase por si necesitas múltiples instancias
export default MatEduAPI;

// ================================
// DATOS DE PRUEBA
// ================================

export const TEST_USERS = {
  admin: {
    email: "admin@edumath.com",
    password: "admin123"
  },
  profesor: {
    email: "maria@edumath.com", 
    password: "profesor123"
  },
  estudiante: {
    email: "juan@estudiante.com",
    password: "estudiante123"
  }
};

// ================================
// TIPOS/ENUMS (para TypeScript)
// ================================

export const USER_TYPES = {
  ESTUDIANTE: 'estudiante',
  PROFESOR: 'profesor',
  ADMIN: 'admin'
};

export const DIFFICULTY_LEVELS = {
  BASICO: 'basico',
  INTERMEDIO: 'intermedio',
  AVANZADO: 'avanzado'
};

export const EXERCISE_TYPES = {
  OPCION_MULTIPLE: 'opcion_multiple',
  DESARROLLO: 'desarrollo',
  VERDADERO_FALSO: 'verdadero_falso',
  COMPLETAR: 'completar'
};

export const PROGRESS_STATES = {
  NO_INICIADO: 'no_iniciado',
  EN_PROGRESO: 'en_progreso',
  COMPLETADO: 'completado'
};
