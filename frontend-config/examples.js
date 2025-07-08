// Ejemplos de uso del API Service en diferentes frameworks

// ================================
// REACT EXAMPLES
// ================================

// Login Component (React)
import { useState } from 'react';
import { api } from './apiService';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await api.login(email, password);
      console.log('Login exitoso:', response);
      // Redirigir al dashboard
    } catch (error) {
      console.error('Error de login:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <input 
        value={email} 
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        type="email"
      />
      <input 
        value={password} 
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password" 
        type="password"
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Cargando...' : 'Iniciar Sesión'}
      </button>
    </form>
  );
}

// Courses Component (React)
import { useEffect, useState } from 'react';
import { api } from './apiService';

function Courses() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCourses();
  }, []);

  const loadCourses = async () => {
    try {
      const data = await api.getCursos();
      setCourses(data);
    } catch (error) {
      console.error('Error loading courses:', error);
    } finally {
      setLoading(false);
    }
  };

  const enrollInCourse = async (courseId) => {
    try {
      await api.enrollInCourse(courseId);
      alert('¡Inscripción exitosa!');
      loadCourses(); // Recargar cursos
    } catch (error) {
      alert('Error en la inscripción: ' + error.message);
    }
  };

  if (loading) return <div>Cargando cursos...</div>;

  return (
    <div>
      <h2>Cursos Disponibles</h2>
      {courses.map(course => (
        <div key={course.id} style={{ border: '1px solid #ccc', margin: '10px', padding: '10px' }}>
          <h3>{course.titulo}</h3>
          <p>{course.descripcion}</p>
          <p>Nivel: {course.nivel_dificultad}</p>
          <p>Duración: {course.duracion_estimada} horas</p>
          <button onClick={() => enrollInCourse(course.id)}>
            Inscribirse
          </button>
        </div>
      ))}
    </div>
  );
}

// ================================
// VUE 3 EXAMPLES
// ================================

// Login Component (Vue 3 Composition API)
/*
<template>
  <form @submit.prevent="handleLogin">
    <input 
      v-model="email" 
      placeholder="Email" 
      type="email"
      required
    />
    <input 
      v-model="password" 
      placeholder="Password" 
      type="password"
      required
    />
    <button type="submit" :disabled="loading">
      {{ loading ? 'Cargando...' : 'Iniciar Sesión' }}
    </button>
  </form>
</template>

<script setup>
import { ref } from 'vue';
import { api } from './apiService';

const email = ref('');
const password = ref('');
const loading = ref(false);

const handleLogin = async () => {
  loading.value = true;
  
  try {
    const response = await api.login(email.value, password.value);
    console.log('Login exitoso:', response);
    // Redirigir al dashboard
  } catch (error) {
    console.error('Error de login:', error);
  } finally {
    loading.value = false;
  }
};
</script>
*/

// ================================
// VANILLA JAVASCRIPT EXAMPLES
// ================================

// Login con JavaScript puro
async function loginUser() {
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  
  try {
    const response = await api.login(email, password);
    console.log('Login exitoso:', response);
    
    // Guardar info del usuario
    localStorage.setItem('user', JSON.stringify(response));
    
    // Redirigir
    window.location.href = '/dashboard.html';
  } catch (error) {
    alert('Error: ' + error.message);
  }
}

// Cargar cursos con JavaScript puro
async function loadCourses() {
  try {
    const courses = await api.getCursos();
    const container = document.getElementById('courses-container');
    
    container.innerHTML = courses.map(course => `
      <div class="course-card">
        <h3>${course.titulo}</h3>
        <p>${course.descripcion}</p>
        <p>Nivel: ${course.nivel_dificultad}</p>
        <button onclick="enrollInCourse(${course.id})">
          Inscribirse
        </button>
      </div>
    `).join('');
  } catch (error) {
    console.error('Error loading courses:', error);
  }
}

// ================================
// EJERCICIOS - EXAMPLES
// ================================

// Responder ejercicio
async function submitExerciseAnswer(exerciseId, userAnswer) {
  try {
    const response = await api.submitAnswer(exerciseId, userAnswer);
    
    if (response.es_correcta) {
      alert(`¡Correcto! Ganaste ${response.puntos_obtenidos} puntos`);
    } else {
      alert('Respuesta incorrecta. Inténtalo de nuevo.');
    }
    
    return response;
  } catch (error) {
    alert('Error al enviar respuesta: ' + error.message);
  }
}

// ================================
// PROGRESO - EXAMPLES
// ================================

// Obtener progreso del usuario
async function getUserProgress(courseId) {
  try {
    const progress = await api.getCourseProgress(courseId);
    
    console.log(`Progreso: ${progress.progreso_porcentaje}%`);
    console.log(`Lecciones completadas: ${progress.lecciones_completadas}/${progress.lecciones_totales}`);
    
    return progress;
  } catch (error) {
    console.error('Error loading progress:', error);
  }
}

export { 
  Login, 
  Courses, 
  loginUser, 
  loadCourses, 
  submitExerciseAnswer, 
  getUserProgress 
};
