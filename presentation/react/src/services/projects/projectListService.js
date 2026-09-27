// API 05 service - GET /api/projects
// Owner: Jesse

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export async function getProjects() {
  const response = await fetch(`${API_BASE_URL}/projects`, {
    method: 'GET',
    credentials: 'include'
  });

  const data = await response.json().catch(() => ([]));

  if (!response.ok) {
    const error = new Error(data.detail || 'Unable to load projects.');
    error.status = response.status;
    throw error;
  }

  return data;
}
