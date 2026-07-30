const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  base: API_BASE,
  wsBase: API_BASE.replace(/^http/, 'ws'),

  getExercises: () => request('/workout/exercises'),
  getWorkoutHistory: () => request('/workout/history'),

  analyzeWorkout: async (exercise, file) => {
    const formData = new FormData();
    formData.append('exercise', exercise);
    formData.append('video', file);
    const res = await fetch(`${API_BASE}/workout/analyze`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({}));
      throw new Error(detail.detail || `Request failed: ${res.status}`);
    }
    return res.json();
  },

  calculateDiet: (payload) =>
    request('/diet/calculate', { method: 'POST', body: JSON.stringify(payload) }),
  getDietHistory: () => request('/diet/history'),
  dietChat: (message, calorie_data) =>
    request('/diet/chat', {
      method: 'POST',
      body: JSON.stringify({ message, calorie_data }),
    }),

  getHabitStatus: () => request('/habit/status'),
};