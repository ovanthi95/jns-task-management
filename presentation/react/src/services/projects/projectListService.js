const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export async function getProjects() {
  const response = await fetch(`${API_BASE_URL}/projects`, {
    method: 'GET',
    credentials: 'include'
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || 'Unable to load projects.');
  }

  return data.projects || data || [];
}
