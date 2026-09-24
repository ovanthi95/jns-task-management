// API 03 service - POST /api/users
// Owner: Manatka
//
// HTTP only. On 400 the backend returns { field: [message] } (DRF validation
// and the service's duplicate-email / unknown-role errors share that shape),
// which is passed through on error.fields for the form to display.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export async function createUser(payload) {
  const response = await fetch(`${API_BASE_URL}/users`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  const data = await response.json();

  if (!response.ok) {
    const error = new Error(data.detail || 'Unable to create user.');
    error.status = response.status;
    error.fields = response.status === 400 && !data.detail ? data : {};
    throw error;
  }

  return data;
}