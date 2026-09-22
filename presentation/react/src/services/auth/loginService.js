// API 01 service - POST /api/auth/login
// Owner: Ovanthi

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';


export async function login(email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    credentials: 'include',

    headers: {
      'Content-Type': 'application/json'
    },

    body: JSON.stringify({
      email,
      password
    })
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || 'Unable to sign in.'
    );
  }

  return data;
}