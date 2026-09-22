// API 01 service - POST /api/auth/login
// Owner: Ovanthi


const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';


export async function logout() {
  const response = await fetch(`${API_BASE_URL}/auth/logout`, {
    method: 'POST',
    credentials: 'include'
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || 'Unable to log out.');
  }

  return data;
}