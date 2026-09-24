// API 02 service - GET /api/users
// Owner: Manatka
//
// HTTP only. Same conventions as services/auth/sessionService.js:
// shared API base, session cookie sent with credentials: 'include'.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export async function getUsers() {
  const response = await fetch(`${API_BASE_URL}/users`, {
    method: 'GET',
    credentials: 'include'
  });

  const data = await response.json();

  if (!response.ok) {
    const error = new Error(data.detail || 'Unable to load users.');
    error.status = response.status;
    throw error;
  }

  return data;
}